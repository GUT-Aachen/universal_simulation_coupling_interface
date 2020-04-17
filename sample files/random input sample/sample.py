import numpy
import deprecated_mesh_transition as mt
import deprecated_random_mesh_input as rand
import logging
import sys

import logging
import sys

# #################################################################################
# Initialize the logger: logging class
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='log.txt',
                    filemode='w')

# Define a handler writing INFO messages or higher to sys.stderr
consoleLogger = logging.StreamHandler(sys.stdout)
consoleLogger.setLevel(logging.INFO)
# Set a format which is simpler for console use
format = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
consoleLogger.setFormatter(format)
logging.getLogger('').addHandler(consoleLogger)  # Add handler to root logger

# Load Abaqus and Pace3D Files into arrays
abaqus_data = mt.read_abaqus('abaqus_pore-pressure.csv', '')  # Abaqus data
abaqus_mesh = mt.read_abaqus('abaqus_matrix.csv', '')  # Abaqus mesh original

# Parameters for transition
mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])
mesh_out = numpy.array([abaqus_mesh[0], abaqus_mesh[1]])
data_in_orig = abaqus_data[3]
data_in_rand = rand.get_random_dataset(abaqus_data[3], -0.6, True)

# Transition
data_orig = mt.mesh_transformation(mesh_in, mesh_out, data_in_orig)
data_rand = mt.mesh_transformation(mesh_in, mesh_out, data_in_rand)

# Create random dataset for proof of concept simulation
mt.write_abaqus(numpy.transpose(numpy.array([abaqus_mesh[3], data_rand[2]])), "export_random.csv")
