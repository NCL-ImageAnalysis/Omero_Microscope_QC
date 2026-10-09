from NanoImagingPack import cal_readnoise # Need to figure out way to do this that doesn't error out if not installed and using other methods
from omero_microscope_qc import omero_objects
import numpy as np

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

_MIN_FOLD_CHANGE = 10

def dict_comparison_to_base(base_dict, comparison_dict_list):
	errors = []
	new_dict = {}
	for k in base_dict:
		value_set = set()
		for d in comparison_dict_list:
			if k in d:
				value_set.add(d[k])
		if len(value_set) > 1:
			errors.append(k)
		elif len(value_set) == 1:
			new_dict[k] = value_set.pop() 
		else:
			new_dict[k] = base_dict[k]
	if len(errors) > 0:
		raise ValueError(f"Key Value(s) {errors} have different values in bright and dark images")
	return new_dict

def run_cal_readnoise(bright_image, dark_image, export_path, save_images=True):
	kwargs = dict_comparison_to_base(_NANOIMAGING_DEFAULTS, [bright_image.key_value_pairs, dark_image.key_value_pairs])
	kwargs["exportpath"] = export_path
	bright_image_data = bright_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	dark_image_data = dark_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	kwargs["doPlot"] = save_images
	kwargs.pop("skip_first")
	return cal_readnoise(bright_image_data, dark_image_data, **kwargs)

def run_detector(conn, image, image_output_directory_str, save_images=True):
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
	except KeyError:
		for partner in dataset.children:
			if partner.acquisition_date == image.acquisition_date and partner.id != image.id:
				partner_image = partner
				n_partners += 1
	if n_partners == 0:
		raise ValueError(f"No partner image found for image {image.id} in dataset {dataset.id} during detector QC.")
	if n_partners > 1:
		raise ValueError(f"Multiple partner images found for image {image.id} in dataset {dataset.id} during detector QC.")

	# Checks if partner image has already been processed
	# If so links its annotations to this image, sets "QC_Processed": "True" 
	# and returns None so annotations are not attempted to be uploaded
	if omero_objects.Bool_or_Missing(partner_image.key_value_pairs, "QC_Processed"):
		for ann in partner_image.file_annotations:
			image.link_annotation(ann)
		image.add_key_values(conn, {"QC_Processed": True}, namespace="qc.status")
		return None

	bright_dark_images = {}
	try:
		bright_dark_images[image.key_value_pairs["bright_or_dark"]] = image
		bright_dark_images[partner_image.key_value_pairs["bright_or_dark"]] = partner_image
	except KeyError:
		image_pair = [image, partner_image]
		brightness = [imp.image_data.mean() for imp in image_pair]
		fold_change = max(brightness) / min(brightness)
		if fold_change < _MIN_FOLD_CHANGE:
			raise ValueError(f"Images {image.id} and {partner_image.id} do not have a sufficient difference in brightness for detector QC. \
			                 Minimum fold change is {_MIN_FOLD_CHANGE} but the fold change is {fold_change}")							 
		bright_dark_images["bright"] = image_pair[np.argmax(brightness)]
		bright_dark_images["dark"] = image_pair[np.argmin(brightness)]
		bright_dark_images["bright"].add_key_values(conn, {"bright_or_dark": "bright"}, namespace="qc.params")
		bright_dark_images["dark"].add_key_values(conn, {"bright_or_dark": "dark"}, namespace="qc.params")
	run_cal_readnoise(bright_dark_images["bright"], bright_dark_images["dark"], image_output_directory_str, save_images=save_images)
	return image_output_directory_str