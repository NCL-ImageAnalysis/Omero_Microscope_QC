from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.resolution import PSFprofiler
from java.lang import Double

from ij import IJ

Opts = QC_Options()
Dialog = MetroloJDialog("PSF profiler report generator", Opts) # Needs image open

imp = IJ.getImage()

profiler = PSFprofiler(imp, Dialog, "test", [Double.NaN, Double.NaN], [""])