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

def run_cal_readnoise(bright_image, dark_image, export_path):
	kwargs = _NANOIMAGING_DEFAULTS.copy()
	kwargs["exportpath"] = export_path
	bright_image_data = bright_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	dark_image_data = dark_image.image_data.to_numpy()[kwargs["skip_first"]:, 0, 0, :, :]
	kwargs.pop("skip_first")
	return cal_readnoise(bright_image_data, dark_image_data, **kwargs)
