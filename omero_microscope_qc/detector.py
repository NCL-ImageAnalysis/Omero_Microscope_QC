# NanoImagingPack is optional: if it is missing (or fails to import) the rest of the package still works,
# but detector QC is disabled. Check NANOIMAGINGPACK_AVAILABLE before calling into this module.
try:
	from NanoImagingPack import cal_readnoise
	NANOIMAGINGPACK_AVAILABLE = True
	NANOIMAGINGPACK_IMPORT_ERROR = None
except Exception as e:
	cal_readnoise = None
	NANOIMAGINGPACK_AVAILABLE = False
	NANOIMAGINGPACK_IMPORT_ERROR = e
from omero_microscope_qc import omero_objects
import numpy as np

# Default settings for NanoImagingPack cal_readnoise function
_NANOIMAGING_DEFAULTS = {
	"skip_first" : 10,
	"numBins" : 100,
	"validRange" : None,
	"linearity_range" : None,
	"histRange" : None,
	"CameraName" : None,
	"correctBrightness" : True,
    "correctOffsetDrift" : True,
	"exclude_hot_cold_pixels" : True,
	"noisy_pixel_percentile" : 98,
	"doPlot" : True,
	"exportFormat" : "png",
    "brightness_blurring" : True, #sCMOS Filter
	"plotWithBgOffset" : True,
	"plotHist" : False,
	"check_bg" : False,
	"saturationImage" : True,
	}

# Minimum fold change in brightness between bright and dark images for detector QC
_MIN_FOLD_CHANGE = 10

def dict_comparison_to_base(base_dict, comparison_dict_list):
	"""Identifies what differences there are from a base dictionary there are to a provided list of dictionaries (where matching keys exist) 

	Args:
		base_dict (dict): The base dictionary.
		comparison_dict_list (list[dict]): A list of dictionaries to compare against the base dictionary.

	Raises:
		ValueError: Provided dictionaries have different values for the same key.

	Returns:
		dict: A new dictionary with the same keys as the base dictionary, but with values from the comparison dictionaries where they exist and match, or from the base dictionary where they do not exist in the comparison dictionaries.
	"""
	# Used to provide any differences in the key value pairs between the bright and dark images for error checking
	errors = []
	new_dict = {}
	# Iterating through keys
	for k in base_dict:
		value_set = set()
		# Iterating though dictionaries
		for d in comparison_dict_list:
			# Adds each unique value to set
			if k in d:
				value_set.add(d[k])
		# if there are multiple values for same key will raise error for it
		if len(value_set) > 1:
			errors.append(k)
		# If there is only one value for the key, will add it to the new dictionary by selecting a "random" value
		elif len(value_set) == 1:
			new_dict[k] = value_set.pop() 
		# If there are no values for the key in the comparison dictionaries, will add the value from the base dictionary to the new dictionary
		else:
			new_dict[k] = base_dict[k]
	# Raises an error if there are any keys with different values in the comparison dictionaries
	if len(errors) > 0:
		raise ValueError(f"Key Value(s) {errors} have different values in bright and dark images")
	return new_dict

def run_cal_readnoise(bright_image, dark_image, export_path, save_images=True):
	"""Runs the NanoImagingPack cal_readnoise function

	Args:
		bright_image (omero_objects.ImageObject): The bright image.
		dark_image (omero_objects.ImageObject): The dark image.
		export_path (_type_): The path to the export directory.
		save_images (bool, optional): Whether to save the output images. Defaults to True.

	Returns:
		tuple: tuple of fit results (offset [adu], gain [electrons / adu], readnoise [e- RMS])
	"""
	# Checks if NanoImagingPack is available and raises an error if not
	_require_nanoimagingpack()
	kwargs = dict_comparison_to_base(_NANOIMAGING_DEFAULTS, [bright_image.key_value_pairs, dark_image.key_value_pairs])
	kwargs["exportpath"] = export_path
	bright_image_data = bright_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	dark_image_data = dark_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	kwargs["doPlot"] = save_images
	kwargs.pop("skip_first")
	return cal_readnoise(bright_image_data, dark_image_data, **kwargs)

def _require_nanoimagingpack():
	if not NANOIMAGINGPACK_AVAILABLE:
		raise ImportError(
			"Detector QC requires NanoImagingPack, which could not be imported "
			f"({NANOIMAGINGPACK_IMPORT_ERROR!r}). Install it with: "
			"pip install git+https://github.com/bionanoimaging/NanoImagingPack.git"
		) from NANOIMAGINGPACK_IMPORT_ERROR

