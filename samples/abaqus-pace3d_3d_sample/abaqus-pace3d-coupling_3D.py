import logging
import sys
from pathlib import Path

from utils.grid import Grid
from utils.grid_transformer import GridTransformer
from utils.simulation_handler import SimulationHandler

# Set root directory to current path
root_directory = Path(Path().cwd())

# #################################################################################
# Initialize the logger: logging class
# Logfile name will be saved in 'root_directory'
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
simulation_name = 'AbaqusPace3dCoupling'
number_of_steps = 1
abaqus_part_name = 'Reservoir-1-Crop'
abaqus_assembly_name = 'Reservoir-1-Crop-1'
abaqus_initial_pore_pressure_value = 62000000  # Constant pore pressure value in N/m²

# Initialize simulation handler
sim = SimulationHandler(simulation_name)
abaqus_handler = sim.add_engine('abaqus')
pace3d_handler = sim.add_engine('pace3d')

# Initialize root path (input and output folder are set additionally)
# A specific sub folder for input and output files can be set via sim.set_input_path() or sim.set_output_path(). If
# it is not set defaults will be used: input folder: input; output folder: output.
sim.set_root_path(root_directory)
sim.output_path_cleanup()  # Clean up process for output folder

# Name of Abaqus subroutine-file (f95) stored in ./input/
abaqus_subroutine_file_name = 'subroutine_export.f'
abaqus_input_file_name = 'abaqus_coupling.inp'
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_file_name = 'pace3D_pore-pressure.dat'

# Set Pace3D paths and files
pace3d_handler.set_path('input', sim.get_input_path())
pace3d_handler.set_path('output', sim.get_output_path() / 'pace3d')
# pace3d_handler.set_file('pore_pressure', pace3d_handler.get_path('input') / pace3d_pore_pressure_file_name) # FIXME missing file
# Initialize Pace3D engine
pace3d_handler.init_engine()

# Set Abaqus paths and files
abaqus_handler.set_path('input', sim.get_input_path())
abaqus_handler.set_path('output', sim.get_output_path() / 'abaqus')
abaqus_handler.set_file('subroutine', abaqus_handler.get_path('input') / abaqus_subroutine_file_name)
abaqus_handler.set_file('input_file', abaqus_handler.get_path('input') / abaqus_input_file_name)
# Because of the size of the model a Abaqus scratch directory is set. This directory will be used to save temporary
# files while the simulation is running.
abaqus_handler.set_path('scratch', abaqus_handler.get_path('output') / 'scratch')
# Initialize Simulia Abaqus engine
abaqus_handler.init_engine({'input_file': abaqus_handler.get_file('input_file')})

# Log environmental variables
log.debug(f'root_directory: {sim.get_root_path()}')
log.debug(f'simulation_handler_name: {sim.name}')
log.debug(f'abaqus_subroutine_file_name: {abaqus_handler.get_file("subroutine")}')
# log.debug(f'pace3d_pore_pressure_file_name: {pace3d_handler.get_file("pore_pressure")}')  # FIXME missing file
log.info(f'number_of_iterations: {number_of_steps}')

# #################################################################################
# Preparing first iteration (geostatic)
log.info('Preparing first iterations')

# Initiate first iteration step (initial) and create subfolders for it.
step_name = 'initial'
actual_step = sim.add_iteration_step(step_name)
actual_step['abaqus'].create_step_folder(abaqus_handler.get_path('output'))

# The initial grid/mesh will be read from the Abaqus input file and stored in a grid object in the actual step.
actual_step['abaqus'].grid.initiate_grid(abaqus_handler.engine.get_nodes(abaqus_part_name))

# Store scratch path in Abaqus engine
abaqus_handler.engine.paths['scratch'] = abaqus_handler.get_path('scratch')

# Create node sets for boundary conditions
abaqus_handler.engine.create_node_set_names('PP', actual_step['abaqus'].grid)
abaqus_handler.engine.create_node_set_all_list('PP', abaqus_assembly_name)

