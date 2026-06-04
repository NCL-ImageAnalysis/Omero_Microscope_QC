Usage
=====

OMERO Setup
-----------
omero_microscope_qc uses OMERO to access images and metadata, as well as for storage of its outputs. 

It expects a structure of:


::

	└── Group
	    └── Project - Microscope
	        └── Dataset - Analysis method
			    └── Individual images

Additional settings for analysis can be attached as key value pairs at any level of this structure, with bottom-most matching key taking precedence. Any class attributes of the MetroloJDialog class that can be cast from text can be added as key value pairs and they will be automatically applied to the analysis. A full list of key value pairs and their functions can be found in :doc:`key_value_pairs`.

Running the script
------------------
Running the script requires an omero config file, the template of which is called `.omero_config <https://github.com/NCL-ImageAnalysis/omero_microscope_qc/blob/main/.omero_config>`_. This requires the hostname of the OMERO server you are connecting to along with a username and password for this server. You also need to provide a path to the top level folder where your version of fiji with MetroloJ_QC is installed.

The script can then be run with:

::

    python -m omero_microscope_qc [temporary_output_path] --config_path [omero_config_path]

Additional arguments can be listed with:

::

    python -m omero_microscope_qc --help