from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.coalignement import coAlignement
from metroloJ_QC.importer import simpleMetaData
from metroloJ_QC.report import coAlignementReport
from java.lang import Double

from ij import IJ

imp = IJ.getImage()
OrigImgName = imp.getTitle()
coords = [Double.NaN, Double.NaN]
output_folder = r"G:\QC\QC_Coreg\Axioimager1"

Opts = QC_Options()

Dialog = MetroloJDialog("Co-registration report generator", Opts) # Needs image open
Dialog.beadDetectionThreshold = "Otsu"
Dialog.centerDetectionMethodIndex = 1

Dialog.savePdf = True
Dialog.saveSpreadsheet = True
Dialog.saveImages = True

creationInfo=simpleMetaData.getOMECreationInfos(Dialog.ip, Dialog.debugMode)

coAlign = coAlignement(imp, Dialog, "test", coords, creationInfo)

coreport = coAlignementReport(imp, Dialog, OrigImgName, coords, creationInfo)
coreport.saveReport(output_folder, "Test_01", None)