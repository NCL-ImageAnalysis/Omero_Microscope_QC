
from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.resolution import PSFprofiler
from metroloJ_QC.importer import simpleMetaData;
from metroloJ_QC.report import PSFprofilerReport
from java.lang import Double
from ij import IJ
from ij import WindowManager
import os
import csv

#Gets Image
imp = IJ.getImage()


Opts = QC_Options()
Dialog = MetroloJDialog("PSF profiler report generator", Opts)

Dialog.beadDetectionThreshold = "Otsu"
Dialog.centerDetectionMethodIndex = 1

Dialog.savePdf = True
Dialog.saveSpreadsheet = True
Dialog.saveImages = True

creationInfo=simpleMetaData.getOMECreationInfos(imp, Dialog.debugMode)

print("Running Profiler")
profiler = PSFprofiler(imp, Dialog, "test", [Double.NaN, Double.NaN], creationInfo)
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



filename = imp.getTitle()
date = creationInfo[0] ##This is coming through as just "######"

fwhm_x = profiler.res[0][0]
fwhm_y = profiler.res[0][1]
fwhm_z = profiler.res[0][2]

r2_x = profiler.fittedValues[0][0].R2
r2_y = profiler.fittedValues[0][1].R2
r2_z = profiler.fittedValues[0][2].R2

magnification = "unknown" ##Figure out how to get this using bioformats

for title in WindowManager.getImageTitles():
    if title != imp.getTitle():
        WindowManager.getImage(title).close()

output_folder = "Y:/Image Analysis/Hackathon_2026/"
csv_path = os.path.join(output_folder, "psf_summary_for_QCDB.csv")

fieldnames = [
    "filename", "date", "objective_magnification",
    "fwhm_x", "fwhm_y", "fwhm_z",
    "r2_x", "r2_y", "r2_z"
]

with open(csv_path, "a") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    if f.tell() == 0:
        writer.writeheader()

    writer.writerow({
        "filename": filename,
        "date": date,
        "objective_magnification": magnification,
        "fwhm_x": fwhm_x,
        "fwhm_y": fwhm_y,
        "fwhm_z": fwhm_z,
        "r2_x": r2_x,
        "r2_y": r2_y,
        "r2_z": r2_z
    })

print("CSV saved:", csv_path)
