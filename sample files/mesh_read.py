import csv
import numpy
import sys

from scipy.interpolate import griddata  # used for mesh transformation
import matplotlib.pyplot as plt  # used for visualisation of transformation validation

#####################################################################################################################


def read_pace3d(filename):
	""" Function to read an dat-file-export from the Software Pace3D from IDM HS Karlsruhe """
	function_name = 'read_pace3d'
	print_pre_str = '\t' + function_name + ' >> '
	print('* Start function: ', function_name)
	print(print_pre_str, 'Load Pace3D-File: ', filename)

	try:
		with open(filename) as csvfile:
			read_csv = csv.reader(csvfile, delimiter=' ')

			x = []
			y = []
			z = []
			data_set = []

			for row in read_csv:
				try:
					x.append(float(row[0]))
					y.append(float(row[1]))
					z.append(float(row[2]))
					data_set.append(float(row[3]))

				except Exception as err:
					print(print_pre_str, 'Empty row found and ignored. Continue... [', str(err), ']')

			print(print_pre_str, len(data_set), ' rows read successfully')

			return numpy.array([x, y, z, data_set])
	except Exception as err:
		print(print_pre_str, 'File --', filename, '-- could not be read correctly')
		print('* ERROR in function: ', function_name, ' [', str(err), ']')
		print()
		return 0

	finally:
		print(print_pre_str, 'exiting function')
		print()


#####################################################################################################################


def read_abaqus(filename):
	""" Function to read an csv-file-export from the Software Simulia Abaqus """
	function_name = 'read_abaqus'
	print_pre_str = '\t' + function_name + ' >> '
	print('* Start function: ', function_name)
	print(print_pre_str, 'Load Abaqus-Mesh-File: ', filename)

	try:
		with open(filename) as csvfile:
			read_csv = csv.reader(csvfile, delimiter='\t')

			x = []
			y = []
			z = []
			data_set = []

			for row in read_csv:
				try:
					x.append(float(row[1]))
					y.append(float(row[2]))
					z.append(float(row[3]))
					data_set.append(float(row[4]))

				except Exception as err:
					print(print_pre_str, 'Empty row found and ignored. Continue... [', str(err), ']')

			print(print_pre_str, len(data_set), ' rows read successfully')

			return numpy.array([x, y, z, data_set])

	except Exception as err:
		print(print_pre_str, 'File --', filename, '-- could not be read correctly')
		print('* ERROR in function: ', function_name, ' [', str(err), ']')
		print()
		return 0

	finally:
		print(print_pre_str, 'exiting function')
		print()


#####################################################################################################################
#####################################################################################################################


def transformation_validation(input_mesh, output_mesh, input_data):
	""" Validating the method of transferring data from one mesh to another We have two different meshes (one is
	coarser then the other). The information within the mesh is transferred from one mesh to the other and backwards.
	The transformation form a finer to a coarser mesh includes data loss. The amount of loss is influenced by the
	difference of the mesh resolution. The following code transforms the data from mesh 'input' (maybe finer) to mesh
	'output' (maybe coarser) back to mesh 'input_re'. The data loss will be shown by checking the difference 'input -
	input_re'. As a result we get a min/max-value, mean and standard deviation to check whether the data loss is
	acceptable. """

	function_name = 'transformation_validation'
	print_pre_str = '\t' + function_name + ' >> '
	print('* Start function: ', function_name)
	print(print_pre_str, '* Transforming validation will be started')

	try:
		# Data transformation from input_mesh to output_mesh
		output = mesh_transformation(input_mesh, output_mesh, input_data)

		output_data = []
		if numpy.size(output, 0) == 3:
			output_data = output[2]
		elif numpy.size(output, 0) == 4:
			output_data = output[3]

		# Data transformation from output_mesh back to input_mesh
		input_re = mesh_transformation(output_mesh, input_mesh, output_data)

		input_re_data = []
		if numpy.size(input_re, 0) == 3:
			input_re_data = input_re[2]
		elif numpy.size(input_re, 0) == 4:
			input_re_data = input_re[3]

		print(print_pre_str, )
		print(print_pre_str, '* Array output: input after retransformation')
		print(print_pre_str, input_re_data)
		print(print_pre_str, )

		# Calculating mean and standard deviation
		# For statistics the absolute values of fine_new_data are used
		diff = numpy.absolute(input_data - input_re_data)

		print(print_pre_str, '* Statistics')
		print(print_pre_str, '\t Nodes fine: \t\t', str(input_mesh[0].size))
		print(print_pre_str, '\t Coarse fine: \t\t', str(output_mesh[0].size))
		print(print_pre_str, )
		print(print_pre_str, '\t * After transformation:')
		print(print_pre_str, '\t\t NaN-Values: \t\t', str(sum(numpy.isnan(input_re_data))))
		print(print_pre_str, '\t\t Mean: \t\t\t\t', str(numpy.nanmean(diff)))
		print(print_pre_str, '\t\t Std. Deviation: \t', str(numpy.nanstd(diff)))
		print(print_pre_str, )

		# Generating the visual output
		print(print_pre_str, '* Plotting datasets to visually comparison')
		mpl_fig = plt.figure()
		ax1 = mpl_fig.add_subplot(221)
		cb1 = ax1.scatter(input_mesh[0], input_mesh[1], s=1, c=input_data, cmap=plt.cm.get_cmap('RdBu'))
		plt.colorbar(cb1, ax=ax1)
		ax1.set_title('input (original)')

		ax2 = mpl_fig.add_subplot(222)
		cb2 = ax2.scatter(output_mesh[0], output_mesh[1], s=1, c=output_data, cmap=plt.cm.get_cmap('RdBu'))
		plt.colorbar(cb2, ax=ax2)
		ax2.set_title('output')

		ax3 = mpl_fig.add_subplot(223)
		cb3 = ax3.scatter(input_mesh[0], input_mesh[1], s=1, c=input_re_data, cmap=plt.cm.get_cmap('RdBu'))
		plt.colorbar(cb3, ax=ax3)
		ax3.set_title('input (retransformation)')

		# function to show the plot
		plt.show()
	except Exception as err:
		sys.exit(print_pre_str + 'ERROR: ' + str(err) + '\nExecution aborted!')

	finally:
		print(print_pre_str, 'exiting function')
		print()

