import logging
import sys
from pathlib import Path
from utils.grid_transformer import GridTransformer
from utils.simulation_handler import SimulationHandler

root_directory = Path('D:\Abaqus_Work_2019\Abaqus-Pace3D-Transition')

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

# Set simulation name
simulation_name = 'M3-200407'
number_of_iterations = 2
abaqus_part_name = 'Reservoir-1-Crop'
abaqus_assembly_name = 'Reservoir-1-Crop-1'

# Initialize simulation handler
sim = SimulationHandler(simulation_name)
abaqus = sim.add_engine('abaqus')
pace3d = sim.add_engine('pace3d')

# Initialize root path (input and output folder are set additionally)
sim.set_root_path(root_directory)
sim.output_path_cleanup()  # Clean up process for output folder

# Name of Abaqus subroutine-file (f95) stored in ./input/
abaqus_subroutine_file_name = 'subroutine_export.f'
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_file_name = 'pace3D_pore-pressure.dat'
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_initial_file_name = 'pace3D_pore-pressure_initial.dat'

# Set Pace3D paths and files
pace3d.set_path('input', sim.get_input_path())
pace3d.set_path('output', sim.get_output_path() / 'pace3d')
pace3d.set_file('pore_pressure', pace3d.get_path('input') / pace3d_pore_pressure_file_name)
pace3d.set_file('initial_pore_pressure', pace3d.get_path('input') / pace3d_pore_pressure_initial_file_name)

# Set Abaqus paths and files
abaqus.set_path('input', sim.get_input_path())
abaqus.set_path('output', sim.get_output_path() / 'abaqus')
abaqus.set_path('scratch', abaqus.get_path('output') / 'scratch')
abaqus.set_path('scratch', abaqus.get_path('output') / 'scratch')
abaqus.set_file('subroutine', abaqus.get_path('input') / abaqus_subroutine_file_name)

# Log environmental variables
log.debug(f'root_directory: {sim.get_root_path()}')
log.debug(f'simulation_handler_name: {sim.name}')
log.debug(f'abaqus_subroutine_file_name: {abaqus.get_file("subroutine")}')
log.debug(f'pace3d_pore_pressure_file_name: {pace3d.get_file("pore_pressure")}')
log.debug(f'pace3d_pore_pressure_initial_file_name: {pace3d.get_file("initial_pore_pressure")}')
log.info(f'number_of_iterations: {number_of_iterations}')

# #################################################################################
# Preparing first iteration (geostatic)
log.info('Preparing first iterations')

step_name = 'initial'

actual_step = sim.add_iteration_step(step_name)
actual_step['abaqus'].create_step_folder(abaqus.get_path('output'))

abaqus.init_engine({'input_file': abaqus.get_path('input') / f'{sim.name}.inp'})
pace3d.init_engine()
actual_step['abaqus'].grid.initiate_grid(abaqus.engine.get_nodes(abaqus_part_name))

abaqus.engine.paths['scratch'] = abaqus.get_path('scratch')
abaqus.engine.create_node_set_names('PP', actual_step['abaqus'].grid)
abaqus.engine.create_node_set_all_list('PP', abaqus_assembly_name)

# Check if the initial pore pressure distribution is given as an data file. Otherwise the initial pore pressure
# distribution of Abaqus will be used.
if pace3d.get_file('initial_pore_pressure'):
    log.debug(f'Setting initial pore pressure distribution by pace3d distribution data.')
    data = pace3d.engine.read_csv_file(pace3d.get_file('initial_pore_pressure'))
    actual_step['pace3d'].grid.initiate_grid(data, 'pore_pressure')

    transformer = GridTransformer()
    transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
    transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')

    transformer.find_nearest_neighbors('pace3d', 'abaqus', 2)
    transformer.transition('pace3d', 'pore_pressure', 'abaqus')

    abaqus.engine.create_boundary_condition('PP', actual_step['abaqus'].grid.get_node_values('pore_pressure'), 8)
else:
    log.debug(f'Setting constant for initial pore pressure.')
    # TODO
    # abaqus.engine.create_boundary_condition('PP', actual_step.grid.get_node_values('pore_pressure'), 8)
    # bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], abaqus_pore_pressure_value], 8)

# Write input- and bash-file
# Current job name consists of abaqus_job_name and current step name
name = f'{sim.name}_{step_name}'
abaqus.set_file(f'input_file_{step_name}', abaqus.engine.write_input_file('PP', name, actual_step['abaqus'].get_path()))

abaqus.set_file(f'bash_file_{step_name}', abaqus.engine.write_bash_file(actual_step['abaqus'].get_path(),
                                                                        abaqus.get_file(f'input_file_{step_name}'),
                                                                        abaqus.get_file('subroutine'),
                                                                        True,
                                                                        'cpus=4'))

# #################################################################################
sim.call_subprocess(abaqus.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)
# #################################################################################
# Postprocessing Abaqus simulation
# Check if completed abaqus.check_iteration_successful()
# Reading output, write into grid
# #################################################################################
# PACE 3D STUFF
# Prepare Transfer
# Transfer from grid to Pace3D
# Start Simulation
# Transfer from Pace3D to Grid
# #################################################################################
# Next Iteration
for x in range(0, number_of_iterations):
    # Preparing simulation iteration
    step_name = f'step_{x+1}'

    # Add a new step which is a copy of the previous step including all grids.
    actual_step = sim.add_iteration_step(step_name, copy_previous=True)
    actual_step['abaqus'].set_step_folder(abaqus.get_path('output'))
    previous_step = sim.get_previous_iterations()

    # Do some random stuff
    data = pace3d.engine.read_csv_file(pace3d.get_file('pore_pressure'))
    actual_step['pace3d'].grid.initiate_grid(data, 'pore_pressure')

    transformer = GridTransformer()
    transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
    transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')

    transformer.find_nearest_neighbors('pace3d', 'abaqus', 2)
    transformer.transition('pace3d', 'pore_pressure', 'abaqus')

    abaqus.engine.create_boundary_condition('PP', actual_step['abaqus'].grid.get_node_values('pore_pressure'), 8)

    # Copy all files into the new directory to restart the previous analysis
    # A restart job is only possible if the files of the previous simulation are in
    # the same folder as the current simulation
    abaqus.engine.copy_previous_result_files(previous_step['abaqus'].path, actual_step['abaqus'].path)

    # Prepare input and batch file
    name = f'{sim.name}_{step_name}'
    abaqus.set_file(f'input_file_{step_name}',
                    abaqus.engine.write_input_file('PP', name, actual_step['abaqus'].get_path()))

    abaqus.set_file(f'bash_file_{step_name}', abaqus.engine.write_bash_file(actual_step['abaqus'].get_path(),
                                                                            abaqus.get_file(f'input_file_{step_name}'),
                                                                            abaqus.get_file('subroutine'),
                                                                            True,
                                                                            'cpus=4'))

    sim.call_subprocess(abaqus.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)

    sim.engines['abaqus'].engine.clean_previous_files(previous_step['abaqus'].name, actual_step['abaqus'].path)
