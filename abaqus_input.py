import numpy
import os
import logging

#####################################################################################################################


def create_boundary_condition(nset_dict, dataset, bc1, bc2=0):
    """ Function to create a dictionary consisting of all node number and abaqus boundary conditions. An entry of the
        the dictionary looks, due to bc1 = 8, for example like this: (node-234-PP, 8, 8, 123456).
        If the second boundary condition is not set, the bc1 will be used twice, according to Abaqus manual.

     Parameters:
        nset_dict: dictionary containing node_no:node_set_names
        dataset (ndarray): array consisting of two columns: 1. nodes, 2. boundary condition values
        bc1: first boundary condition number, according to Abaqus manual
        bc2: second boundary condition number, according to Abaqus manual (optional)

    Returns:
        bc_dict
    """

    function_name = 'create_boundary_condition'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    if bc2 == 0:
        bc2 = bc1

    bc_dict = {}

    try:
        # Every node gets its own boundary condition as shown below:
        # node-1-PP, 8, 8, 123456
        with numpy.nditer(dataset, op_flags=['readonly']) as it:
            for data in it:

                node = int(data[0])
                value = data[1]

                bc_string = nset_dict[node] + ', ' + str(bc1) + ', ' + str(bc2) + ', ' + str(value)
                bc_dict[int(node)] = bc_string

        return bc_dict

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def create_nodesets_all_list(nset_dict, part_name):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations. An entry of the
        the dictionary looks, due to part_name = 'Part-1', for example like this:
        (234: *Nset, nset = node-234-PP, internal, instance = Part-1 \n 234).

     Parameters:
        nset_dict: dictionary containing node_no:node_set_names
        part_name: name of the part containing the nodes

    Returns:
        dictionary{node_no: nset_name}
    """

    function_name = 'create_nodesets_all_list'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    nset_list = {}

    try:
        # Every node gets its own node set as shown below:
        # *Nset, nset = node-234-PP, internal, instance = Part-1
        # 234

        for node, name in nset_dict.items():
            nset_string = '*Nset, nset=' + name + ', instance=' + part_name + '\n' + str(node) + ','
            nset_list[int(node)] = nset_string

        return nset_list

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def create_nodesets_all(nodes, bc_name):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations. An entry of the
        the dictionary looks, due to bc_name = 'PP', for example like this: (234: node-234-PP).

     Parameters:
        nodes (ndarray): array consisting of just one column: nodes numbers
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """

    function_name = 'create_nodesets_all'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    nodes = nodes.astype(int)

    nset_string = ''
    nset_dict = {}

    try:
        # Every node gets its own node set as shown below:
        # _Node392_PP_
        with numpy.nditer(nodes, op_flags=['readonly']) as it:
            for node in it:
                nset_name = 'node-' + str(node) + '-' + bc_name
                nset_dict[int(node)] = nset_name

        return nset_dict

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def write_inputfile(dict_bc, nset_list, input_file_name, job_name, output_path):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nodes (ndarray): array consisting of one column: 1. nodes
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """
    # FIXME Function description
    function_name = 'write_inputfile'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        input_file_name = input_file_name.replace("\\", "/")
        output_path = output_path.replace("\\", "/")
        output_file = output_path + '/' + job_name + '.inp'

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        input_file = open(input_file_name, 'r')
        file = open(output_file, 'w')

        for line in input_file:

            if '** Nset_python_fill_in_placeholder' in line:
                file.write('**Node sets for every single node created by Python' + '\n')
                for nset in nset_list.values():
                    file.write(nset  + '\n')

            elif '** bc_python_fill_in_placeholder' in line:
                file.write('**Boundary conditions created by Python' + '\n')
                file.write('*Boundary' + '\n')
                for bc in dict_bc.values():
                    file.write(bc + '\n')

            else:
                file.write(line)

        input_file.close()
        file.close()

        return output_file

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def write_bashfile_windows(output_path, param_input, param_job, param_user, param_scratch='', param_oldjob='',
                           param_additional=''):
    """ Function to create windows bash file to execute Abaqus simulation in console.

     Parameters:
        output_path (String): Path where to save the bash file
        param_input (String): Input filename including path
        param_job (String): Name of the job to be used as filename
        param_user (String): User subroutine filename including path
        param_scratch (String): Path of the scratch directory (optional)
        param_oldjob (String): name of the old job (optional)
        param_additional (String): Aditional parameters to be used for the execution of the simulation

    Returns:
        bash_file_name (String)
    """

    function_name = 'write_inputfile'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        output_path = output_path.replace("\\", "/")

        bash_file_name = output_path + '/' + param_job + '.bat'

        # Create bash file and open in write mode
        bash_file = open(bash_file_name, 'w')

        # Replace backslashes by slashes
        param_input = param_input.replace("/", "\\")
        param_user = param_user.replace("/", "\\")
        param_scratch = param_scratch.replace("/", "\\")

        param_additional = ' interactive ' + param_additional

        # Create the command line for the bash file according to given function input parameters.
        cmd_string = 'call abaqus job=' + param_job + ' input=' + param_input

        # Check if oldjob parameter is given and add parameter to command line
        if param_oldjob != '':
            cmd_string = cmd_string + ' oldjob=' + param_oldjob

        # Add user subroutine to command line
        cmd_string = cmd_string + ' user=' + param_user

        # Check if scratch parameter is given and add parameter to command line
        if param_scratch != '':
            cmd_string = cmd_string + ' scratch=' + param_scratch

        # Add additional parameters to command line
        cmd_string = cmd_string + param_additional

        # Write and close bash file
        bash_file.write(cmd_string)
        bash_file.close()

        # Return bash file name
        return bash_file_name

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################


def log(msg, log_file):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nodes (ndarray): array consisting of one column: 1. nodes
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """
    # FIXME Function description
    print(msg)
    log_file.write(msg + '\n')
    return 0


