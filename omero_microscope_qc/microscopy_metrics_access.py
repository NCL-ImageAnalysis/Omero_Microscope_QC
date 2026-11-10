import omero_microscope_qc
import numpy as np
import os
from microscopy_metrics.detection import Detection
from microscopy_metrics.thresholdTools.threshold_tool import Threshold
from microscopy_metrics.detectionTools.detection_tool import DetectionTool
from microscopy_metrics.metrics import Metrics
from microscopy_metrics.resolutionTools.theoretical_resolution import TheoreticalResolution
from microscopy_metrics.fitting import Fitting
from microscopy_metrics.report_generator import ReportGenerator

# Global variables--------------------------------------------------------------------------------------------v

# Dictionary to hold accepted values for different parameters for MM
_ACCEPTED_VALUES = {
	"thresholding_method": ["isodata", "legacy", "li", "manual", "minimum", "otsu", "triangle"],
	"center_dectection_method": ["Centroids", "peak local maxima", "Laplacian of Gaussian", "Difference of Gaussian"],
	"microscope_type": ["widefield", "confocal", "spinning disk", "multiphoton"]}
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

def run_MM(image,
							outdir,
							  thresholding_method="legacy",
							  center_dectection_method="Centroids",
                              ReportGenerator=ReportGenerator):
	"""Runs the MM PSF image analysis pipeline. Results files are written to outdir

	Args:
		image (batch_qc.omero_objects.ImageObject): ImageObject to be analysed by the MM. Must have key value pairs for "microscope_type" and if microscope type is CLSM, "pinhole_size_AU"
		outdir (str): output directory to save analysis results and temp filess
		thresholding_method (str, optional): Thresholding method used by MM. Must be one of "Legacy", "Li", "Minimum", "Otsu". Defaults to "Otsu".
		center_dectection_method (str, optional): Center detection method used by MM. Must be one of "ellipses", "centroid", "max". Defaults to "centroid".
        ReportGenerator: pass package into function
	Raises:
		KeyError: Raised if the microscope type or pinhole size is not found in the image key value pairs.
		ValueError: Raised if the image does not meet the requirements for the specified method or incorrect inputs passed to function parameters.
		TypeError: Raised if key value pairs used for MM attributes are of the wrong type and cannot be cast to the required type.
	"""
    # translate method strings to MM syntax
	microscope_type_dict = {"WideField": "widefield", "CLSM": "confocal", "Spinning Disc Confocal": "spinning disk", "Multiphoton": "multiphoton"}
	center_method_dic = {"centroid": "Centroids", "max": "peak local maxima"}
    # clear empty dimensions from image
	pic_noEmpty = np.squeeze(image.image_data.values)
	# Input checks---------------------------------------------------------------------------------------------------------------------------v
	check_inputs("thresholding_method", thresholding_method.lower())
	check_inputs("center_dectection_method", center_method_dic[center_dectection_method])	
	try:
		check_inputs("microscope_type", microscope_type_dict[image.key_value_pairs["microscope_type"]])
	except KeyError:
		raise KeyError("Microscope type not found in image key value pairs. " \
		"Please ensure that the image has a key 'microscope_type' with value 'WideField', 'CLSM', 'Spinning Disc Confocal' or 'Multiphoton'")

	# Input checks---------------------------------------------------------------------------------------------------------------------------^

	# Checks that the image meets the requirements for the specified method

	if not image.size_z > 1:
		raise ValueError(f"Image {image.name} (ID: {image.id}) requires a Z stack for PSF analysis but sizeZ is {image.size_z}.")	
	if image.size_c > 1:
		raise ValueError(f"Image {image.name} (ID: {image.id}) has too many channels for PSF analysis. Only one channel is required ")	
	if image.NA == None or image.refractive_index == None:
		raise ValueError(f"Objective information not found for image {image.name} (ID: {image.id}). Please ensure that the image has key value pairs for 'NA' and 'refractiveIndex'.")
    # initialise settings, translate syntax for MM
	settings_dict = {"ringInnerDistance": 1.0, "ringThickness": 2.0, "beadSize": 0.175, "ZRejectionMargin": 1, 
	                 "cropFactor": 10, "thresholdIntensity": 0.5, "prominenceRel": 100, "thresholdRSquared": 0.95}
	translate_settings_name_dict = {"ringInnerDistance": "innerAnnulusEdgeDistanceToBead", 
	                                "ringThickness": "annulusThickness",
                                    "beadSize": "beadSize",
                                    "ZRejectionMargin": "ZRejectionMargin",
                                    "cropFactor": "cropFactor",
                                    "thresholdIntensity": "thresholdIntensity",
                                    "prominenceRel": "prominenceRel",
                                    "thresholdRSquared": "R2Threshold"}
	# replace with keyvals where available
	for key, val in enumerate(settings_dict):
		try:
			settings_dict[val] = float(image.key_value_pairs[translate_settings_name_dict[val]])
		except:
			pass
	detector = Detection()
	detector.image = pic_noEmpty # Assign the PSF image

	# Configure the detection tool (e.g., "Centroids", "peak local maxima", etc.)
	detectionTool = DetectionTool.getInstance(center_method_dic[center_dectection_method])
	detectionTool._image = pic_noEmpty
	detectionTool._thresholdTool = Threshold.getInstance(thresholding_method.lower())

	# Assign the detection tool to the detector
	detector._detectionTool = detectionTool
	detector.beadSize = settings_dict["beadSize"] # Expected bead size (in micrometers)
	detector._ZRejectionMargin = settings_dict["ZRejectionMargin"] # reject bead if too close to top or bottom of stack
	detector._cropFactor = settings_dict["cropFactor"]
	detector._thresholdIntensity = settings_dict["thresholdIntensity"]
	detector._prominenceRel = settings_dict["prominenceRel"]
	detector.pixelSize = np.array([image.scale_z._value, image.scale_y._value, image.scale_x._value])  # Pixel size (Z, Y, X)

	# Run detection and save ROIs
	for _ in detector.run(outputDir=outdir):
		pass

	# Access the image analyzer for further processing
	imageAnalyzer = detector._imageAnalyzer
	imageAnalyzer._path = outdir

    # Initialize the metrics tool
	MetricTool = Metrics()
	MetricTool._imageAnalyzer = imageAnalyzer

	# Adding metadata from Omero

	MetricTool._TheoreticalResolutionTool = TheoreticalResolution.getInstance(microscope_type_dict[image.key_value_pairs["microscope_type"]])
	MetricTool._TheoreticalResolutionTool._numericalAperture = image.NA
	MetricTool._TheoreticalResolutionTool._refractiveIndex = image.refractive_index
	MetricTool._TheoreticalResolutionTool._excitationWavelength = [ch.excitation_wave for ch in image.channels][0]
	MetricTool._TheoreticalResolutionTool._emissionWavelength = [ch.emission_wave for ch in image.channels][0]

	# Set ring parameters for SBR calculation
	MetricTool._ringInnerDistance = settings_dict["ringInnerDistance"]  # Inner radius for background estimation
	MetricTool._ringThickness = settings_dict["ringThickness"]     # Thickness of the background ring

	# Run pre-fitting metrics
	for _ in MetricTool.runPrefittingMetrics():
		pass
	# Save mesh data for each bead (optional)
	for bead in imageAnalyzer._beadAnalyzer:
		if bead._rejected == False and bead._roi is not None and bead._metricTool.meshBuilder is not None:
			bead._metricTool.meshBuilder.saveMesh(os.path.join(outdir, f"bead_{bead._id}_mesh.obj"))
	# Initialize the fitting tool
	FittingTool = Fitting()
	FittingTool._imageAnalyzer = imageAnalyzer

	# Configure fitting parameters
	FittingTool.fitType = "1D"  # or "1D", "3D", "2D Ellips", "2D Rotation", "3D Rotation"
	FittingTool._thresholdRSquared = settings_dict["thresholdRSquared"]  # Minimum R² value for a valid fit

	# Run the fitting
	FittingTool.computeFitting()

	# Assign the fitting results to the metrics tool
	MetricTool._imageAnalyzer = FittingTool._imageAnalyzer

	# Run metrics calculation
	for _ in MetricTool.runMetrics():
		pass

	# Access the updated image analyzer
	imageAnalyzer = MetricTool._imageAnalyzer

	# Crop PSF images for the report
	detector.cropPsf(outdir)          # Crop individual PSFs
	detector.GlobalCropPsf(outdir)    # Crop global PSF overview

	# Display fitting results
	FittingTool.displayFitting(outdir)

	# Generate the HTML report
	ReportGenerator = ReportGenerator().getInstance("PDF")
	ReportGenerator._inputDir = outdir
	ReportGenerator._imageAnalyzer = imageAnalyzer
	ReportGenerator.generateReport(outdir)