# Set constant initial pore pressure for Abaqus simulation
log.debug(f'Setting constant for initial pore pressure.')
# Get dict of empty nodes
nodes_dict = actual_step['abaqus'].grid.get_empty_nodes()
# Set pore pressure values to nodes
for node_number in nodes_dict.keys():
    nodes_dict[node_number] = abaqus_initial_pore_pressure_value
actual_step['abaqus'].grid.set_node_values('pore_pressure', nodes_dict)

# Finally create boundary condition to be added into a Abaqus step in the input file
abaqus_handler.engine.create_boundary_condition('PP', actual_step['abaqus'].grid.get_node_values('pore_pressure'), 8)

# Write input- and bash-file
# Current job name consists of abaqus_job_name and current step name
actual_step['abaqus'].set_prefix(f'{sim.name}_{step_name}')
abaqus_handler.set_file(f'input_file_{step_name}',
                        abaqus_handler.engine.write_input_file('PP',
                                                               actual_step['abaqus'].get_prefix(),
                                                               actual_step['abaqus'].get_path()))

abaqus_handler.set_file(f'bash_file_{step_name}',
                        abaqus_handler.engine.write_bash_file(
                            # Path of the actual step output
                            path=actual_step['abaqus'].get_path(),
                            # Path of input file for this step
                            input_file_path=abaqus_handler.get_file(f'input_file_{step_name}'),
                            # Path of user subroutine
                            user_subroutine_path=abaqus_handler.get_file('subroutine'),
                            # Add any valid abaqus parameter in here
                            additional_parameters='cpus=2 interactive',
                            # Tell Abaqus to use scratch path
                            use_scratch_path=True
                        ))

# Start the simulation by calling a sub process
sim.call_subprocess(abaqus_handler.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)

# #################################################################################
# Postprocessing Abaqus simulation
abaqus_handler.set_file(f'ouput_file_{step_name}_void-ratio', actual_step['abaqus'].get_path() /
                        f'{actual_step["abaqus"].get_prefix()}_void-ratio.csv')

# Read pore pressure from previous ended simulation stored in **_pore-pressure.csv and store those in actual step
# as grid values. Those can be used to generate randomly lowered pore pressure values.
void_ratio_import = abaqus_handler.engine.read_csv_file(
    abaqus_handler.get_file(f'ouput_file_{step_name}_void-ratio'))

# Initiate a new temporary grid for imported pore pressure
pore_pressure_import_grid = Grid()
pore_pressure_import_grid.initiate_grid(void_ratio_import, 'void_ratio')

# Transform void ratio from imported grid to abaqus engine's grid
transformer = GridTransformer()
transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
transformer.add_grid(pore_pressure_import_grid, 'import')
transformer.find_nearest_neighbors('import', 'abaqus', 4)
transformer.transition('import', 'void_ratio', 'abaqus')

# #################################################################################
# PACE 3D STUFF
# Prepare Transfer
# Transfer Abaqus pore pressure results into Pace3D Grid object
transformer = GridTransformer()
transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')
transformer.find_nearest_neighbors('abaqus', 'pace3d', 4)
transformer.transition('abaqus', 'void_ratio', 'pace3d')

# Transfer from grid to Pace3D
# Start Pace3D Simulation

# Transfer Pace3d simulation results into Grid object
data = pace3d_handler.engine.read_csv_file(pace3d_handler.get_file('pore_pressure'))
actual_step['pace3d'].grid.initiate_grid(data, 'pore_pressure')

