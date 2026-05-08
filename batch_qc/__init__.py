from metroloJ_access import *
from omero_images import *
from z_accuracy import *

import scyjava

_ij = None
_java = {}

_JAVA_CLASSES = {
	"Double": "java.lang.Double",
	"WindowManager": "ij.WindowManager",
	"Calibration": "ij.measure.Calibration",
	"MetroloJDialog": "metroloJ_QC.setup.MetroloJDialog",
	"QC_Options": "metroloJ_QC.setup.QC_Options",
	"simpleMetaData": "metroloJ_QC.importer.simpleMetaData",
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
	"Analyzer": "ij.plugin.filter.Analyzer"
}

def initialise(ij_instance):
	global _ij, _java

	_ij = ij_instance
	_java = {name: scyjava.jimport(class_path) for name, class_path in _JAVA_CLASSES.items()}