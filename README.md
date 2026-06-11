[![Documentation Status](https://readthedocs.org/projects/omero-microscope-qc/badge/?version=latest)](https://omero-microscope-qc.readthedocs.io/en/latest/)

# Omero Microscope QC

This python module allows for batch processing of images used for quality control of microscopes based upon [QUAREP-LiMi's](https://quarep.org/) recommendations. 

It uses [OMERO](https://www.openmicroscopy.org/omero/) and the ImageJ plugin [MetroloJ_QC](https://github.com/MontpellierRessourcesImagerie/MetroloJ_QC) (run via [pyImageJ](https://github.com/imagej/pyimagej)) to perform resolution, co-registration and stage precision analysis on bead images and a custom script for Z-drive accuracy run on images of a "3D Crossing stairs" pattern on an [Argolight](https://argolight.com/) calibration slide. Images are pulled directly from an OMERO server with results attached to the same images. These attachments can then be loaded into the feets-db microscopy QC database.

## Installation
### System Requirements
Requires an operating system with a GUI interface. Unfortunately due to requirements of MetroloJ_QC omero_microscope_qc cannot be run fully headlessly.

Currently only Windows devices have been tested but it should be compatible with Mac OS and Linux (please let us know if these work for you and we can update our documentation).

### Dependencies
- Python >= 3.10 (3.12 recommended)
- [pyimagej](https://pypi.org/project/pyimagej/)
- [omero-py](https://pypi.org/project/omero-py/)
- [IcePy 3.6](https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html)
- [networkx](https://pypi.org/project/networkx/)
- [pandas](https://pypi.org/project/pandas/)
- [click](https://pypi.org/project/click/)

### Installation with conda/mamba
I would recommend using mamba instead of conda as it is much faster at resolving environments. You can get a lightweight implementation with mamba preinstalled with [miniforge](https://github.com/conda-forge/miniforge).

Create your environment with:

    mamba create -n omero-microscope-qc-env python=3.12 pyimagej openjdk=11

This will create your environments and install pyImageJ and java requirements. For any issues at this stage see pyImageJ's documentation here: https://py.imagej.net/en/latest/index.html

To install omero-py you will need to first install ZeroC IcePy 3.6 python bindings. Details for how to do this can be found on omero-py's GitHub: https://github.com/ome/omero-py

When that is installed you can then install omero-microscope-qc and all remaining requirements.

If you have git installed this can be done with:

    pip install git+https://github.com/NCL-ImageAnalysis/Omero_Microscope_QC.git

Otherwise you can download the repository, navigate to where the folder is extracted and install with

    pip install .

### Fiji/MetroloJ_QC installation
omero_microscope_qc requires a working Fiji installation with MetroloJ_QC installed into Fiji's plugin folder.

You can download Fiji from: https://fiji.sc/ and the MetroloJ_QC jar file from its GitHub repository here: https://github.com/MontpellierRessourcesImagerie/MetroloJ_QC

After Fiji has been unzipped from its archive download the MetroloJ_QC jar file to its plugin folder. Currently this has been tested on MetroloJ_QC v1.3.1.2

### Installation without pyImageJ/MetroloJ
It is possible to install without pyImageJ in order to just use the omero helper functions. pyimagej is only a requirement if you add \[imagej\] to your pip install command e.g.

    pip install .[imagej]

## OMERO Setup
omero-microscope-qc uses OMERO to access images and metadata, as well as for storage of its outputs. 

It expects a structure of:

	└── Group
	    └── Project - Microscope
	        └── Dataset - Analysis method
			    └── Individual images

Additional settings for analysis can be attached as key value pairs at any level of this structure, with bottom-most matching key taking precedence. Any class attributes of the MetroloJDialog class that can be cast from text can be added as key value pairs and they will be automatically applied to the analysis. A full list of key value pairs and their functions can be found in [this document](key_value_pairs.md).	 

## Usage
Running the script requires an omero config file, the template of which is called [.omero_config](https://github.com/NCL-ImageAnalysis/omero_microscope_qc/blob/main/.omero_config). This requires the hostname of the OMERO server you are connecting to along with a username and password for this server. You also need to provide a path to the top level folder where your version of fiji with MetroloJ_QC is installed.

The script can then be run with:

    python -m omero_microscope_qc [temporary_output_path] --config_path [omero_config_path]

Additional arguments can be listed with:

    python -m omero_microscope_qc --help


