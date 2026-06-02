import batch_qc

# Global variables--------------------------------------------------------------------------------------------v
# Dictionary to hold method strings and return strings for MetroloJDialog initialisation
_METHODS = {
	"psf": ("PSF profiler report generator", "PSF-profile"),
	"drift": ("Stage positioning and drift report generator", "Drift-profile"),
	"registration": ("Co-registration report generator", "Registration-profile")}

# Dictionary to hold center detection method strings and their corresponding integer values
_CENTER_DETECTION = {"ellipses": 0, "centroid": 1, "max": 2}

# Dictionary to hold microscope type strings and their corresponding integer values
_MICROSCOPE_TYPES = {"WideField": 0, "CLSM": 1, "Spinning Disc Confocal": 2, "Multiphoton": 3}

# Dictionary to hold accepted values for different parameters in the MetroloJDialog initialisation
_ACCEPTED_VALUES = {
	"method": ["psf", "drift", "registration"],
	"thresholding_method": ["Legacy", "Li", "Minimum", "Otsu"],
	"center_dectection_method": ["ellipses", "centroid", "max"],
	"microscope_type": ["WideField", "CLSM", "Spinning Disc Confocal", "Multiphoton"]}
# Global variables--------------------------------------------------------------------------------------------^

def check_inputs(key, value):
	"""Helper function that checks that input values for different parameters in the MetroloJDialog initialisation are valid and raises an error if not.

	Args:
		key (str): The parameter name
		value (str): The parameter value

	Raises:
		ValueError: Raised if the value is not valid for the given parameter
	"""
	if value not in _ACCEPTED_VALUES[key]:
		raise ValueError(f"{key} must be one of {_ACCEPTED_VALUES[key]}")

