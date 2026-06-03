from .metroloJ_access import *
from .omero_objects import *	
from .z_accuracy import *
from .imagej_utils import *

import imagej
import scyjava

# Global variables
# ImageJ instance - None until initialised by calling batch_qc.initialise()
_ij = None
# Dictionary to hold imported Java classes, populated on initialisation
_java = {}
# Dictionary with keys for the name of each java import and the package path as the value. 
# This is used to import the required Java classes on initialisation and store them in the _java dictionary for use in other functions in this module. 
_JAVA_CLASSES = {
	"Double": "java.lang.Double",
	"WindowManager": "ij.WindowManager",
	"Calibration": "ij.measure.Calibration",
	"MetroloJDialog": "metroloJ_QC.setup.MetroloJDialog",
	"QC_Options": "metroloJ_QC.setup.QC_Options",
	"coAlignement": "metroloJ_QC.coalignement.coAlignement",
	"coAlignementReport": "metroloJ_QC.report.coAlignementReport",
	"driftProfiler": "metroloJ_QC.stage.driftProfiler",
	"driftProfilerReport": "metroloJ_QC.report.driftProfilerReport",
	"PSFprofiler": "metroloJ_QC.resolution.PSFprofiler",
	"PSFprofilerReport": "metroloJ_QC.report.PSFprofilerReport",
	"IJ": "ij.IJ",
	"FileSaver": "ij.io.FileSaver",
	"Line": "ij.gui.Line",
	"Overlay": "ij.gui.Overlay",
	"Roi": "ij.gui.Roi",
	"Measurements": "ij.measure.Measurements",
	"ResultsTable": "ij.measure.ResultsTable",
	"ZProjector": "ij.plugin.ZProjector",
	"Analyzer": "ij.plugin.filter.Analyzer",
	"Slicer": "ij.plugin.Slicer",
	"MaximumFinder": "ij.plugin.filter.MaximumFinder"
}

def initialise(*args, memory=None, **kwargs):
	"""Initialise ImageJ and import required Java classes. Must be called before using any other functions in this module.
	Takes arguments used for imagej.init() and an optional memory argument to specify the maximum memory allocation pool for the Java virtual machine (e.g. "4g" for 4 gigabytes). If memory is not specified, the default memory allocation will be used.

	Args:
		memory (str, optional): The maximum memory allocation pool for the Java virtual machine (e.g. "4g" for 4 gigabytes). Defaults to None.
	"""
	global _ij, _java

	if memory is not None:
		scyjava.config.add_option(f"-Xmx{memory}")
	# Initialises ImageJ
	_ij = imagej.init(*args, **kwargs)
	# Imports required Java classes and stores them in the _java dictionary
	_java = {name: scyjava.jimport(class_path) for name, class_path in _JAVA_CLASSES.items()}