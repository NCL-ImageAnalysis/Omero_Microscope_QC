from NanoImagingPack import cal_readnoise # Need to figure out way to do this that doesn't error out if not installed and using other methods
import omero_microscope_qc
from omero_microscope_qc import omero_objects

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

def run_cal_readnoise(bright_image, dark_image, export_path):
	kwargs = dict_comparison_to_base(_NANOIMAGING_DEFAULTS, [bright_image.key_value_pairs, dark_image.key_value_pairs])
	kwargs["exportpath"] = export_path
	bright_image_data = bright_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	dark_image_data = dark_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	kwargs.pop("skip_first")
	return cal_readnoise(bright_image_data, dark_image_data, **kwargs)

def run_detector(conn, image, image_output_directory_str, save_suffix="", save_images=True):
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

	# To Do
	# Check if dataset has key value listing as bright or dark images
	# If not check if regex key value is present and match based on that
	# If not check by checking which has higher mean intensity and assume that is bright image
