import numpy
import mesh_transition as mt
import random_mesh_input as rand
import abaqus_input as inp
import shutil
import os
import subprocess
import logging

# Set job name
abaqus_work_path = 'D:\Abaqus_Work_2019\Abaqus-Pace3D-Transition'
abaqus_job_name = 'Cube_PP_SubR'
abaqus_input_file_name = 'Cube_PP_SubR.inp'
abaqus_subroutine_file_name = 'subroutine_export.f'
abaqus_mesh_file_name = 'abaqus_matrix.csv'
abaqus_pore_pressure_file_name = 'abaqus_pore-pressure.csv'
number_of_iterations = 40

# Logfile name will be saved in 'abaqus_work_path'
log_file_name = abaqus_job_name + '.log'

# Handling input files and paths
# Replace backslashes in case of a windows path
abaqus_work_path = abaqus_work_path.replace("\\", "/")
abaqus_input_path = abaqus_work_path + '/input'
abaqus_output_path = abaqus_work_path + '/output'
abaqus_input_file = abaqus_input_path + '/' + abaqus_input_file_name
abaqus_subroutine_file = abaqus_input_path + '/' + abaqus_subroutine_file_name

# #################################################################################
# Initialize the logger: logging class
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=abaqus_work_path + '/' + log_file_name,
                    filemode='w')

# Define a handler writing INFO messages or higher to sys.stderr
consoleLogger = logging.StreamHandler()
consoleLogger.setLevel(logging.INFO)
# Set a format which is simpler for console use
format = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
consoleLogger.setFormatter(format)
logging.getLogger('').addHandler(consoleLogger)  # Add handler to root logger
log = logging.getLogger(__main__ + '.main')  # Define a logger for __main__ file

# Log environmental variables
log.debug('abaqus_work_path: %s', abaqus_work_path)
log.debug('abaqus_job_name: %s', abaqus_job_name)
log.debug('abaqus_input_file_name: %s', abaqus_input_file_name)
log.debug('abaqus_subroutine_file_name: %s', abaqus_subroutine_file_name)
log.debug('abaqus_mesh_file_name: %s', abaqus_mesh_file_name)
log.debug('abaqus_pore_pressure_file_name: %s', abaqus_pore_pressure_file_name)
log.info('number_of_iterations: %s', number_of_iterations)

# #################################################################################
# Cleaning up and preparing for first iteration of simulation
# Clean up process for folder
if os.path.exists(abaqus_output_path):
    log.info('* Cleanup process: Deleting output folder')
    log.info('Folder: ', abaqus_output_path)
    shutil.rmtree(abaqus_output_path)

# Preparing first iteration
log.info('Preparing first iterations')

current_input_file = ''  # Initiate variable for current input file
iteration_cnt = 0  # Initiate iteration counter
subfolder = '/step_' + str(iteration_cnt)  # Set current subfolder path

# Load Abaqus (and Pace3D) files into ndArrays
abaqus_mesh = mt.read_abaqus(abaqus_mesh_file_name, abaqus_input_path)  # Abaqus mesh original - X|Y|Z|NODES
abaqus_data = mt.read_abaqus(abaqus_pore_pressure_file_name, abaqus_input_path)  # Abaqus data - X|Y|Z|VALUES

# Set parameters for transition
mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])  # Input/start mesh
mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])  # Output/target mesh
data_in_orig = abaqus_data[3] # Original Abaqus mesh values (without mesh)
data_in_rand = rand.get_random_dataset(abaqus_data[3], -0.2, False)  # Randomized Abaqus mesh values (without mesh)
nodes = abaqus_mesh[3]  # Abaqus mesh nodes (without mesh)

# Transition
log.info('Data transition from mesh_in to mesh_out')
data_rand = mt.mesh_transformation(mesh_in, mesh_out, data_in_rand)  # Transition of randomized-abaqus-values

# Prepare Abaqus input-file
log.info('Prepare Abaqus input-file')
nset_dict = inp.create_nodesets_all(nodes, 'PP')  # Dictionary of node|node_names_set
bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], data_rand[2]], 8)  # Dictionary of nodes|boundary conditions
nset_list_dict = inp.create_nodesets_all_list(nset_dict, 'Part_1-1') # Dictionary of nodes|node_set

#Write input- and bash-file
current_job_name = abaqus_job_name + '_' + str(iteration_cnt)  # Current job name constits of abaqus_job_name and current iteration number
current_job_folder = abaqus_output_path + subfolder  # Current job folder name
current_input_file = inp.write_inputfile(bc_dict, nset_list_dict, abaqus_input_file, current_job_name, current_job_folder)  # Write input file
log.info('Write input file: %s', current_input_file)
current_bash_file = inp.write_bashfile_windows(current_job_folder, current_input_file, current_job_name, abaqus_subroutine_file) # bash file in subfolder
log.info('Write windows bash file: %s', current_bash_file)

