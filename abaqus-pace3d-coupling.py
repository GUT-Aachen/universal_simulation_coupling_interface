from utils.engines_handler import EnginesHandler
import logging
import sys
from pathlib import Path

root_directory = Path('C:/Users/Sven F. Biebricher/Desktop/Abaqus-Pace3D-Transition.old')

# #################################################################################
# Initialize the logger: logging class
# Logfile name will be saved in 'abaqus_work_path'
log_file_name = root_directory / 'logfile.log'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=log_file_name,
                    filemode='w')

# Define a handler writing INFO messages or higher to sys.stderr
consoleLogger = logging.StreamHandler(sys.stdout)
consoleLogger.setLevel(logging.DEBUG)
# Set a format which is simpler for console use
format_logger = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
consoleLogger.setFormatter(format_logger)
logging.getLogger('').addHandler(consoleLogger)  # Add handler to root logger
log = logging.getLogger('sample' + '.main')  # Define a logger for __main__ file
# #################################################################################

# Set Abaqus job name
abaqus_job_name = 'CoupledSim_80'

# Set engines
abaqus = EnginesHandler('abaqus')
pace3d = EnginesHandler('pace3d')

work_directory = root_directory

# Name of Abaqus subroutine-file (f95) stored in ./input/
abaqus_subroutine_file_name = 'subroutine_export.f'
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_file_name = 'pace3D_pore-pressure.dat'
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_initial_file_name = 'pace3D_pore-pressure_initial.dat'

pace3d.set_path('work', work_directory)
pace3d.set_path('input', pace3d.get_path('work') / 'input')
pace3d.set_file('pore_pressure', pace3d.get_path('input') / pace3d_pore_pressure_file_name)
pace3d.set_file('initial_pore_pressure', pace3d.get_path('input') / pace3d_pore_pressure_initial_file_name)

# Handling input files and paths
abaqus.set_path('work', work_directory)
abaqus.set_path('input', abaqus.get_path('work') / 'input')
abaqus.set_path('output', abaqus.get_path('work') / 'output')
abaqus.set_path('scratch', abaqus.get_path('output') / 'scratch')

abaqus.set_file('subroutine', abaqus.get_path('input') / abaqus_subroutine_file_name)

number_of_iterations = 1
abaqus_part_name = 'Part-1'

# Log environmental variables
log.debug(f'abaqus_work_path: {abaqus.get_path("work")}')
log.debug(f'abaqus_job_name: {abaqus_job_name}')
log.debug(f'abaqus_subroutine_file_name: {abaqus.get_file("subroutine")}')
log.debug(f'pace3d_pore_pressure_file_name: {pace3d.get_file("pore_pressure")}')
log.debug(f'pace3d_pore_pressure_initial_file_name: {pace3d.get_file("initial_pore_pressure")}')
log.info(f'number_of_iterations: {number_of_iterations}')

# #################################################################################
# Cleaning up and preparing for first iteration of simulation
# Clean up process for folder
abaqus.path_cleanup('output')

# Preparing first iteration (geostatic)
log.info('Preparing first iterations')

step_name = 'initial'

actual_step = abaqus.iterations.add_iteration_step(step_name)
actual_step.create_step_folder(abaqus.get_path('output'))

# log.info(f'Start Iteration No. {iteration_cnt}')

# Load Abaqus nodes and coordinates from input file
log.info(f'Read Abaqus node and coordinates for part {abaqus_part_name}')

abaqus.init_engine({'input_file': abaqus.get_path('input') / f'{abaqus_job_name}.inp'})

exit()
# #################################################################################

abaqus_mesh = inp.read_part_nodes(abaqus_input_file, abaqus_part_name)
nodes = abaqus_mesh[3]  # Abaqus mesh nodes (without mesh)

# Check if the initial pore pressure distribution is given as an data file. Otherwise the initial pore pressure
# distribution of Abaqus will be used.
if not os.path.isfile(abaqus_input_path + '/' + pace3d_pore_pressure_initial_file_name):
    log.warning('pace3d_pore_pressure_initial_file_name: "%s" does not exist or is not a regular file. Regular Abaqus '
              'pore pressure distribution will be used.',
              abaqus_input_path + '/' + pace3d_pore_pressure_initial_file_name)
    pace3d_initials_given = False

else:
    pace3d_initials_given = True

if pace3d_initials_given:
    # Load Pace3D files into ndArrays
    pace3d_data = mt.read_pace3d(pace3d_pore_pressure_initial_file_name, abaqus_input_path)  # Pace3D data - X|Y|Z|VALUES

    # Set parameters for transition
    mesh_in = numpy.array([pace3d_data[0], pace3d_data[1]])  # Input/start mesh
    mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])  # Output/target mesh
    data_in_orig = pace3d_data[3]  # Original Pace3D mesh values (without mesh)

    # Transition
    log.info('Data transition from mesh_in to mesh_out')
    data_out = mt.mesh_transformation(mesh_in, mesh_out, data_in_orig)  # Transition of Pace3D pore pressure values
    # mt.transformation_validation(mesh_in, mesh_out, data_in_orig)

# Prepare Abaqus input-file
log.info('Prepare Abaqus input-file')
nset_dict = inp.create_nodesets_all(nodes, 'PP')  # Dictionary of node|node_names_set
nset_list_dict = inp.create_nodesets_all_list(nset_dict, abaqus_part_name)  # Dictionary of nodes|node_set

if pace3d_initials_given:
    # Dictionary of nodes|boundary conditions
    bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], data_out[2]], 8)
else:
    bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], abaqus_pore_pressure_value], 8)

# Write input- and bash-file
# Current job name consists of abaqus_job_name and current iteration number
current_job_name = abaqus_job_name + '_' + str(iteration_cnt)
# Current job folder name
current_job_folder = abaqus_output_path + subfolder
# Write input file
current_input_file = inp.write_inputfile(bc_dict, nset_list_dict, abaqus_input_file, current_job_name,
                                             current_job_folder)
log.info('Write input file: %s', current_input_file)
# bash file in subfolder
current_bash_file = inp.write_bashfile_windows(current_job_folder, current_input_file, current_job_name,
                                               abaqus_subroutine_file, abaqus_scratch_path)
log.info('Write windows bash file: %s', current_bash_file)

# Start simulation
log.info('Start Simulia Abaqus simulation')
current_bash_file_win = current_bash_file.replace('/', '\\')  # Is this necessary? Shall be managed elsewhere
subprocess.call(current_bash_file_win, shell=True, cwd=current_job_folder)  # Start simulation in shell
log.info('End Simulia Abaqus simulation')
log.info('End Iteration No. %d', iteration_cnt)