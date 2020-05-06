# Universal Simulation Coupling Interface

![License: GNU](https://img.shields.io/github/license/froido/simulation_coupling_interface?style=flat-square)
![License: GNU](https://img.shields.io/github/release-date/froido/simulation_coupling_interface?style=flat-square)
![License: GNU](https://img.shields.io/github/v/release/froido/simulation_coupling_interface?style=flat-square)
![DOI](https://img.shields.io/static/v1?label=DOI&message=DOIDOIDOI&color=blue&style=flat-square)

> This framework can be used to partially couple two or more simulations. This interface manages the workflow of the simulation coupling, as it exchanges data between grids or meshes at each iteration and modifies the data to fit manufacturer specifications. At the moment only two engines (Simulia Abaqus and Pace3D) are included, but thanks to a modular programming new engines can be easily added. The communication between the `Universal Simulation Coupling Interface` and the engine is established via CLI (command line interface). The data exchange between the interface and the engine is currently handled via ASCII files, but differs depending on the engine.

---

## Features (pending)

---

## Requirements (pending)
 
 - Python 3.7 or higher
 - Command line interface to communicate with the simulation software
 - Developement of an engine to tell the Interface how to communicate and exchange data
 
---

## Setup (pending)
  - Download latest release of Universal Simulation Coupling Interface to your local machine
  
---

## Usage (pending)

---

## Support (pending)

Reach out to me at one of the following places!

- Website at <a href="http://www.geotechnik.rwth-aachen.de/index.php?section=Biebricher_en" target="_blank">`www.geotechnik.rwth-aachen.de`</a>

---

## License

![License: GNU](https://img.shields.io/github/license/froido/simulation_coupling_interface?style=flat-square)
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details

---

## Thanks

[![NumPy](https://img.shields.io/static/v1?label=numpy&message=NumPy&color=blue&style=flat-square&logo=github)](https://github.com/numpy/numpy)
[![SciPy](https://img.shields.io/static/v1?label=scipy&message=SciPy&color=blue&style=flat-square&logo=github)](https://github.com/scipy/scipy)
[![matplotlib](https://img.shields.io/static/v1?label=matplotlib&message=matplotlib&color=blue&style=flat-square&logo=github)](https://github.com/matplotlib/matplotlib)

---
---
---

## NodeData Transition Abaqus <> Pace3D
This python 2.7 compatible function toolbox can be used to perform a data transition from a mesh in [Simulia Abaqus](https://www.3ds.com/de/produkte-und-services/simulia/produkte/abaqus/) to a grid in [Pace3D](https://www.hs-karlsruhe.de/idm/pace3d-software/).

Two data sets are needed:
1. Abaqus data: node_number | x | y | z | values (delimiter: \tab)
1. Pace3D data: x | y | z | values (delimiter: space)

**Important: Both node_sets need to have the same point or origin!**

It is possible to convert the data from Abaqus to Pace3D and vice versa. The values will be transferred by using the [`scipy.interpolate.griddata()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) function which uses a qhull. It uses the coordinates from the mesh and the grid to make a liner interpolation to fill the values. If a linear interpolation is not possible (e.g. the coordinates are outside the input hull) the nearest neighbor will be used.

Functions:
-----
* `read_pace3d` Reads the Pace3d datafile containing at least coordinates (x,y,z). Values if pace3d is the source.
* `read_abaqus` Reads the Abaqus datafile containing at least node numbers, coordinates (x,y,z) and values if Abaqus is the source.
* `mesh_transformation` Function to transform the source data set from the source mesh/grid to the target mesh/grid. Output of the function is the target mesh/grid including the values. 
* `transformation_validation` Used to transform data from source to target and again from target to source mesh/grid. The output of the second transition will be compared to the original data to check the data loss. All three data sets will be visualized.

Sample:
-----
In the folder `sample files` data files from abaqus and pace3d and a short script that shows the usage are supported.

Note:
-----
With a little know how those scripts can be used to transform any data between to different grids/meshes, but has been developed just for the case of Abaqus <> Pace3D.
