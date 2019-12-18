import csv
import numpy
import sys
import os
import logging

from scipy.interpolate import griddata  # used for mesh transformation
import matplotlib.pyplot as plt  # used for visualisation of transformation validation

#####################################################################################################################


def read_pace3d(file_name, path=''):
    """ Function to read an dat-file-export from the Software Pace3D from IDM HS Karlsruhe

     Parameters:
        file_name (str): filename including filetype (e.g. data.dat)
        path (str), optional: path to the file

    Returns:
        ndarray
    """
    function_name = 'read_pace3d'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        path = path.replace("\\", "/")

        # Check wheter there is a path or only a filename handed over
        if path != '':
            file_path = path + '/' + file_name
        else:
            file_path = file_name

        # Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError

        log.info('Load Pace3D-File: %s', file_path)

        with open(file_path) as csvfile:
            read_csv = csv.reader(csvfile, delimiter=' ')

            x = []
            y = []
            z = []
            data_set = []

            for row in read_csv:
                try:
                    x.append(float(row[0]))
                    y.append(float(row[1]))
                    z.append(float(row[2]))
                    data_set.append(float(row[3]))

                except Exception as err:
                    log.info('Empty row found and ignored. Continue... [%s]', str(err))

            log.info('%s rows read successfully', len(data_set))

            return numpy.array([x, y, z, data_set])

    except Exception as err:
        log.error('File --%s-- could not be read correctly [%s]', file_name, str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################


def read_abaqus(file_name, path=''):
    """ Function to read an csv-file-export from the Software Simulia Abaqus

     Parameters:
        file_name (str): filename including filetype (e.g. data.dat)
        path (str), optional: path to the file

    Returns:
        ndarray
    """

    function_name = 'read_abaqus'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        path = path.replace("\\", "/")

        # Check wheter there is a path or only a filename handed over
        if path != '':
            file_path = path + '/' + file_name
        else:
            file_path = file_name

        #Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError

        log.info('Load Abaqus-Mesh-File: %s', file_path)

        with open(file_path) as csvfile:
            read_csv = csv.reader(csvfile, delimiter=',')

            x = []
            y = []
            z = []
            data_set = []

            for row in read_csv:
                try:
                    if len(row) == 4:
                        x.append(float(row[0]))
                        y.append(float(row[1]))
                        z.append(float(row[2]))
                        data_set.append(float(row[3]))

                    if len(row) != 4:
                        log.info('Empty row found or transition failed. Continue...')

                except Exception as err:
                    log.warning('Empty row found or transition failed. Continue... [%s]', str(err))

            log.debug('%d rows read successfully', len(x))

            return numpy.array([x, y, z, data_set])

    except Exception as err:
        log.error('File --%s-- could not be read correctly [%s]', file_name, str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def write_abaqus(data, file_name, path=''):
    """ Function to write an csv-file-input from a given ndarray for the Software Simulia Abaqus

     Parameters:
        data (ndarray): dataset
        file_name (str): filename including filetype (e.g. data.dat)
        path (str), optional: path to the file

    Returns:
        boolean
    """

    function_name = 'write_abaqus'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        path.replace("\\", "/")

        # Check whether there is a path or only a filename handed over
        if path != '':
            file_path = path + '/' + file_name
        else:
            file_path = file_name

        log.info('Write Abaqus-data-file: %s', file_path)

        # Writing data to csv-file
        numpy.savetxt(file_path, data, delimiter=',', fmt='%11.8s')

        return 0

    except Exception as err:
        log.error('Writing data in  --%s-- not successful. [%s]', file_name, str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def write_pace3D(data, file_name, path=''):
    """ Function to write an csv-file-input from a given ndarray for the Software Pace3D

     Parameters:
        data (ndarray): dataset
        file_name (str): filename including filetype (e.g. data.dat)
        path (str), optional: path to the file

    Returns:
        boolean
    """

    function_name = 'write_pace3D'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        path.replace("\\", "/")

        # Check wheter there is a path or only a filename handed over
        if path != '':
            file_path = path + '/' + file_name
        else:
            file_path = file_name

        log.info('Write pace3D-data-file: %s', file_path)

        # Writing data to csv-file
        numpy.savetxt(file_path, data, delimiter=' ', fmt='%i %i %f')

        return 0

    except Exception as err:
        log.error('Writing data in  --%s-- not successful. [%s]', file_name, str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def transformation_validation(input_mesh, output_mesh, input_data):
    """ Validating the method of transferring data from one mesh to another We have two different meshes (one is
    coarser then the other). The information within the mesh is transferred from one mesh to the other and backwards.
    The transformation form a finer to a coarser mesh includes data loss. The amount of loss is influenced by the
    difference of the mesh resolution. The following code transforms the data from mesh 'input' (maybe finer) to mesh
    'output' (maybe coarser) back to mesh 'input_re'. The data loss will be shown by checking the difference 'input -
    input_re'. As a result we get a min/max-value, mean and standard deviation to check whether the data loss is
    acceptable.

    Parameters:
        input_mesh (ndarray): input mesh as type(narray); contains 2d(x,y) or 3d(x,y,z) coordinates; size corresponding
            to the input data parameter
        output_mesh (ndarray): output mesh as type(narray); contains 2d(x,y) or 3d(x,y,z) coordinates
        input_data (ndarray): input data as type(narray) containing the data that shall be transformed to the
            output mesh

    Returns:
        None
    """

    function_name = 'transformation_validation'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')
    log.info('Transforming validation will be started')

    try:
        # Data transformation from input_mesh to output_mesh
        output = mesh_transformation(input_mesh, output_mesh, input_data)

        output_data = []
        if numpy.size(output, 0) == 3:
            output_data = output[2]
        elif numpy.size(output, 0) == 4:
            output_data = output[3]

        # Data transformation from output_mesh back to input_mesh
        input_re = mesh_transformation(output_mesh, input_mesh, output_data)

        input_re_data = []
        if numpy.size(input_re, 0) == 3:
            input_re_data = input_re[2]
        elif numpy.size(input_re, 0) == 4:
            input_re_data = input_re[3]

        log.debug('Array output: input after retransformation')
        # print(print_pre_str, input_re_data) #Loggable?

        # Calculating mean and standard deviation
        # For statistics the absolute values of fine_new_data are used
        diff = numpy.absolute(input_data - input_re_data)

        log.debug('Statistics:')
        log.debug('Nodes fine: %d', input_mesh[0].size)
        log.debug('Coarse fine: %d', output_mesh[0].size)
        log.debug('After transformation:')
        log.debug('NaN-Values: %d', sum(numpy.isnan(input_re_data)))
        log.debug('Mean: %f', numpy.nanmean(diff))
        log.debug('Std. Deviation: %f', numpy.nanstd(diff))

        # Generating the visual output
        log.info('Plotting datasets to visually comparison')
        mpl_fig = plt.figure()
        ax1 = mpl_fig.add_subplot(221)
        cb1 = ax1.scatter(input_mesh[0], input_mesh[1], s=1, c=input_data, cmap=plt.cm.get_cmap('RdBu'))
        plt.colorbar(cb1, ax=ax1)
        ax1.set_title('input (original)')

        ax2 = mpl_fig.add_subplot(222)
        cb2 = ax2.scatter(output_mesh[0], output_mesh[1], s=1, c=output_data, cmap=plt.cm.get_cmap('RdBu'))
        plt.colorbar(cb2, ax=ax2)
        ax2.set_title('output')

        ax3 = mpl_fig.add_subplot(223)
        cb3 = ax3.scatter(input_mesh[0], input_mesh[1], s=1, c=input_re_data, cmap=plt.cm.get_cmap('RdBu'))
        plt.colorbar(cb3, ax=ax3)
        ax3.set_title('input (retransformation)')

        # function to show the plot
        plt.show()

        return 0

    except Exception as err:
        log.critical('Execution aborted! [%s]', str(err))
        sys.exit(print_pre_str + 'ERROR: ' + str(err) + '\nExecution aborted!')

    finally:
        log.debug('Exit function')


#####################################################################################################################


def mesh_transformation(input_mesh, output_mesh, input_data):
    """
    Data transformation from input_mesh to output_mesh using input_data. For the transformation the
    scipy.interpolate.griddata method will be used with two different options. First a linear interpolation.
    Potentially upcomming NaN-values within the linear interpolation will be filled with data from a nearest-neighbor
    interpolation. Output is an array containing output_mesh and output_data.

    Parameters:
        input_mesh (ndarray): input mesh as type(narray); contains 2d(x,y) or 3d(x,y,z) coordinates; size corresponding
            to the input data parameter
        output_mesh (ndarray): output mesh as type(narray); contains 2d(x,y) or 3d(x,y,z) coordinates
        input_data (ndarray): input data as type(narray) containing the data that shall be transformed to the
            output mesh

    Returns:
        output_mesh (ndarray):output_mesh including transformed data
    """

    function_name = 'mesh_transformation'
    log = logging.getLogger('mesh_transition.py.' + function_name)
    log.debug('Start function')
    log.info('Transforming information from input mesh to output mesh')

    try:
        # Check size of input_mesh
        if numpy.size(input_mesh, 0) == 2:
            log.info('Input is a 2D-mesh')
            dimensions = 2
            input_mesh_list = (input_mesh[0], input_mesh[1])

        elif numpy.size(input_mesh, 0) == 3:
            log.info('Input is a 3D-mesh')
            dimensions = 3
            input_mesh_list = (input_mesh[0], input_mesh[1], input_mesh[2])

        else:
            raise Exception('Size of input_mesh_array does not fit (x,y,z). z is optional')

        # Check size of input_mesh
        if numpy.size(output_mesh, 0) == 2 and dimensions == 2:
            log.info('Output is a 2D-mesh')
            output_mesh_list = (output_mesh[0], output_mesh[1])

        elif numpy.size(output_mesh, 0) == 3 and dimensions == 3:
            log.info('Output is a 3D-mesh')
            output_mesh_list = (output_mesh[0], output_mesh[1], output_mesh[2])

        else:
            raise Exception('Size of output_mesh_array (' + str(numpy.size(output_mesh, 0)) +
                            ')does not fit (x,y,z); z is optional. Both meshes (input and output) ' +
                            'need to have the same size 2D or 3D.')

        # Check if size of input_mesh and input_data are equal
        if numpy.size(input_data) != numpy.size(input_mesh, 1):
            raise Exception('Size of data_array (data: ' + str(numpy.size(input_data)) + ' mesh: '
                            + str(numpy.size(input_mesh, 1))
                            + ') does not fit. It should contain just one row and the same length as input_mesh.')

        # Choose whether a 2d or 3d interpolation has to be done In the first place a linear interpolation will be
        # done. By a transformation from coarse to fine, we are having problems with regions, that are not able to be
        # filled with a linear interpolation (getting NaN). For example, when the fine mesh has outer boundaries/lines
        # which are not "surrounded" by coarse-mesh. Those points need a nearest neighbor transformation.
        # 1. linear interpolation
        # 2. nearest neighbor
        # 3. fill all NaN-gabs in 1. with 2.
        log.debug('Calculation interpolation in 2D')

        linear = griddata(input_mesh_list, input_data, output_mesh_list, 'linear')
        nearest = griddata(input_mesh_list, input_data, output_mesh_list, 'nearest')

        # Search NaN in linear and replace by nearest
        for x in range(len(linear)):
            if numpy.isnan(linear[x]):
                linear[x] = nearest[x]
            # print(print_pre_str, str(linear[x]), ' is nearest neighbor instead of NaN')

        # Create return: array including mesh and data
        output_data = linear
        output_array = numpy.append(output_mesh, [output_data], axis=0)

        # Print some statistics
        log.debug('Statistics:')
        log.debug('Intput Nodes: %d', input_mesh[0].size)
        log.debug('Output Nodes: %d', input_mesh[0].size)
        log.debug('NaN-Values: %d', sum(numpy.isnan(output_data)))

        return output_array

    except Exception as err:
        log.critical('Execution aborted! [%s]', str(err))
        sys.exit(print_pre_str + 'ERROR: ' + str(err) + '\nExecution aborted!')

    finally:
        log.debug('Exit function')


#####################################################################################################################


