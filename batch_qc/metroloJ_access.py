import batch_qc

_METHODS = {
	"psf": ("PSF profiler report generator", "PSF-profile"),
	"drift": ("Stage positioning and drift report generator", "Drift-profile"),
	"registration": ("Co-registration report generator", "Registration-profile")
}

_CENTER_DETECTION = {"ellipses": 0, "centroid": 1, "max": 2}

_MICROSCOPE_TYPES = {"WideField": 0, "CLSM": 1, "Spinning Disc Confocal": 2, "Multiphoton": 3}

_ACCEPTED_VALUES = {
	"method": ["psf", "drift", "registration"],
	"thresholding_method": ["Legacy", "Li", "Minimum", "Otsu"],
	"center_dectection_method": ["ellipses", "centroid", "max"],
	"microscope_type": ["WideField", "CLSM", "Spinning Disc Confocal", "Multiphoton"],
}

def check_inputs(key, value):
	if value not in _ACCEPTED_VALUES[key]:
		raise ValueError(f"{key} must be one of {_ACCEPTED_VALUES[key]}")

def initialize_MetroloJDialog(method,
							  image,
							  thresholding_method="Otsu",
							  center_dectection_method="centroid",
							  save_pdf=True,
							  save_csv=True,
							  save_images=True):
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	
	check_inputs("method", method)
	method_string, title_string = _METHODS[method]

	check_inputs("thresholding_method", thresholding_method)
	check_inputs("center_dectection_method", center_dectection_method)
	
	center_integer = _CENTER_DETECTION[center_dectection_method]
	try:
		check_inputs("microscope_type", image.key_value_pairs["microscope_type"])
		microscope_index = _MICROSCOPE_TYPES[image.key_value_pairs["microscope_type"]]
	except KeyError:
		raise KeyError("Microscope type not found in image key value pairs. Please ensure that the image has a key 'microscope_type' with value 'WideField', 'CLSM', 'Spinning Disc Confocal' or 'Multiphoton'")
	
	if microscope_index == 1:  # CLSM
		try:
			pinhole_size = float(image.key_value_pairs["pinhole_size_AU"])
		except KeyError:
			raise KeyError("Pinhole size not found in image key value pairs. Please ensure that the image has a key 'pinhole_size_AU' with the pinhole size in AU as the value.")

	image_plus = image.image_plus
	if image_plus is None:
		image_plus = image.generate_ImagePlus()

	batch_qc._java["WindowManager"].setTempCurrentImage(image_plus)
	Dialog = batch_qc._java["MetroloJDialog"](method_string, batch_qc._java["QC_Options"]())
	Dialog.title = title_string
	Dialog.beadDetectionThreshold = thresholding_method
	Dialog.centerDetectionMethodIndex = center_integer

	Dialog.NA = image.NA
	Dialog.refractiveIndex = image.refractive_index
	Dialog.emWavelengths = [ch.emission_wave for ch in image.channels]
	Dialog.exWavelengths = [ch.excitation_wave for ch in image.channels]

	Dialog.savePdf = save_pdf
	Dialog.saveSpreadsheet = save_csv
	Dialog.saveImages = save_images

	class_fields = [class_obj.getName() for class_obj in Dialog.getClass().getFields()]
	for dict_key in image.key_value_pairs:
		if dict_key in class_fields:
			try:
				setattr(Dialog, dict_key, image.key_value_pairs[dict_key])
			except TypeError:
				try:
					field_type = type(getattr(Dialog, dict_key))
					setattr(Dialog, dict_key, field_type(image.key_value_pairs[dict_key]))
				except ValueError:
					raise TypeError(f"Error: {dict_key} requires input of the type {type(getattr(Dialog, dict_key))}.")
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