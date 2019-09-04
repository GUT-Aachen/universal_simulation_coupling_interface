# NodeData Transition Abaqus <> Pace3D
This python 2.7 compatible function toolbox can be used to perform a data transition from a mesh in [Simulia Abaqus](https://www.3ds.com/de/produkte-und-services/simulia/produkte/abaqus/) to a grid in [Pace3D](https://www.hs-karlsruhe.de/idm/pace3d-software/).

Two data sets are needed:
1. Abaqus data: node_number | x | y | z | values (delimiter: \tab)
1. Pace3D data: x | y | z | values (delimiter: space)

It is possible to convert the data from Abaqus to Pace3D and vice versa. The values will be transferred by using the [`scipy.interpolate.griddata()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) function which uses a qhull. It uses the coordinates from the mesh and the grid to make a liner interpolation to fill the values. If a linear interpolation is not possible (e.g. the coordinates are outside the input hull) the nearest neighbor will be used.

###Functions:
* `read_pace3d` Reads the Pace3d datafile containing at least coordinates (x,y,z). Values if pace3d is the source.
* `read_abaqus` Reads the Abaqus datafile containing at least node numbers, coordinates (x,y,z) and values if Abaqus is the source.
* `mesh_transformation` Function to transform the source data set from the source mesh/grid to the target mesh/grid. Output of the function is the target mesh/grid including the values. 
* `transformation_validation` Used to transform data from source to target and again from target to source mesh/grid. The output of the second transition will be compared to the original data to check the data loss. All three data sets will be visualized.

###Sample:
In the folder `sample files` data files from abaqus and pace3d and a short script that shows the usage are supported.

###Note:
With a little know how those scripts can be used to transform any data between to different grids/meshes, but has been developed just for the case of Abaqus <> Pace3D.