#####################################################################################################################
#####################################################################################################################


def write_inputfile_restart(dict_bc, prev_input_file_path, step_name, job_name, output_path, restart_step, resume = True):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nodes (ndarray): array consisting of one column: 1. nodes
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """
    # FIXME Function description
    function_name = 'write_inputfile_restart'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    try:
        # Replace backslashes by slashes
        prev_input_file_path = prev_input_file_path.replace("\\", "/")
        output_path = output_path.replace("\\", "/")
        output_file = output_path + '/' + job_name + '.inp'

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        prev_input_file = open(prev_input_file_path, 'r')
        restart_file = open(output_file, 'w')

        copy_input_file = 0

        # Write restart headline
        restart_file.write('** Description:' + '\n')
        restart_file.write('** Restart for input file: ' + prev_input_file_path + '\n')
        restart_file.write('** ----------------------------------------------------------------' + '\n')
        restart_file.write('*Heading' + '\n')
        restart_file.write('*Restart, read, step=' + str(restart_step) + '\n')

        # If the simulation shall not be resumed, all steps (but Geostatic-Step) will be copied into the new input file
        if not resume:
            for line in prev_input_file:
                if '** restart_point_python_placeholder' in line:
                    copy_input_file = 1

                if copy_input_file:
                    restart_file.write(line)

        # Write new step
        restart_file.write('**' + '\n')
        restart_file.write('** STEP:' + step_name + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('*Step, name=' + step_name + ', nlgeom=NO, amplitude=RAMP, inc=10000' + '\n')
        restart_file.write('*Soils, consolidation, end=PERIOD, utol=50000., creep=none' + '\n')
        restart_file.write('6000., 43200., 1e-05, 6000.,' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('** BOUNDARY CONDITIONS' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('** Name: BC_PP Type: Pore pressure' + '\n')

        restart_file.write('**Boundary conditions created by Python' + '\n')
        restart_file.write('*Boundary' + '\n')
        for bc in dict_bc.values():
            restart_file.write(bc + '\n')

        restart_file.write('**' + '\n')
        restart_file.write('** OUTPUT REQUESTS' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('** *Restart, write, frequency = 1' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('** FIELD OUTPUT: F - Output - 1' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('*Output, field' + '\n')
        restart_file.write('*Node Output' + '\n')
        restart_file.write('CF, COORD, POR, RF, U' + '\n')
        restart_file.write('*Element Output, directions = YES' + '\n')
        restart_file.write('FLUVR, LE, S, SAT, VOIDR, NFORC' + '\n')
        restart_file.write('*Contact Output' + '\n')
        restart_file.write('CDISP, CSTRESS, PFL' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('** HISTORY OUTPUT: H - Output - 1' + '\n')
        restart_file.write('**' + '\n')
        restart_file.write('*Output, history, variable = PRESELECT' + '\n')
        restart_file.write('*EL FILE, frequency=10000' + '\n')
        restart_file.write('COORD, VOIDR, POR' + '\n')
        restart_file.write('*NODE FILE' + '\n')
        restart_file.write('COORD' + '\n')
        restart_file.write('*End Step' + '\n')

        # Close files
        prev_input_file.close()
        restart_file.close()

        return output_file

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')


#####################################################################################################################
#####################################################################################################################

def read_part_nodes (input_file_path, part_name):
    """ Function to create an array consisting of all node number and the corresponding coordinates. Full path of the
        input file must be passed. The name of the part one want to extract the node-coordinates must be passed as
        well. The part name is not case sensitive!

     Parameters:
        input_file_path (String): Full path of input file
        part_name (String): Name of the part

    Returns:
        ndarray: Containing nodes and corresponding coordinates for each node in part_name

    """

    function_name = 'read_part_nodes'
    log = logging.getLogger('abaqus_input.py.' + function_name)
    log.debug('Start function')

    try:
        # Check if file exists
        if not os.path.isfile(input_file_path):
            raise FileNotFoundError

        # Open input file
        input_file = open(input_file_path, 'r')

        # Coordinates of nodes can be stored in part or in assembly therefore two search strings (case insensitive) have
        # have to be created.
        part_string = '*Part, name=' + part_name
        part_string = part_string.lower()
        assembly_string = '*Instance, name=' + part_name
        assembly_string = assembly_string.lower()

        # Variable set to True when node information have been found.
        read_coordinates = False

        # Initialize empty arrays for nodes and coordinates. These will be assembled after filling with data.
        node_array = []
        x_array = []
        y_array = []
        z_array = []

        # Check each line of input file
        for line in input_file:
            line_string = line.strip().lower()

            # If read_coordinates is True and *Element was found in the actual line, the listing of coordinates ended.
            if '*Element,' in line:
                if read_coordinates:
                    log.debug('Found end of part/assembly.')
                    break

            # True if the coordinates are stored in a part.
            if part_string == line_string:
                log.info('Found nodes in parts at: %s. Start reading coordinates of nodes for this part.',
                         part_string)
                read_coordinates = True

            # True if the coordinates are stored in the assembly.
            if assembly_string == line_string:
                log.info('Found nodes in assembly at: %s. Start reading coordinates of nodes for this part.',
                         part_string)
                read_coordinates = True

            # If beginning of coordination listing is found, the coordinates are going to be extracted from each line
            # and appended into an earlier initialized array. It must be checked if the line contains x/y/z or only
            # x/y coordinates.
            if read_coordinates:
                try:
                    line_array = numpy.fromstring(line, dtype=float, sep=',')
                    if line_array.__len__() == 3:
                        node = line_array[0]
                        x = line_array[1]
                        y = line_array[2]

                        log.debug('node: %s;\t x: %s;\t y: %s', node, x, y)

                        node_array.append(int(node))
                        x_array.append(float(x))
                        y_array.append(float(y))

                    if line_array.__len__() == 4:
                        node = line_array[0]
                        x = line_array[1]
                        y = line_array[2]
                        z = line_array[3]

                        log.debug('node: %s;\t x: %s;\t y: %s\t z: %s', node, x, y, z)

                        node_array.append(int(node))
                        x_array.append(float(x))
                        y_array.append(float(y))
                        z_array.append(float(z))

                except Exception as err:
                    log.error('An error occured while reading coordinates for nodes. Error: %s', str(err))

        # Close input file
        input_file.close()

        # Return ndarray containing a set of nodes and the corresponding coordinates.
        if z_array.__len__() == 0:
            log.info('Added %s nodes with x/y-coordinates', node_array.__len__())
            return numpy.array([node_array, x_array, y_array])
        else:
            log.info('Added %s nodes with x/y/z-coordinates', node_array.__len__())
            return numpy.array([node_array, x_array, y_array, z_array])

    except Exception as err:
        log.error(str(err))
        return -1

    finally:
        log.debug('Exit function')

#####################################################################################################################