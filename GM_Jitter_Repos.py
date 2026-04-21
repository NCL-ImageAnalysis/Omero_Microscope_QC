
from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.stage import driftprofiler
from metroloJ_QC.importer import simpleMetaData;
from metroloJ_QC.report import driftProfilerReport
from java.lang import Double

from ij import IJ
from ij import WindowManager
import os
import csv

#Gets Image
imp = IJ.getImage()
title = imp.getTitle()


Opts = QC_Options()
Dialog = MetroloJDialog("Stage positioning and drift report generator", Opts)

##Don't know which parts of this are important
##Dialog.beadDetectionThreshold = "Otsu"
Dialog.centerDetectionMethodIndex = 2

Dialog.savePdf = True
Dialog.saveSpreadsheet = True
Dialog.saveImages = True

coords = [Double.NaN, Double.NaN]
creationInfo=simpleMetaData.getOMECreationInfos(imp, Dialog.debugMode)

print("Running Profiler")
profiler = driftprofiler(imp, Dialog, title, coords, creationInfo)
print("Profiler executed")


print("Generating Report")
profilerReport = driftProfilerReport(imp, Dialog, title, coords, creationInfo)
print("Report Generated")

print("Saving Report")
output_folder = "Y:/Image Analysis/Hackathon_2026/"  
profilerReport.saveReport(output_folder, "Drift_Profiler_Report", None)
print("Report saved to:", output_folder)