def initialize_MetroloJDialog(method,
							  image,
							  thresholding_method="Otsu",
							  center_dectection_method="centroid",
							  save_pdf=True,
							  save_csv=True,
							  save_images=True):
	"""Initialises a MetroloJDialog with the given parameters and returns the dialog instance.

	Args:
		method (str): Method string for the type of MetroloJDialog to be initialised. Must be one of "psf", "drift" or "registration"
		image (batch_qc.omero_objects.ImageObject): ImageObject to be analysed by the MetroloJDialog. Must have key value pairs for "microscope_type" and if microscope type is CLSM, "pinhole_size_AU"
		thresholding_method (str, optional): Thresholding method used by metroloJ. Must be one of "Legacy", "Li", "Minimum", "Otsu". Defaults to "Otsu".
		center_dectection_method (str, optional): Center detection method used by metroloJ. Must be one of "ellipses", "centroid", "max". Defaults to "centroid".
		save_pdf (bool, optional): Whether to save the analysis results as a PDF. Defaults to True.
		save_csv (bool, optional): Whether to save the analysis results as a CSV file. Defaults to True.
		save_images (bool, optional): Whether to save the analysed images. Defaults to True.

	Raises:
		RuntimeError: Raised if ImageJ has not been initialised.
		KeyError: Raised if the microscope type or pinhole size is not found in the image key value pairs.
		ValueError: Raised if the image does not meet the requirements for the specified method or incorrect inputs passed to function parameters.
		TypeError: Raised if key value pairs used for MetroloJDialog attributes are of the wrong type and cannot be cast to the required type.

	Returns:
		metroloJ_QC.setup.MetroloJDialog: The initialised MetroloJDialog instance
	"""
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	
	# Input checks---------------------------------------------------------------------------------------------------------------------------v
	check_inputs("method", method)
	method_string, title_string = _METHODS[method]
	check_inputs("thresholding_method", thresholding_method)
	check_inputs("center_dectection_method", center_dectection_method)	
	center_integer = _CENTER_DETECTION[center_dectection_method]
	try:
		check_inputs("microscope_type", image.key_value_pairs["microscope_type"])
		microscope_index = _MICROSCOPE_TYPES[image.key_value_pairs["microscope_type"]]
	except KeyError:
		raise KeyError("Microscope type not found in image key value pairs. " \
		"Please ensure that the image has a key 'microscope_type' with value 'WideField', 'CLSM', 'Spinning Disc Confocal' or 'Multiphoton'")
	if microscope_index == 1:  # CLSM
		try:
			pinhole_size = float(image.key_value_pairs["pinhole_size_AU"])
		except KeyError:
			raise KeyError("Pinhole size not found in image key value pairs. " \
			"Please ensure that the image has a key 'pinhole_size_AU' with the pinhole size in AU as the value.")
	# Input checks---------------------------------------------------------------------------------------------------------------------------^

	# Checks that the image meets the requirements for the specified method
	if method == "psf":
		if not image.size_z > 1:
			raise ValueError(f"Image {image.name} (ID: {image.id}) requires a Z stack for {method} analysis but sizeZ is {image.size_z}.")	
	elif method == "registration":
		if not (image.size_c > 1 and image.size_z > 1):
			raise ValueError(f"Image {image.name} (ID: {image.id}) requires a multi-channel Z stack for co-registration analysis but sizeC is {image.size_c} and sizeZ is {image.size_z}.")
	elif method == "drift":
		if not image.size_t > 1:
			raise ValueError(f"Image {image.name} (ID: {image.id}) requires a time series for drift analysis but sizeT is {image.size_t}.")

	# Generates ImagePlus if not already generated, as this is needed for the MetroloJDialog
	image_plus = image.image_plus
	if image_plus is None:
		image_plus = image.generate_ImagePlus()

	# MetroloJDialog needs to be the active image in ImageJ, so sets the current image to the image plus of the image being analysed
	batch_qc._java["WindowManager"].setTempCurrentImage(image_plus)
	# Initialises MetroloJDialog
	Dialog = batch_qc._java["MetroloJDialog"](method_string, batch_qc._java["QC_Options"]())
	Dialog.title = title_string
	Dialog.beadDetectionThreshold = thresholding_method
	Dialog.centerDetectionMethodIndex = center_integer

	# Adding metadata from Omero
	Dialog.NA = image.NA
	Dialog.refractiveIndex = image.refractive_index
	Dialog.emWavelengths = [ch.emission_wave for ch in image.channels]
	Dialog.exWavelengths = [ch.excitation_wave for ch in image.channels]

	Dialog.savePdf = save_pdf
	Dialog.saveSpreadsheet = save_csv
	Dialog.saveImages = save_images

	# This will loop through key value pairs for the given image. 
	# If the key matches a field in the MetroloJDialog, it will set the value of that field to the value in the image key value pairs. 
	# This allows for additional parameters to be set in the MetroloJDialog through project/dataset/image metadata.
	class_fields = [class_obj.getName() for class_obj in Dialog.getClass().getFields()]
	for dict_key in image.key_value_pairs:
		if dict_key in class_fields:
			try:
				setattr(Dialog, dict_key, image.key_value_pairs[dict_key])
			except TypeError:
				try:
					# In order for this to work, boolean values must have already been processed and cast to boolean types in the image key value pairs.
					# As simply casting a string to a boolean will not work (e.g. bool("False") will return True).
					field_type = type(getattr(Dialog, dict_key))
					setattr(Dialog, dict_key, field_type(image.key_value_pairs[dict_key]))
				except ValueError:
					raise TypeError(f"Error: {dict_key} requires input of the type {type(getattr(Dialog, dict_key))}.")
	return Dialog

def execute_MetroloJ_process(Dialog, report_dir, report_name, aquisition_date):
	"""Runs metroloJ setup on the provided dialog and saves outputs to the given report_dir

	Args:
		Dialog (metroloJ_QC.setup.MetroloJDialog): The initialised MetroloJDialog instance
		report_dir (str): Path to the directory where the report will be saved
		report_name (str): The name of the report
		aquisition_date (datetime): The date of acquisition

	Raises:
		RuntimeError: Raised if ImageJ has not been initialised.
		NotImplementedError: Raised if the report type specified in the dialog is not supported. Supported types are "PSF profiler", "stage positioning and drift" and "co-registration".

	Returns:
		The instance of the process that was run, which can be used to access outputs such as images and measurements tables.
	"""
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	image = Dialog.ip
	image_title = image.getTitle()
	creationInfo = [aquisition_date.strftime("%Y-%m-%d %H:%M:%S"), "from Metadata"]
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
		raise NotImplementedError("Report types supported are PSF profiler, stage positioning and drift and co-registration")
	
	report_instance.saveReport(report_dir, report_name, None)
	return execution_instance