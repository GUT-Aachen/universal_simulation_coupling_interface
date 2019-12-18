import numpy
import os
import logging

from scipy.interpolate import griddata  # used for mesh transformation
import matplotlib.pyplot as plt  # used for visualisation of transformation validation

#####################################################################################################################


def create_boundary_condition(nset_dict, dataset, bc1, bc2=0):
    """ Function to create a dictionary consisting of all node number and abaqus boundary conditions.

     Parameters:
        nset_dict: dictionary containing node_no:node_set_names
        dataset (ndarray): array consisting of two columns: 1. nodes, 2. boundary conditions
        bc1: frist boundary condition number
        bc2: second boundary condition number (optional)

    Returns:
        bc_dict
    """

    function_name = 'create_boundary_condition'
    log = logging.getLogger(__main__ + '.' + function_name)  # Define a logger
    # print_pre_str = '\t' + function_name + ' >> '
    log.debug('Start function')
    # print('* Start function: ', function_name)
    if bc2 == 0:
        bc2 = bc1

    bc_dict = {}

    try:
        # Every node gets its own boundary condition as shown below:
        # _Node392_PP_, 8, 8, 123456
        with numpy.nditer(dataset, op_flags=['readonly']) as it:
            for data in it:

                node = int(data[0])
                value = data[1]

                bc_string = nset_dict[node] + ', ' + str(bc1) + ', ' + str(bc2) + ', ' + str(value)
                bc_dict[int(node)] = bc_string

        return bc_dict

    except Exception as err:
        log.error(str(err))
        # print('* ERROR in function: ', function_name, ' [', str(err), ']')
        # print()
        return -1

    finally:
        log.debug('Exit function')
        # print(print_pre_str, 'exiting function')
        # print()


#####################################################################################################################
#####################################################################################################################

def create_nodesets_all_list(nset_dict, part_name):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nset_dict: dictionary containing node_no:node_set_names
        part_name: name of the part containing the nodes

    Returns:
        dictionary{node_no: nset_name}
    """

    function_name = 'create_nodesets_all_list'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)

    nset_list = {}

    try:
        # Every node gets its own node set as shown below:
        # *Nset, nset = _Node392_PP_, internal, instance = Part_1 - 1
        # 392

        for node, name in nset_dict.items():
            nset_string = '*Nset, nset=' + name + ', instance=' + part_name + '\n' + str(node) + ','
            nset_list[int(node)] = nset_string

        return nset_list

    except Exception as err:
        print('* ERROR in function: ', function_name, ' [', str(err), ']')
        print()
        return -1

    finally:
        print(print_pre_str, 'exiting function')
        print()


#####################################################################################################################
#####################################################################################################################

def create_nodesets_all(nodes, bc_name):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nodes (ndarray): array consisting of one column: 1. nodes
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """

    function_name = 'create_nodesets_all'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)

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
        print('* ERROR in function: ', function_name, ' [', str(err), ']')
        print()
        return -1

    finally:
        print(print_pre_str, 'exiting function')
        print()


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

    function_name = 'write_inputfile'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)

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

            if ('** Nset_python_fill_in_placeholder' in line):
                file.write('**Node sets for every single node created by Python' + '\n')
                for nset in nset_list.values():
                    file.write(nset  + '\n')

            elif ('** bc_python_fill_in_placeholder' in line):
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
        print('* ERROR in function: ', function_name, ' [', str(err), ']')
        print()
        return -1

    finally:
        print(print_pre_str, 'exiting function')
        print()


#####################################################################################################################
#####################################################################################################################

def write_bashfile_windows(output_path, param_input, param_job, param_user, param_oldjob = ''):
    """ Function to create a dictionary consisting of all node number and abaqus node set combinations.

     Parameters:
        nodes (ndarray): array consisting of one column: 1. nodes
        bc_name: name of the boundary condition

    Returns:
        dictionary{node_no: nset_name}
    """

    function_name = 'write_inputfile'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)

    try:
        # Replace backslashes by slashes
        output_path = output_path.replace("\\", "/")

        bash_file_name = output_path + '/' + param_job + '.bat'
        bash_file = open(bash_file_name, 'w')

        # Replace backslashes by slashes
        param_input = param_input.replace("/", "\\")
        param_user = param_user.replace("/", "\\")

        # Distinguishing between restart analysis and normal analysis. Restart needs 'oldjob-parameter'
        if param_oldjob != '':
            cmd_string = 'abaqus job=' + param_job + ' input=' + param_input + ' oldjob=' + param_oldjob + ' user=' + param_user + ' interactive '
            bash_file.write(cmd_string)
        else:
            cmd_string = 'abaqus job=' + param_job + ' input=' + param_input + ' user=' + param_user + ' interactive '
            bash_file.write(cmd_string)

        bash_file.close()

        return bash_file_name

    except Exception as err:
        print('* ERROR in function: ', function_name, ' [', str(err), ']')
        print()
        return -1

    finally:
        print(print_pre_str, 'exiting function')
        print()


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

    function_name = 'write_inputfile_restart'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)

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
        print('* ERROR in function: ', function_name, ' [', str(err), ']')
        print()
        return -1

    finally:
        print(print_pre_str, 'exiting function')
        print()

#####################################################################################################################


