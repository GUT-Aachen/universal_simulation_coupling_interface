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

# Initialize simulation handler
sim = SimulationHandler(simulation_name)

# Initialize root path (input and output folder are set additionally)
# A specific sub folder for input and output files can be set via sim.set_input_path() or sim.set_output_path(). If
# it is not set defaults will be used: input folder: input; output folder: output.
sim.set_root_path(root_directory)
sim.output_path_cleanup()  # Clean up process for output folder

# Add specific engine handler, here: Simulia Abaqus
abaqus_handler = sim.add_engine('abaqus')
pace3d_handler = sim.add_engine('pace3d')

# Tell the Abaqus engine where paths and files to be found. The scratch folder is used by Abaqus to store temporarily
# needed files on the disk.
# Input: Contains all files that are needed to run the simulation
# Output: Is the root folder for the output. In here all generated files will be stored.
# Scratch: Abaqus can use a scratch folder so store temporary files
abaqus_handler.set_path('input', sim.get_input_path())
abaqus_handler.set_path('output', sim.get_output_path() / 'abaqus')

# To get an output from Abaqus at the end of each iteration step, a so called user subroutine is needed.
# Name of Abaqus subroutine-file (f95) stored in ./input/
abaqus_subroutine_file_name = 'subroutine_export.f'
abaqus_handler.set_file('subroutine', abaqus_handler.get_path('input') / abaqus_subroutine_file_name)

# Set Abaqus input file to Abaqus engine
abaqus_handler.set_file('input_file', abaqus_handler.get_path('input') / 'abaqus_coupling.inp')

# Initialize the Simulia Abaqus and Pace3D engine. Any engine needs a dictionary of input parameters. In case of
# Abaqus only one key is needed: input_file
abaqus_handler.init_engine({'input_file': abaqus_handler.get_file('input_file')})
pace3d_handler.init_engine()

# Set Pace3D paths and files
pace3d_handler.set_path('input', sim.get_input_path())
pace3d_handler.set_path('output', sim.get_output_path() / 'pace3d')
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_file_name = 'pace3D_pore-pressure.dat'
pace3d_handler.set_file('pore_pressure', pace3d_handler.get_path('input') / pace3d_pore_pressure_file_name)
# Name of Pace3D pore pressure file (csv) stored in ./input/
pace3d_pore_pressure_initial_file_name = 'pace3D_pore-pressure_initial.dat'
pace3d_handler.set_file('initial_pore_pressure', pace3d_handler.get_path('input') /
                        pace3d_pore_pressure_initial_file_name)

# Set the number of steps to be done
number_of_steps = 1

# According to the Abaqus engine a specific part has to be defined for the coupling. In more complex simulations
# multiple parts can be chosen and coupled. The name must be the same as shown in the Abaqus input file
# in the input folder (abaqus_pseudo_coupling.inp, see line 16).
abaqus_part_name = 'Part-1'

# Log environmental variables to make the log traceable
log.debug(f'root_directory: {sim.get_root_path()}')
log.debug(f'simulation_handler_name: {sim.name}')
log.debug(f'abaqus_subroutine_file_name: {abaqus_handler.get_file("subroutine")}')
log.debug(f'pace3d_pore_pressure_file_name: {pace3d_handler.get_file("pore_pressure")}')
log.debug(f'pace3d_pore_pressure_initial_file_name: {pace3d_handler.get_file("initial_pore_pressure")}')
log.info(f'number_of_iterations: {number_of_steps}')

# #################################################################################
# Preparing first step (geostatic)
log.info('Preparing first step')

# Set the name for the first simulation step. Here it is a geostatic calculation step. The step name is only used to
# identify the steps in this interface. The name is not directly connected to the Abaqus input file.
step_name = 'initial'

# Initiate the first step (initial) and create a sub folder for it. Sub folder name equals the step name. The new
# created step will be linked to a variable called actual_step. The step can alternatively called by
# sim.get_current_iterations().
actual_step = sim.add_iteration_step(step_name)
actual_step['abaqus'].create_step_folder(abaqus_handler.get_path('output'))

# The initial grid/mesh will be read from the Abaqus input file and stored in a grid object in the actual step. This
# decouples the input file and the grid completely. Each nodes values can now be stored in this grid object.
actual_step['abaqus'].grid.initiate_grid(abaqus_handler.engine.get_nodes(abaqus_part_name))

# To modify boundary conditions within a simulation in Abaqus node sets have to be defined. Here we want to change
# the pore pressure at each node of Part-1. Therefore a each node needs its own set. In a first step all nodes get their
# individual names like
# 234: node-234
abaqus_handler.engine.create_node_set_names('PP', actual_step['abaqus'].grid)
# In a second step a dictionary by node numbers and set_name like
# 234: *Nset, nset = node-234, internal, instance = Part-1 \n 234
# will be created in the engine.
abaqus_handler.engine.create_node_set_all_list('PP', abaqus_part_name)

# Set initial pore pressure distribution imported from an data file from Pace3D.
log.debug(f'Setting initial pore pressure distribution by pace3d distribution data.')
data = pace3d_handler.engine.read_csv_file(pace3d_handler.get_file('initial_pore_pressure'))
actual_step['pace3d'].grid.initiate_grid(data, 'pore_pressure')

# Transform data from Pace3D grid to Simulia Abaqus Mesh
transformer = GridTransformer()
transformer.add_grid(actual_step['abaqus'].grid, 'abaqus')
transformer.add_grid(actual_step['pace3d'].grid, 'pace3d')
transformer.find_nearest_neighbors('pace3d', 'abaqus', 4)
transformer.transition('pace3d', 'pore_pressure', 'abaqus')

# Finally create boundary condition to be added into a Abaqus step in the input file
abaqus_handler.engine.create_boundary_condition('PP', actual_step['abaqus'].grid.get_node_values('pore_pressure'), 8)

# Write Abaqus input- and Microsoft Windows bash-file
# Prefix for output files consists of simulation name and current step name
actual_step['abaqus'].set_prefix(f'{sim.name}_{step_name}')
abaqus_handler.set_file(f'input_file_{step_name}',
                        abaqus_handler.engine.write_input_file('PP',
                                                               actual_step['abaqus'].get_prefix(),
                                                               actual_step['abaqus'].get_path()))

# In the bash file a couple of parameters can be set to run the simulation.
abaqus_handler.set_file(f'bash_file_{step_name}',
                        abaqus_handler.engine.write_bash_file(
                            # Path of the actual step output
                            path=actual_step['abaqus'].get_path(),
                            # Path of input file for this step
                            input_file_path=abaqus_handler.get_file(f'input_file_{step_name}'),
                            # Path of user subroutine
                            user_subroutine_path=abaqus_handler.get_file('subroutine'),
                            # Add any valid abaqus parameter in here
                            additional_parameters='cpus=2 interactive'
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

    transformer.find_nearest_neighbors('pace3d', 'abaqus', 4)
    transformer.transition('pace3d', 'pore_pressure', 'abaqus')

    # Create modified boundary conditions in Abaqus input file. This must be done according to Abaqus manual
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
