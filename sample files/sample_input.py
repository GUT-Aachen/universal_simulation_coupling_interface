import numpy
import mesh_transition as mt
import random_mesh_input as rand
import abaqus_input as inp
import shutil
import os
import subprocess
import logging as log

# Set job name
abaqus_job_name = 'Cube_PP_SubR'
abaqus_input_file_name = 'Cube_PP_SubR.inp'
abaqus_subroutine_file_name = 'subroutine_export.f'
abaqus_mesh_file_name = 'abaqus_matrix.csv'
abaqus_pore_pressure_file_name = 'abaqus_pore-pressure.csv'
log_file_name = abaqus_job_name + '.log'
abaqus_work_path = 'D:\Abaqus_Work_2019\Abaqus-Pace3D-Transition'

number_of_iterations = 40

abaqus_work_path = abaqus_work_path.replace("\\", "/")

abaqus_input_path = abaqus_work_path + '/input'
abaqus_output_path = abaqus_work_path + '/output'
abaqus_input_file = abaqus_input_path + '/' + abaqus_input_file_name
abaqus_subroutine_file = abaqus_input_path + '/' + abaqus_subroutine_file_name

# Initialize the logger
log.basicConfig(level=log.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=abaqus_work_path + '/' + log_file_name,
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = log.StreamHandler()
console.setLevel(log.INFO)
# set a format which is simpler for console use
formatter = log.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
log.getLogger('').addHandler(console)

# Now, define a couple of other loggers which might represent areas in your
# application:
# logger1 = logging.getLogger('myapp.area1')
log.debug('abaqus_work_path: %s', abaqus_work_path)
log.debug('abaqus_job_name: %s', abaqus_job_name)
log.debug('abaqus_input_file_name: %s', abaqus_input_file_name)
log.debug('abaqus_subroutine_file_name: %s', abaqus_subroutine_file_name)
log.debug('abaqus_mesh_file_name: %s', abaqus_mesh_file_name)
log.debug('abaqus_pore_pressure_file_name: %s', abaqus_pore_pressure_file_name)
log.info('Number of iterations: %s', number_of_iterations)


# Clean up process for folder
if os.path.exists(abaqus_output_path):
    log.info('* Cleanup process: Deleting output folder')
    log.info('Folder: ', abaqus_output_path)
    shutil.rmtree(abaqus_output_path)
    log.info()

log.info('Preparing first iterations')

actual_input_file = ''
iteration_cnt = 0
subfolder = '/step_' + str(iteration_cnt)

# Load Abaqus and Pace3D Files into arrays
abaqus_mesh = mt.read_abaqus(abaqus_mesh_file_name, abaqus_input_path)  # Abaqus mesh original
abaqus_data = mt.read_abaqus(abaqus_pore_pressure_file_name, abaqus_input_path)  # Abaqus data

# Parameters for transition
mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])
mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])
data_in_orig = abaqus_data[3]
data_in_rand = rand.get_random_dataset(abaqus_data[3], -0.2, False)

nodes = abaqus_mesh[3]

# Transition
log.info('Data transition from mesh_in to mesh_out')
data_rand = mt.mesh_transformation(mesh_in, mesh_out, data_in_rand)

# Prepare Abaqus input-file
log.info('Prepare Abaqus input-file')
nset_dict = inp.create_nodesets_all(nodes, 'PP')
bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], data_rand[2]], 8)
nset_list_dict = inp.create_nodesets_all_list(nset_dict, 'Part_1-1')

actual_job_name = abaqus_job_name + '_' + str(iteration_cnt)
actual_job_folder = abaqus_output_path + subfolder
actual_input_file = inp.write_inputfile(bc_dict, nset_list_dict, abaqus_input_file, actual_job_name, actual_job_folder)
actual_bash_file = inp.write_bashfile_windows(actual_job_folder, actual_input_file, actual_job_name, abaqus_subroutine_file) # bash file in subfolder

# Start simulation
log.info('Start Simulia Abaqus simulation')
actual_bash_file_win = actual_bash_file.replace('/', '\\')
subprocess.call(actual_bash_file_win, shell=True, cwd=actual_job_folder)
log.info('End Simulia Abaqus simulation')

##################################################
# Next Iteration
for x in range(0, number_of_iterations):
    iteration_cnt += 1
    subfolder = '/step_' + str(iteration_cnt)
    step_name = 'Step_PPChange_' + str(iteration_cnt)
    log.info('Preparing simulation step: %s', step_name)
    prev_job_folder = actual_job_folder
    actual_job_folder = abaqus_output_path + subfolder
    prev_job_name = actual_job_name
    actual_job_name = abaqus_job_name + '_' + str(iteration_cnt)

    # Clean up process for subfolder
    if os.path.exists(actual_job_folder):
        log.info('Cleanup process: Deleting output subfolder (%s)', actual_job_folder)
        shutil.rmtree(actual_job_folder)

    # As a first approach of a completetion check the msg-file should be checked.
    if not os.path.isfile(prev_job_folder + '/' + prev_job_name + '.msg'):
        log.critical('Previous simulation not completed')
        exit()

    # Copy all files into the new directory to restart the previous analysis
    log.info('Copying files from previous simulation to actual subfolder to restart analysis')
    shutil.copytree(prev_job_folder, actual_job_folder)

    # Load Abaqus and Pace3D Files into arrays
    results_mesh_file_name = prev_job_name + '_matrix.csv'
    log.info('Read new mesh from %s', results_mesh_file_name)
    abaqus_mesh = mt.read_abaqus(results_mesh_file_name, prev_job_folder)  # Abaqus mesh original

    results_pore_pressure_file_name = prev_job_name + '_pore-pressure.csv'
    log.info('Read new dataset from %s', results_pore_pressure_file_name)
    abaqus_data = mt.read_abaqus(results_pore_pressure_file_name, prev_job_folder)  # Abaqus data

    # Parameters for transition
    mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])
    mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])
    data_in_orig = abaqus_data[3]
    data_in_rand = rand.get_random_dataset(abaqus_data[3], -0.2, False)

    nodes = abaqus_mesh[3]

    # Transition
    log.info('Data transition from mesh_in to mesh_out')
    data_rand = mt.mesh_transformation(mesh_in, mesh_out, data_in_rand)

    log.info('Prepare Abaqus input-file (restart)')
    nset_dict = inp.create_nodesets_all(nodes, 'PP')
    bc_dict = inp.create_boundary_condition(nset_dict, [abaqus_mesh[3], data_rand[2]], 8)
    nset_list_dict = inp.create_nodesets_all_list(nset_dict, 'Part_1-1')

    actual_input_file = inp.write_inputfile_restart(bc_dict, actual_input_file, step_name, actual_job_name, actual_job_folder, iteration_cnt, False)
    actual_bash_file = inp.write_bashfile_windows(actual_job_folder, actual_input_file, actual_job_name, abaqus_subroutine_file, prev_job_name)

    # Start simulation
    log.info('Start Simulia Abaqus simulation')
    actual_bash_file_win = actual_bash_file.replace('/', '\\')
    subprocess.call(actual_bash_file_win, shell=True, cwd=actual_job_folder)
    log.info('End Simulia Abaqus simulation')

    # Remove files from previous simulation
    log.info('Removing files of previous simulation from actual subfolder')
    for dirname, dirnames, filenames in os.walk(actual_job_folder):
        for filename in filenames:
            if prev_job_name in filename:
                os.remove(actual_job_folder + '/' + filename)
                log.info('File removed: %s', filename)
