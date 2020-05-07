import logging
import sys
from pathlib import Path
from utils.simulation_handler import SimulationHandler
from utils.random_grid import GaussRandomizeGrid

# The goal of this simulation is to show that this framework can be used to change e.g. boundary conditions at each
# node of a mesh in a Simulia Abaqus simulation. This corresponds to the application of a pseudo coupling, means that
# only one engine is used and the modification of a boundary condition (here pore pressure) is made by a simple function
# or (like here) with a random lowering of the existing boundary conditions. This can
# also be used while developing an new engine.

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
simulation_name = 'PseudoCoupling'

# Initialize simulation handler
sim = SimulationHandler(simulation_name)

# Initialize root path (input and output folder are set additionally)
# A specific sub folder for input and output files can be set via sim.set_input_path() or sim.set_output_path(). If
# it is not set defaults will be used: input folder: input; output folder: output.
sim.set_root_path(root_directory)
sim.output_path_cleanup()  # Clean up process for output folder

# Add specific engine handler, here: Simulia Abaqus
abaqus_handler = sim.add_engine('abaqus')

# Tell the Abaqus engine where paths and files to be found. The scratch folder is used by Abaqus to store temporarily
# needed files on the disk.
abaqus_handler.set_path('input', sim.get_input_path())
abaqus_handler.set_path('output', sim.get_output_path() / 'abaqus')
abaqus_handler.set_path('scratch', abaqus_handler.get_path('output') / 'scratch')

# To get an output from Abaqus at the end of each iteration step, a so called user subroutine is needed.
# Name of Abaqus subroutine-file (f95) stored in ./input/
abaqus_subroutine_file_name = 'subroutine_export.f'
abaqus_handler.set_file('subroutine', abaqus_handler.get_path('input') / abaqus_subroutine_file_name)

# Set Abaqus input file to Abaqus engine
abaqus_handler.set_file('input_file', abaqus_handler.get_path('input') / 'abaqus_pseudo_coupling.inp')

# Initialize the Simulia Abaqus engine. Any engine needs a dictionary of input parameters. In case of Abaqus only one
# key is needed: input_file
abaqus_handler.init_engine({'input_file': abaqus_handler.get_file('input_file')})

# Set the number of steps to be done
number_of_steps = 5

# According to the Abaqus engine a specific part has to be defined for the coupling. In more complex simulations
# multiple parts can be chosen and coupled. The name must be the same as shown in the Abaqus input file
# in the input folder (abaqus_pseudo_coupling.inp, see line 16).
abaqus_part_name = 'Part-1'

# Log environmental variables to make the log traceable
log.debug(f'root_directory: {sim.get_root_path()}')
log.debug(f'simulation_handler_name: {sim.name}')
log.debug(f'abaqus_subroutine_file_name: {abaqus_handler.get_file("subroutine")}')
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

abaqus_handler.engine.paths['scratch'] = abaqus_handler.get_path('scratch')

# To modify boundary conditions within a simulation in Abaqus node sets have to be defined. Here we want to change
# the pore pressure at each node of Part-1. Therefore a each node needs its own set. In a first step all nodes get their
# individual names like
# 234: node-234
abaqus_handler.engine.create_node_set_names('PP', actual_step['abaqus'].grid)
# In a second step a dictionary by node numbers and set_name like
# 234: *Nset, nset = node-234, internal, instance = Part-1 \n 234
# will be created in the engine.
abaqus_handler.engine.create_node_set_all_list('PP', 'Part-1')

# A individual pore pressure can be set for each node. In this sample we set the pore pressure to a constant value of
# 62000000 N/m² at any node.
abaqus_pore_pressure_value = 62000000
log.debug(f'Setting constant for initial pore pressure.')
# Get dict of empty nodes
nodes_dict = actual_step['abaqus'].grid.get_empty_nodes()
# Set pore pressure values to nodes
for node_number in nodes_dict.keys():
    nodes_dict[node_number] = abaqus_pore_pressure_value
actual_step['abaqus'].grid.set_node_values('pore_pressure', nodes_dict)

# Finally create boundary condition to be added into a Abaqus step in the input file
abaqus_handler.engine.create_boundary_condition('PP', actual_step['abaqus'].grid.get_node_values('pore_pressure'), 8)

# Write Abaqus input- and Microsoft Windows bash-file
# Current job name consists of abaqus_job_name and current step name
actual_step['abaqus'].set_prefix(f'{sim.name}_{step_name}')
abaqus_handler.set_file(f'input_file_{step_name}',
                        abaqus_handler.engine.write_input_file('PP',
                                                               actual_step['abaqus'].get_prefix(),
                                                               actual_step['abaqus'].get_path()))
# In the bash file a couple of parameters can be set to run the simulation.
abaqus_handler.set_file(f'bash_file_{step_name}',
                        abaqus_handler.engine.write_bash_file(
                            actual_step['abaqus'].get_path(),  # Path of the actual step output
                            abaqus_handler.get_file(f'input_file_{step_name}'),  # Path of input file for this step
                            abaqus_handler.get_file('subroutine'),  # Path of user subroutine
                            True,  # Shall scratch path be used for simulation?
                            'cpus=2 interactive'  # Add any valid abaqus parameter in here
                        ))

# Start the simulation by calling a sub process
sim.call_subprocess(abaqus_handler.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)

# abaqus_handler.set_file(f'ouput_file_{step_name}_pore-pressure', actual_step['abaqus'].get_path() /
#                         f'{actual_step["abaqus"].get_prefix()}_pore-pressure.csv')
# abaqus_handler.set_file(f'ouput_file_{step_name}_void-ratio', actual_step['abaqus'].get_path() /
#                         f'{actual_step["abaqus"].get_prefix()}_void-ratio.csv')


# Next iteration steps
for x in range(0, number_of_steps):
    # Set name for next steps.
    step_name = f'step_{x+1}'

    # Add a new step which is a copy of the previous step including all grids.
    actual_step = sim.add_iteration_step(step_name, copy_previous=True)
    actual_step['abaqus'].grid.get_node_values('pore_pressure')
    actual_step['abaqus'].set_step_folder(abaqus_handler.get_path('output'))
    previous_step = sim.get_previous_iterations()

    # Read pore pressure from previous ended simulation stored in **_pore-pressure.csv and store those in actual step
    # as grid values. Those can be used to generate randomly lowered pore pressure values.
    node_value_dict = previous_step['abaqus'].grid.get_node_values('pore_pressure')
    randomizer = GaussRandomizeGrid()
    abaqus_rand_data = randomizer.get_random_data_set(node_value_dict, -0.05, False)
    actual_step['abaqus'].grid.set_node_values('pore_pressure', abaqus_rand_data)

    # Create modified boundary conditions in Abaqus input file
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

    abaqus_handler.set_file(f'bash_file_{step_name}',
                            abaqus_handler.engine.write_bash_file(
                                actual_step['abaqus'].get_path(),  # Path of the actual step output
                                abaqus_handler.get_file(f'input_file_{step_name}'),  # Path of input file for this step
                                abaqus_handler.get_file('subroutine'),  # Path of user subroutine
                                True,  # Shall scratch path be used for simulation?
                                'cpus=2 interactive'  # Add any valid abaqus parameter in here
                            ))

    # Call the subprocess
    sim.call_subprocess(abaqus_handler.get_file(f'bash_file_{step_name}'), actual_step['abaqus'].path)

    # After subprocess ended all files from previous simulation can be deleted. Only files of the actual step remain
    # in the actual step output folder.
    sim.engines['abaqus'].engine.clean_previous_files(previous_step['abaqus'].name, actual_step['abaqus'].path)
