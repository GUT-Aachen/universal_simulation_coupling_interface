import numpy
import mesh_transition as mt
import random_mesh_input as rand

# Load Abaqus and Pace3D Files into arrays
abaqus_data = mt.read_abaqus('abaqus_void-ratio.csv', '')  # Abaqus mesh original
pace3d_data = mt.read_pace3d('pace3d_pressure_2D_sample.dat', '')  # Pace3D dataset

# Parameters for transition
mesh_in = numpy.array([abaqus_data[0], abaqus_data[1]])
mesh_out = numpy.array([pace3d_data[0], pace3d_data[1]])
data_in = abaqus_data[3]

# Transferring data from Abaqus mesh to Pace3d grid and export to csv
data = mt.mesh_transformation(mesh_in, mesh_out, data_in)
mt.write_abaqus(numpy.transpose(data), "export_data.csv")
mt.write_pace3D(numpy.transpose(data), "export_data_pace3D.csv")

# Transferring data from Abaqus mesh to Pace3d grid and backwards to validate the progress and to check the data loss
mt.transformation_validation(mesh_in, mesh_out, data_in)