#####################################################################################################################


def mesh_transformation(input_mesh, output_mesh, input_data):
	""" Data transformation from input_mesh to output_mesh using input_data. For the transformation the
	scipy.interpolate.griddata method will be used with two different options. First a linear interpolation.
	Potentially upcomming NaN-values within the linear interpolation will be filled with data from a nearest-neighbor
	interpolation. Output is an array containing output_mesh and output_data. """

	function_name = 'mesh_transformation'
	print_pre_str = '\t' + function_name + ' >> '
	print('* Start function: ', function_name)
	print(print_pre_str, '* Transforming information from input mesh to output mesh')

	try:
		# Check size of input_mesh
		if numpy.size(input_mesh, 0) == 2:
			print(print_pre_str, 'Input is a 2D-mesh')
			dimensions = 2
			input_mesh_list = (input_mesh[0], input_mesh[1])

		elif numpy.size(input_mesh, 0) == 3:
				print(print_pre_str, 'Input is a 3D-mesh')
				dimensions = 3
				input_mesh_list = (input_mesh[0], input_mesh[1], input_mesh[2])

		else:
			raise Exception('Size of input_mesh_array does not fit (x,y,z). z is optional')

		# Check size of input_mesh
		if numpy.size(output_mesh, 0) == 2 and dimensions == 2:
			print(print_pre_str, 'Output is a 2D-mesh')
			output_mesh_list = (output_mesh[0], output_mesh[1])

		elif numpy.size(output_mesh, 0) == 3 and dimensions == 3:
			print(print_pre_str, 'Output is a 3D-mesh')
			output_mesh_list = (output_mesh[0], output_mesh[1], output_mesh[2])

		else:
			raise Exception('Size of output_mesh_array (' + str(numpy.size(output_mesh, 0)) +
							')does not fit (x,y,z); z is optional. Both meshes (input and output) need to have the same size 2D or 3D.')

		# Check if size of input_mesh and input_data are equal
		if numpy.size(input_data) != numpy.size(input_mesh, 1):
			raise Exception('Size of data_array (data: ' + str(numpy.size(input_data)) + ' mesh: '
							+ str(numpy.size(input_mesh, 1))
							+ ') does not fit. It should contain just one row and the same length as input_mesh.')

		# Choose whether a 2d or 3d interpolation has to be done In the first place a linear interpolation will be
		# done. By a transformation from coarse to fine, we are having problems with regions, that are not able to be
		# filled with a linear interpolation (getting NaN). For example, when the fine mesh has outer boundaries/lines
		# which are not "surrounded" by coarse-mesh. Those points need a nearest neighbor transformation.
		# 1. linear interpolation
		# 2. nearest neighbor
		# 3. fill all NaN-gabs in 1. with 2.
		print(print_pre_str, 'Calculation interpolation in 2D')

		linear = griddata(input_mesh_list, input_data, output_mesh_list, 'linear')
		nearest = griddata(input_mesh_list, input_data, output_mesh_list, 'nearest')

		# Search NaN in linear and replace by nearest
		for x in range(len(linear)):
			if numpy.isnan(linear[x]):
				linear[x] = nearest[x]
				# print(print_pre_str, str(linear[x]), ' is nearest neighbor instead of NaN')

		# Create return: array including mesh and data
		output_data = linear
		output_array = numpy.append(output_mesh, [output_data], axis=0)

		# Print some statistics
		print(print_pre_str, '* Statistics')
		print(print_pre_str, '\t Intput Nodes: \t', str(input_mesh[0].size))
		print(print_pre_str, '\t Output Nodes: \t', str(input_mesh[0].size))
		print(print_pre_str, '\t NaN-Values: \t', str(sum(numpy.isnan(output_data))))

		return output_array

	except Exception as err:
		sys.exit(print_pre_str + 'ERROR: ' + str(err) + '\nExecution aborted!')

	finally:
		print(print_pre_str, 'exiting function')
		print()

#####################################################################################################################


coarse = read_abaqus('abaqus_voidRatio.csv')
fine = read_pace3d('pace3d_pressure_2D_sample.dat')

print(type(fine[0]))

mesh_in = numpy.array([fine[0], fine[1]])
mesh_out = numpy.array([coarse[0], coarse[1]])
data_in = fine[3]

data = mesh_transformation(mesh_in, mesh_out, data_in)
print(data)
transformation_validation([fine[0], fine[1]], [coarse[0], coarse[1]], fine[3])
