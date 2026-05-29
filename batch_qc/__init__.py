from .metroloJ_access import *
from .omero_images import *	
from .z_accuracy import *
from .imagej_utils import *
# from .crop_multibeads import *

import imagej
import scyjava

_ij = None
_java = {}

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
	"Math": "java.lang.Math",
	"IJ": "ij.IJ",
	"FileSaver": "ij.io.FileSaver",
	"Line": "ij.gui.Line",
	"Overlay": "ij.gui.Overlay",
	"Roi": "ij.gui.Roi",
	"Measurements": "ij.measure.Measurements",
	"ResultsTable": "ij.measure.ResultsTable",
	"ZProjector": "ij.plugin.ZProjector",
	"Analyzer": "ij.plugin.filter.Analyzer",
	"NoSuchFileException": "java.nio.file.NoSuchFileException",
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
	_ij = imagej.init(*args, **kwargs)
	_java = {name: scyjava.jimport(class_path) for name, class_path in _JAVA_CLASSES.items()}