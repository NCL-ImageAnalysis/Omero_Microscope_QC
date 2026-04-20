
from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.resolution import PSFprofiler
from metroloJ_QC.importer import simpleMetaData;
from metroloJ_QC.report import PSFprofilerReport
from java.lang import Double
from ij import IJ

#Gets Image
imp = IJ.getImage()


Opts = QC_Options()
Dialog = MetroloJDialog("PSF profiler report generator", Opts) # Needs image open

Dialog.beadDetectionThreshold = "Otsu"
Dialog.centerDetectionMethodIndex = 1

Dialog.savePdf = True
Dialog.saveSpreadsheet = True
Dialog.saveImages = True

creationInfo=simpleMetaData.getOMECreationInfos(imp, Dialog.debugMode) #why dialog.ip instead of imp??

print("Running Profiler")
profiler = PSFprofiler(imp, Dialog, "test", [Double.NaN, Double.NaN], creationInfo)
##profiler.run()
print("Profiler executed")


##imp = IJ.getImage()
OrigImgName = imp.getTitle()
coords = [Double.NaN, Double.NaN]
creationInfo = simpleMetaData.getOMECreationInfos(imp, Dialog.debugMode)

print("Generating Report")
profilerReport = PSFprofilerReport(imp, Dialog, OrigImgName, coords, creationInfo)
print("Report Generated")

print("Saving Report")
output_folder = "Y:/Image Analysis/Hackathon_2026/"  
profilerReport.saveReport(output_folder, "Test_01", None)
print("Report saved to:", output_folder)