# #################################################################################
# Next Iteration
for x in range(0, number_of_steps):
    # #################################################################################
    # GENERAL STUFF
    # Add a new step which is a copy of the previous step including all grids.
    step_name = f'step_{x + 1}'
    actual_step = sim.add_iteration_step(step_name, copy_previous=True)
    previous_step = sim.get_previous_iterations()  # for quick access

    # #################################################################################
    # SIMULIA ABAQUS STUFF
    # Preparing simulation iteration
    actual_step['abaqus'].set_step_folder(abaqus_handler.get_path('output'))
    actual_step['abaqus'].set_prefix(f'{sim.name}_{step_name}')

    transformer = GridTransformer()
    transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
    transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')

    transformer.find_nearest_neighbors('pace3d', 'abaqus', 2)
    transformer.transition('pace3d', 'pore_pressure', 'abaqus')

    abaqus_handler.engine.create_boundary_condition('PP',
                                                    actual_step['abaqus'].grid.get_node_values('pore_pressure'),
                                                    8)

    # Copy all files into the new directory to restart the previous analysis
    # A restart job is only possible if the files of the previous simulation are in
    # the same folder as the current simulation
    abaqus_handler.engine.copy_previous_result_files(previous_step['abaqus'].path, actual_step['abaqus'].path)

    # Prepare input and batch file
    name = f'{sim.name}_{step_name}'
    abaqus_handler.set_file(f'input_file_{step_name}',
                            abaqus_handler.engine.write_input_file('PP', name, actual_step['abaqus'].get_path()))

    abaqus_handler.set_file(f'input_file_{step_name}',
                            abaqus_handler.engine.write_input_file_restart('PP',
                                                                           actual_step['abaqus'].get_prefix(),
                                                                           actual_step['abaqus'].get_path(),
                                                                           abaqus_handler.get_file(f'input_file_'
                                                                                                   f'{previous_step["abaqus"].name}'),
                                                                           actual_step['abaqus'].name,
                                                                           previous_step["abaqus"].step_no + 1,
                                                                           # Set to False if each sim should
                                                                           # start at the very beginning
                                                                           True))

    abaqus_handler.set_file(f'bash_file_{step_name}',
                            abaqus_handler.engine.write_bash_file(
                                # Path of the actual step output
                                path=actual_step['abaqus'].get_path(),
                                # Path of input file for this step
                                input_file_path=abaqus_handler.get_file(f'input_file_{step_name}'),
                                # Path of user subroutine
                                user_subroutine_path=abaqus_handler.get_file('subroutine'),
                                # Add any valid abaqus parameter in here
                                additional_parameters='cpus=2 interactive',
                                # Name of the old job to resume
                                old_job_name=previous_step['abaqus'].get_prefix()
                            ))

    sim.call_subprocess(abaqus_handler.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)

    sim.engines['abaqus'].engine.clean_previous_files(previous_step['abaqus'].name, actual_step['abaqus'].path)

    abaqus_handler.set_file(f'ouput_file_{step_name}_void-ratio', actual_step['abaqus'].get_path() /
                            f'{actual_step["abaqus"].get_prefix()}_void-ratio.csv')

    # Read pore pressure from previous ended simulation stored in **_pore-pressure.csv and store those in actual step
    # as grid values. Those can be used to generate randomly lowered pore pressure values.
    void_ratio_import = abaqus_handler.engine.read_csv_file(
        abaqus_handler.get_file(f'ouput_file_{step_name}_void-ratio'))

    # Initiate a new temporary grid for imported pore pressure
    pore_pressure_import_grid = Grid()
    pore_pressure_import_grid.initiate_grid(void_ratio_import, 'void_ratio')

    # Transform void ratio from imported grid to abaqus engine's grid
    transformer = GridTransformer()
    transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
    transformer.add_grid(pore_pressure_import_grid, 'import')
    transformer.find_nearest_neighbors('import', 'abaqus', 4)
    transformer.transition('import', 'void_ratio', 'abaqus')

    # #################################################################################
    # PACE 3D STUFF
    # Prepare Transfer
    # Transfer Abaqus void ratio results into Pace3D Grid object
    transformer = GridTransformer()
    transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
    transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')
    transformer.find_nearest_neighbors('abaqus', 'pace3d', 4)
    transformer.transition('abaqus', 'void_ratio', 'pace3d')

    # Transfer from grid to Pace3D
    # Start Pace3D Simulation
    # Transfer Pace3d simulation results into Grid object