def run_detector(conn, image, image_output_directory_str, save_images=True):
	"""Identifies the partner detector image for supplied image and runs the NanoImagingPack cal_readnoise function, saving the output to the specified directory.

	Args:
		conn (gateway.BlitzGateway): Connected BlitzGateway
		image (omero_objects.ImageObject): The image to process. Either the bright or dark image can be supplied, the function will find the partner image in the same dataset.
		image_output_directory_str (str): The directory to save the output images.
		save_images (bool, optional): Whether to save the output images. Defaults to True.

	Returns:
		tuple: tuple of fit results (offset [adu], gain [electrons / adu], readnoise [e- RMS])
	"""
	# Checks if NanoImagingPack is available and raises an error if not
	_require_nanoimagingpack()
	# Checks if the image has already been processed
	# If so, returns None so annotations are not attempted to be uploaded
	if omero_objects.Bool_or_Missing(image.key_value_pairs, "QC_Processed"):
		return None

	# Gets the partner image for the given image
	dataset = image.parent
	try:
		# Used to eliminate any images with multiple partners identified
		n_partners = 0
		# First checks if test identifier has been set for the image and uses that to find the partner image
		test_index = image.key_value_pairs["test_identifier"]
		for partner in dataset.children:
			if partner.key_value_pairs.get("test_identifier") == test_index and partner.id != image.id:
				partner_image = partner
				n_partners += 1
	# If no test_identifier is set, uses acquisition date to find the partner image
	# This will either be from OMERO metadata or parsed from the filename by omero_objects
	except KeyError:
		for partner in dataset.children:
			try:
				if partner.acquisition_date.strftime("%Y-%m-%d") == image.acquisition_date.strftime("%Y-%m-%d") and partner.id != image.id:
					partner_image = partner
					n_partners += 1
			except AttributeError:
				raise ValueError(f'Image {image.id} or partner image {partner.id} does not have an acquisition date set. Either include date in filename or add matching "test_identifier" to key value pairs.')
	if n_partners == 0:
		raise ValueError(f"No partner image found for image {image.id} in dataset {dataset.id} during detector QC.")
	if n_partners > 1:
		raise ValueError(f"Multiple partner images found for image {image.id} in dataset {dataset.id} during detector QC.")

	# Checks if partner image has already been processed
	# If so links its annotations to this image, sets "QC_Processed": "True" 
	# and returns None so annotations are not attempted to be uploaded
	if omero_objects.Bool_or_Missing(partner_image.key_value_pairs, "QC_Processed"):
		for ann in partner_image.file_annotations:
			if ann.getNs() == "qc.detector":
				image.link_annotation(ann)
		image.add_key_values(conn, {"QC_Processed": "True"}, namespace="qc.status")
		return None

	bright_dark_images = {}
	# First checks if the bright/dark status has been set for the image and partner image in the key value pairs
	try:
		bright_dark_images[image.key_value_pairs["bright_or_dark"]] = image
		bright_dark_images[partner_image.key_value_pairs["bright_or_dark"]] = partner_image
	# If the bright/dark status has not been set, uses the mean brightness of the images to determine which is bright and which is dark
	except KeyError:
		image_pair = [image, partner_image]
		brightness = [imp.image_data.mean() for imp in image_pair]
		fold_change = max(brightness) / min(brightness)
		# Fold change is set to a minimum threshold. May need tuning later
		if fold_change < _MIN_FOLD_CHANGE:
			raise ValueError(f"Images {image.id} and {partner_image.id} do not have a sufficient difference in brightness for detector QC. \
			                 Minimum fold change is {_MIN_FOLD_CHANGE} but the fold change is {fold_change}")
		# Argmax and argmin are used to identify the list index of the image pair
		bright_dark_images["bright"] = image_pair[np.argmax(brightness)]
		bright_dark_images["dark"] = image_pair[np.argmin(brightness)]
		# Sets the bright/dark status in the key value pairs for both images for future reference/validation
		bright_dark_images["bright"].add_key_values(conn, {"bright_or_dark": "bright"}, namespace="qc.params")
		bright_dark_images["dark"].add_key_values(conn, {"bright_or_dark": "dark"}, namespace="qc.params")
	# Runs the NanoImagingPack cal_readnoise function and saves the output to the specified directory
	run_cal_readnoise(bright_dark_images["bright"], bright_dark_images["dark"], image_output_directory_str, save_images=save_images)
	return image_output_directory_str