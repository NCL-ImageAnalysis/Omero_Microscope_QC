import scyjava

def initialize_MetroloJDialog(method,
							  image,
							  thresholding_method="Otsu",
							  center_dectection_method="centroid",
							  save_pdf=False,
							  save_csv=False,
							  save_images=False):
	if method == "psf":
		method_string = "PSF profiler report generator"
	elif method == "drift":
		method_string = "Stage positioning and drift report generator"
	elif method == "registration":
		method_string = "Co-registration report generator"
	else:
		raise ValueError("Method must be one of 'psf', 'drift' or 'registration'")

	if thresholding_method not in ["Legacy", "Li", "Minimum", "Otsu"]:
		raise ValueError("Thresholding method must be one of 'Legacy', 'Li', 'Minimum', or 'Otsu'")
	
	if center_dectection_method == "ellipses":
		center_integer = 0
	elif center_dectection_method == "centroid":
		center_integer = 1
	elif center_dectection_method == "max":
		center_integer = 2
	else:
		raise ValueError("Center detection method must be one of 'ellipses', 'centroid', or 'max'")
	
	image_plus = image.generate_ImagePlus()

	WindowManager = scyjava.jimport("ij.WindowManager")
	MetroloJDialog = scyjava.jimport("metroloJ_QC.setup.MetroloJDialog")
	QC_Options = scyjava.jimport("metroloJ_QC.setup.QC_Options")

	WindowManager.setTempCurrentImage(image_plus)
	Dialog = MetroloJDialog(method_string, QC_Options())
	Dialog.beadDetectionThreshold = thresholding_method
	Dialog.centerDetectionMethodIndex = center_integer

	Dialog.savePdf = save_pdf
	Dialog.saveSpreadsheet = save_csv
	Dialog.saveImages = save_images

	Dialog.NA = image.NA
	Dialog.refractiveIndex = image.refractive_index
	Dialog.emWavelengths = [ch.emission_wave for ch in image.channels]
	Dialog.exWavelengths = [ch.excitation_wave for ch in image.channels]

	return Dialog

def execute_MetroloJ_process(Dialog, report_dir, report_name):
	simpleMetaData = scyjava.jimport("metroloJ_QC.importer.simpleMetaData")
	Double = scyjava.jimport("java.lang.Double")
	
	image = Dialog.ip
	image_title = image.getTitle()
	creationInfo = simpleMetaData.getOMECreationInfos(image, Dialog.debugMode)
	coords = [Double.NaN, Double.NaN]
	
	if Dialog.reportType == "pp":
		PSFprofiler = scyjava.jimport("metroloJ_QC.resolution.PSFprofiler")
		PSFprofilerReport = scyjava.jimport("metroloJ_QC.report.PSFprofilerReport")
		execution_instance = PSFprofiler(image, Dialog, image_title, coords, creationInfo)
		report_instance = PSFprofilerReport(image, Dialog, image_title, coords, creationInfo)
	elif Dialog.reportType == "pos":
		driftProfiler = scyjava.jimport("metroloJ_QC.stage.driftProfiler")
		driftProfilerReport = scyjava.jimport("metroloJ_QC.report.driftProfilerReport")
		execution_instance = driftProfiler(image, Dialog, image_title, coords, creationInfo)
		report_instance = driftProfilerReport(image, Dialog, image_title, coords, creationInfo)
	elif Dialog.reportType == "coa":
		coAlignement = scyjava.jimport("metroloJ_QC.coalignement.coAlignement")
		coAlignementReport = scyjava.jimport("metroloJ_QC.report.coAlignementReport")
		execution_instance = coAlignement(image, Dialog, image_title, coords, creationInfo)
		report_instance = coAlignementReport(image, Dialog, image_title, coords, creationInfo)
	else:
		raise ValueError("Report types supported are PSF profiler, stage positioning and drift and co-registration")
	
	report_instance.saveReport(report_dir, report_name, None)
	return execution_instance