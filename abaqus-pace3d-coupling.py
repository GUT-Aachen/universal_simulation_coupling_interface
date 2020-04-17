from utils.engines_handler import EnginesHandler
import logging
import sys
from pathlib import Path
import pprint
from utils.grid_transformer import GridTransformer

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
abaqus.set_path(f'subfolder_{step_name}', actual_step.create_step_folder(abaqus.get_path('output')))

pace3d.iterations.add_iteration_step(step_name)

# log.info(f'Start Iteration No. {iteration_cnt}')

# Load Abaqus nodes and coordinates from input file
log.info(f'Read Abaqus node and coordinates for part {abaqus_part_name}')

abaqus.init_engine({'input_file': abaqus.get_path('input') / f'{abaqus_job_name}.inp'})
pace3d.init_engine()
# parts = abaqus.engine.get_part_names()
# instances = abaqus.engine.get_instance_names()
actual_step.grid.initiate_grid(abaqus.engine.get_nodes('Part-1'))

abaqus.engine.paths['scratch'] = abaqus.get_path('scratch')
abaqus.engine.create_node_set_names('PP', actual_step.grid)
abaqus.engine.create_node_set_all_list('PP', 'Part-1')

# Check if the initial pore pressure distribution is given as an data file. Otherwise the initial pore pressure
# distribution of Abaqus will be used.
if pace3d.get_file('initial_pore_pressure'):
    log.debug(f'Setting initial pore pressure distribution by pace3d distribution data.')
    data = pace3d.engine.read_csv_file(pace3d.get_file('initial_pore_pressure'))
    pace3d.iterations[step_name].grid.initiate_grid(data, 'pore_pressure')

    transformer = GridTransformer()
    transformer.add_grid(actual_step.grid, 'abaqus')
    transformer.add_grid(pace3d.iterations['initial'].grid, 'pace3d')

    transformer.find_nearest_neighbors('pace3d', 'abaqus', 2)
    transformer.transition('pace3d', 'pore_pressure', 'abaqus')

    abaqus.engine.create_boundary_condition('PP', actual_step.grid.get_node_values('pore_pressure'), 8)
else:
    log.debug(f'Setting constant for initial pore pressure.')
    # TODO
    # abaqus.engine.create_boundary_condition('PP', actual_step.grid.get_node_values('pore_pressure'), 8)
    #bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], abaqus_pore_pressure_value], 8)

# Write input- and bash-file
# Current job name consists of abaqus_job_name and current step name
name = f'{abaqus_job_name}_{step_name}'
abaqus.set_file(f'input_file_{step_name}', abaqus.engine.write_input_file('PP', name, actual_step.get_path()))

abaqus.set_file(f'bash_file_{step_name}', abaqus.engine.write_bash_file(actual_step.get_path(),
                                                                        abaqus.get_file(f'input_file_{step_name}'),
                                                                        abaqus.get_file('subroutine'),
                                                                        True,
                                                                        'cpus=2'))

abaqus.call_subprocess(str(abaqus.get_file(f'bash_file_{step_name}')), str(abaqus.get_path(f'subfolder_{step_name}')))
exit()
# #################################################################################

subprocess.call(current_bash_file_win, shell=True, cwd=current_job_folder)  # Start simulation in shell
log.info('End Simulia Abaqus simulation')
