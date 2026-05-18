import batch_qc

_METROLOJ_DEFAULTS = {
	
}



_ACCEPTED_VALUES = {
	"method": ["psf", "drift", "registration"],
	"thresholding_method": ["Legacy", "Li", "Minimum", "Otsu"],
	"center_dectection_method": ["ellipses", "centroid", "max"],
	"microscope_type": ["WideField", "CLSM", "Spinning Disc Confocal", "Multiphoton"],
	"pinhole_size_AU": float,
	"save_pdf": bool,
	"save_csv": bool,
	"save_images": bool,
	"multiple_beads": bool,
	"bead_channel": int,
	"bead_size_um": float,
	"crop_factor": float,
	"min_distance_to_top_and_bottom_um": float,
	"reject_doublets": bool,
	"bead_prominence": float,
	"inner_annulus_edge_distance_to_bead_um": float,
	"annulus_thickness_um": float,
	"apply_tolerance": bool,
	"coal_ratio_tolerance": float,
	"XY_ratio_tolerance": float,
	"Z_ratio_tolerance": float,
	"uniformity_tolerance": float,
	"cent_acc_tolerance": float,
	"max_gap_length": int,
	"use_resolution_thresholds": bool,



}

def initialize_MetroloJDialog(method,
							  image,
							  thresholding_method="Otsu",
							  center_dectection_method="centroid"):
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	if method == "psf":
		method_string = "PSF profiler report generator"
		title_string = "PSF-profile"
	elif method == "drift":
		method_string = "Stage positioning and drift report generator"
		title_string = "Drift-profile"
	elif method == "registration":
		method_string = "Co-registration report generator"
		title_string = "Registration-profile"
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

	batch_qc._java["WindowManager"].setTempCurrentImage(image_plus)
	Dialog = batch_qc._java["MetroloJDialog"](method_string, batch_qc._java["QC_Options"]())
	Dialog.title = title_string
	Dialog.beadDetectionThreshold = thresholding_method
	Dialog.centerDetectionMethodIndex = center_integer

	Dialog.savePdf = save_pdf
	Dialog.saveSpreadsheet = save_csv
	Dialog.saveImages = save_images

	Dialog.NA = image.NA
	Dialog.refractiveIndex = image.refractive_index
	Dialog.emWavelengths = [ch.emission_wave for ch in image.channels]
	Dialog.exWavelengths = [ch.excitation_wave for ch in image.channels]

	try:
		microscope_type = image.key_value_pairs["microscope_type"]
		if microscope_type == "WideField":
			Dialog.microType = 0
		elif microscope_type == "CLSM":
			Dialog.microType = 1
		elif microscope_type == "Spinning Disc Confocal":
			Dialog.microType = 2
		elif microscope_type == "Multiphoton":
			Dialog.microType = 3
		else:
			raise ValueError("Microscope type must be one of 'WideField', 'CLSM', 'Spinning Disc Confocal' or 'Multiphoton'")
	except KeyError:
		raise KeyError("Microscope type not found in image key value pairs. Please ensure that the image has a key 'microscope_type' with value 'WideField', 'CLSM', 'Spinning Disc Confocal' or 'Multiphoton'")
	
	if microscope_type == "CLSM":
		try:
			Dialog.pinhole = float(image.key_value_pairs["pinhole_size_AU"])
		except KeyError:
			raise KeyError("Pinhole size not found in image key value pairs. Please ensure that the image has a key 'pinhole_size_AU' with the pinhole size in AU as the value.")

	return Dialog

def execute_MetroloJ_process(Dialog, report_dir, report_name):
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	image = Dialog.ip
	image_title = image.getTitle()
	creationInfo = batch_qc._java["simpleMetaData"].getOMECreationInfos(image, Dialog.debugMode)
	coords = [batch_qc._java["Double"].NaN, batch_qc._java["Double"].NaN]
	
	if Dialog.reportType == "pp":
		execution_instance = batch_qc._java["PSFprofiler"](image, Dialog, image_title, coords, creationInfo)
		report_instance = batch_qc._java["PSFprofilerReport"](image, Dialog, image_title, coords, creationInfo)
	elif Dialog.reportType == "pos":
		execution_instance = batch_qc._java["driftProfiler"](image, Dialog, image_title, coords, creationInfo)
		report_instance = batch_qc._java["driftProfilerReport"](image, Dialog, image_title, coords, creationInfo)
	elif Dialog.reportType == "coa":
		execution_instance = batch_qc._java["coAlignement"](image, Dialog, image_title, coords, creationInfo)
		report_instance = batch_qc._java["coAlignementReport"](image, Dialog, image_title, coords, creationInfo)
	else:
		raise ValueError("Report types supported are PSF profiler, stage positioning and drift and co-registration")
	
	report_instance.saveReport(report_dir, report_name, None)
	return execution_instance