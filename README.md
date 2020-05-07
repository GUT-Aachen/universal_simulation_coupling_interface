# Universal Simulation Coupling Interface

![License: GNU](https://img.shields.io/github/license/froido/simulation_coupling_interface?style=flat-square)
![License: GNU](https://img.shields.io/github/release-date/froido/simulation_coupling_interface?style=flat-square)
![License: GNU](https://img.shields.io/github/v/release/froido/simulation_coupling_interface?style=flat-square)
![DOI](https://img.shields.io/static/v1?label=DOI&message=DOIDOIDOI&color=blue&style=flat-square)

> This framework can be used to partially couple two or more simulations. 
  This interface manages the workflow of the simulation coupling, as it exchanges data between grids or meshes at each iteration and modifies the data to fit manufacturer specifications. 
  At the moment only two engines (Simulia Abaqus and Pace3D) are included, but thanks to a modular programming new engines can be easily added. The communication between the `USCI (Universal Simulation Coupling Interface)` and the engine is established via CLI (command line interface).
  The data exchange between the interface and the engine is currently handled via ASCII files, but differs depending on the engine.

---

## Features

---

## Requirements
 
 - Python 3.7 or higher
 - Python package dependencies: [![NumPy](https://img.shields.io/static/v1?label=numpy&message=NumPy&color=blue&style=flat-square&logo=github)](https://github.com/numpy/numpy)
[![SciPy](https://img.shields.io/static/v1?label=scipy&message=SciPy&color=blue&style=flat-square&logo=github)](https://github.com/scipy/scipy)
[![matplotlib](https://img.shields.io/static/v1?label=matplotlib&message=matplotlib&color=blue&style=flat-square&logo=github)](https://github.com/matplotlib/matplotlib)

 - At least two different simulation software with a known command line interface
 - Developement of an engine to tell USCI how to communicate and exchange data with simulation software
 
---

## Setup
 - Check for python package dependencies
 - Download latest release of USCI to your local machine
 - Construct you own simulation workflow or try one of the [samples](samples)
  
---

## Usage (pending)

---

## Support

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
