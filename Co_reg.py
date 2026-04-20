from metroloJ_QC.setup import MetroloJDialog, QC_Options
from metroloJ_QC.coalignment import coAlignment
from metroloJ_QC.importer import simpleMetaData
from java.lang import Double

from ij import IJ

Opts = QC_Options()

Dialog = MetroloJDialog("Co-registration report generator", Opts) # Needs image open
Dialog.beadDetectionThreshold = "Otsu"
Dialog.centerDetectionMethodIndex = 1

imp = IJ.getImage()

creationInfo=simpleMetaData.getOMECreationInfos(Dialog.ip, Dialog.debugMode)

coAlign = coAlignment(imp, Dialog, "test", [Double.NaN, Double.NaN], creationInfo)