# Start simulation
log.info('Start Simulia Abaqus simulation')
current_bash_file_win = current_bash_file.replace('/', '\\')  # Is this necessary? Shall be managed elsewhere
subprocess.call(current_bash_file_win, shell=True, cwd=current_job_folder) # Start simulation in shell
log.info('End Simulia Abaqus simulation')

# #################################################################################
# Next Iteration
for x in range(0, number_of_iterations):
    # Preparing simulation iteration
    iteration_cnt += 1  # Increment iteration number
    subfolder = '/step_' + str(iteration_cnt)  # subfolder for iteration
    step_name = 'Step_PPChange_' + str(iteration_cnt)  # step name
    log.info('Preparing simulation step: %s', step_name)

    # Save previous job folder and name
    prev_job_folder = current_job_folder
    prev_job_name = current_job_name

    # Set current job folder and name
    current_job_folder = abaqus_output_path + subfolder
    current_job_name = abaqus_job_name + '_' + str(iteration_cnt)

    # Clean up process for subfolder (if it exists)
    if os.path.exists(current_job_folder):
        log.info('Cleanup process: Deleting output subfolder (%s)', current_job_folder)
        shutil.rmtree(current_job_folder)

    # Check if previous simulation was sucessfully completed
    # As a first approach: check if msg-file exists
    if not os.path.isfile(prev_job_folder + '/' + prev_job_name + '.msg'):
        log.critical('Previous simulation not completed')
        exit()

    # Copy all files into the new directory to restart the previous analysis
    # A restart job is only possible if the files of the previous simulation are in
    # the same folder as the current simulation
    log.info('Copying files from previous simulation to current subfolder to restart analysis')
    shutil.copytree(prev_job_folder, current_job_folder)  # Copy files

    # Load Abaqus and Pace3D Files into arrays
    results_mesh_file_name = prev_job_name + '_matrix.csv'  # Name of mesh file
    log.info('Read new mesh from %s', results_mesh_file_name)
    abaqus_mesh = mt.read_abaqus(results_mesh_file_name, prev_job_folder)  # Load Abaqus mesh to ndArray

    results_pore_pressure_file_name = prev_job_name + '_pore-pressure.csv' # Name of pore pressure file
    log.info('Read new dataset from %s', results_pore_pressure_file_name)
    abaqus_data = mt.read_abaqus(results_pore_pressure_file_name, prev_job_folder)  # Load Abaqus values to ndArray

    # Set parameters for transition (see above)
    mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])
    mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])
    data_in_orig = abaqus_data[3]
    nodes = abaqus_mesh[3]

    # Randomize Abaqus input data
    data_in_rand = rand.get_random_dataset(abaqus_data[3], -0.2, False)

    # Transition
    log.info('Data transition from mesh_in to mesh_out')
    data_rand = mt.mesh_transformation(mesh_in, mesh_out, data_in_rand)

    # Prepare Abaqus input-file (see above)
    log.info('Prepare Abaqus input-file')
    nset_dict = inp.create_nodesets_all(nodes, 'PP')
    bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], data_rand[2]], 8)
    nset_list_dict = inp.create_nodesets_all_list(nset_dict, 'Part_1-1')

    # Write input- and bash-file
    current_input_file = inp.write_inputfile_restart(bc_dict, current_input_file, step_name, current_job_name, current_job_folder, iteration_cnt, False)
    log.info('Write input file: %s', current_input_file)
    current_bash_file = inp.write_bashfile_windows(current_job_folder, current_input_file, current_job_name, abaqus_subroutine_file, prev_job_name)
    log.info('Write windows bash file: %s', current_bash_file)

    # Start simulation
    log.info('Start Simulia Abaqus simulation')
    current_bash_file_win = current_bash_file.replace('/', '\\')  # Is this necessary? Shall be managed elsewhere
    subprocess.call(current_bash_file_win, shell=True, cwd=current_job_folder) # Start simulation in shell
    log.info('End Simulia Abaqus simulation')

    # Remove files from previous simulation
    # Current folder is looped and every file consisting of the previous job name will be deleted
    log.info('Removing files of previous simulation from current subfolder')
    for dirname, dirnames, filenames in os.walk(current_job_folder):
        for filename in filenames:
            if prev_job_name in filename:
                os.remove(current_job_folder + '/' + filename)
                log.info('File removed: %s', filename)
