from NanoImagingPack import cal_readnoise # Need to figure out way to do this that doesn't error out if not installed and using other methods

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

def run_detector(image, image_output_directory_str, save_suffix="", save_images=True):
	dataset = image.parent
	# To Do
	# Check if already has been processed and if so return None
	# Check if dataset has key value to tie to test date otherwise use aquisition date
	# Check if partner has already been processed
	# If so link its annotations to this image, set "QC_Processed": "True" and return None
	# Check if dataset has key value listing as bright or dark images
	# If not check if regex key value is present and match based on that
	# If not check by checking which has higher mean intensity and assume that is bright image
