import batch_qc

def analyzeParticles(
		Binary_Image,
		size_min = "0.00",
		size_max = "Infinity",
		circ_min = "0.00",
		circ_max = "1.00",
		exclude=True,
		stack=False,
		pixel=False
		):
	"""Runs analyze particles on the binary image, returning the ROI

	Args:
		Binary_Image (ij.ImagePlus): Segmented binary image
		size_min (str): Min size setting for analyse particles. Defaults to "0.00"
		size_max (str): Max size setting for analyse particles. Defaults to "Infinity"
		circ_min (str): Min circularity setting for analyse particles. Defaults to "0.00"
		circ_max (str): Max circularity setting for analyse particles. Defaults to "1.00"
		exclude (bool): Whether to exclude particles touching the edges of the image. Defaults to True
		stack (bool): Whether to analyze the entire Z/T stack. Defaults to False
		pixel (bool): Whether to use pixel units for measurements instead of scaled units. Defaults to False

	Returns:
		[PolygonRoi]: Outputted Rois
	"""	
	
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	
	# Defines analyse particles settings
	AnalyzeParticlesSettings = (f"size={size_min}-{size_max} circularity={circ_min}-{circ_max} overlay")
	if exclude:
		AnalyzeParticlesSettings += " exclude"
	if stack:
		AnalyzeParticlesSettings += " stack"
	if pixel:
		AnalyzeParticlesSettings += " pixel"
	# Runs the analyze particles command to get ROI. 
	# Done by adding to the overlay in order to not have ROIManger shown to user
	batch_qc._java["IJ"].run(Binary_Image, "Analyze Particles...", AnalyzeParticlesSettings)
	# Gets the Overlayed ROIs from analyze particles
	Overlayed_Rois = Binary_Image.getOverlay()
	# Takes the overlay and turns it into an array of ROI
	RoiList = Overlayed_Rois.toArray()
	# Removes this overlay to clean up the image
	batch_qc._java["IJ"].run(Binary_Image, "Remove Overlay", "")
	return RoiList

def getRoiMeasurements(SampleRoi, Image, Measurement_Options):
	"""Gets the given measurements of the provided Roi for the given image

	Args:
		SampleRoi (ij.gui.Roi): Roi to be analysed
		Image (ij.ImagePlus): Image to be analysed
		Measurement_Options ([str]) or ([ij.measure.Measurements]): Measurements to be taken in the form of either strings of the column headings or ij.measure.Measurements integers

	Returns:
		 dict: Dictionary of measurements with column headings as titles
	"""	

	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")

	Measurements = batch_qc._java["Measurements"]

	# This dictionary converts Measurement_Options to the corresponding column names in the results table
	Measurement_Dict = {
		Measurements.ADD_TO_OVERLAY: [None],
		Measurements.AREA: ['Area'],
		Measurements.AREA_FRACTION: ['%Area'],
		Measurements.CENTER_OF_MASS: ['XM', 'YM'],
		Measurements.CENTROID: ['X', 'Y'],
		Measurements.CIRCULARITY: ['Circ.', 'AR', 'Round', 'Solidity'],
		Measurements.ELLIPSE: ['Major', 'Minor', 'Angle'],
		Measurements.FERET: ['Feret', 'FeretX', 'FeretY', 'FeretAngle', 'MinFeret'],
		Measurements.INTEGRATED_DENSITY: ['IntDen'],
		Measurements.INVERT_Y: [None],
		Measurements.KURTOSIS: ['Kurt'],
		Measurements.LABELS: ['Label'],
		Measurements.LIMIT: [None],
		Measurements.MAX_STANDARDS: [None],
		Measurements.MEAN: ['Mean'],
		Measurements.MEDIAN: ['Median'],
		Measurements.MIN_MAX: ['Min', 'Max'],
		Measurements.MODE: ['Mode'],
		Measurements.NaN_EMPTY_CELLS: [None],
		Measurements.PERIMETER: ['Perim.'],
		Measurements.RECT: ['ROI_X', 'ROI_Y', 'ROI_Width', 'ROI_Height'],
		Measurements.SCIENTIFIC_NOTATION: [None],
		Measurements.SHAPE_DESCRIPTORS: ['Circ.', 'AR', 'Round', 'Solidity'],
		Measurements.SKEWNESS: ['Skew'],
		Measurements.SLICE: [None],
		Measurements.STACK_POSITION: [None],
		Measurements.STD_DEV: ['StdDev']
	}

	# Initialises a new empty results table
	RTable = batch_qc._java["ResultsTable"]()
	# Initialises an Analyzer object using 
	# the image and the empty results table
	try:
		# If input list is of ij.measure.Measurements will use those measurements for the analyzer
		Measurement_int = sum(Measurement_Options)
		An = batch_qc._java["Analyzer"](Image, Measurement_int, RTable)
	except TypeError:
		# Otherwise will just use global measurement options
		Measurement_int = None
		An = batch_qc._java["Analyzer"](Image, RTable)
	# Selects the roi on the image
	Image.setRoi(SampleRoi)
	# Takes the measurements
	An.measure()
	# If the measurements were not specified
	# will use input column headings
	if Measurement_int == None:
		Output_List = Measurement_Options
	# Otherwise will get measurement options from dictionary
	else:
		Output_List = []
		for Option in Measurement_Options:
			Output_List += Measurement_Dict[Option]
	# Takes the desired results from the results table and adds to the dictionary
	OutputDict = {}
	for Option in Output_List:
		if Option != None:
			OutputDict[Option] = RTable.getValue(Option, 0)
	# Clears the results table
	RTable.reset()
	# Clears the roi from the image
	Image.resetRoi()
	return OutputDict

def getProjectedBeads(Imp, exclude_edges=True):
	"""Takes a bead image z-stack and returns the rois of beads from a max intensity projected image. 

	Args:
		Imp (ij.ImagePlus): Beads z-stack image
		exclude_edges (bool, optional): Whether to exclude rois touching edges. Defaults to True.

	Returns:
		[ij.gui.Roi]: List of ROIs corresponding to the beads in the projected image
	"""
	Projected = batch_qc._java["ZProjector"].run(Imp, "max")
	# Gaussian blur image
	batch_qc._java["IJ"].run(Projected, "Gaussian Blur...", "sigma=2")
	# Thresholds the image to get the ladder
	batch_qc._java["IJ"].setAutoThreshold(Projected, "Otsu dark")
	batch_qc._java["IJ"].run(Projected, "Convert to Mask", "")
	RoiList = analyzeParticles(Projected, exclude=exclude_edges)
	Projected.close()
	return RoiList
	
def crop_points(img, xy, crop_width, crop_height):
	"""Crops an image around a given point and checks if there is a single bead in the cropped region.

	Args:
		img (ij.ImagePlus): Image to be cropped
		xy (list): List of x and y coordinates to crop around in the form [x, y]
		crop_width (int): Width of the crop region in pixels
		crop_height (int): Height of the crop region in pixels

	Returns:
		tuple: The ROI parameters for the cropped region in the form (x, y, width, height) if there is a single bead in the region, otherwise None
	"""
	roi_params = (round(xy[0]-(crop_width/2)), round(xy[1]-(crop_height/2)), crop_width, crop_height)
	img.setRoi(*roi_params)
	out = img.crop("stack")
	if crop_width != out.getWidth() or crop_height != out.getHeight():
		return None
	RoiList = getProjectedBeads(out, exclude_edges=False)
	out.close()
	if len(RoiList) == 1:
		return roi_params

def get_crop_roi_params(Imp, scaled_width, scaled_height):
	"""Generates roi for single beads from a supplied bead image and returns a list of their defining parameters

	Args:
		Imp (ij.ImagePlus): Bead image
		scaled_width (float): Width of the crop region in scaled units
		scaled_height (float): Height of the crop region in scaled units

	Returns:
		_list_: List of tuples containing the parameters for ROIs corresponding to single beads in the image in the form (x, y, width, height)
	"""

	# Clearing any Rois as this can affect downstream processes
	Imp.resetRoi()
	# Calculate desired crop size in pixels
	Calibration = Imp.getCalibration()
	width_px = round(Calibration.getRawX(scaled_width))
	height_px = round(Calibration.getRawY(scaled_height))

	# Gets the rois of the beads in the projected image
	RoiList = getProjectedBeads(Imp)
	FilteredPointList = []
	# Need unscaled image so can get centroid in pixels not scaled units
	NoScale = Imp.crop()
	NoScale.removeScale()
	for ThisRoi in RoiList:
		Centroid_dict = getRoiMeasurements(ThisRoi, NoScale, [batch_qc._java["Measurements"].CENTROID])
		goodpoint = crop_points(Imp, [round(Centroid_dict["X"]), round(Centroid_dict["Y"])], width_px, height_px)
		if goodpoint is not None:
			FilteredPointList.append(goodpoint)
	# Close the no scale crop to free up memory
	NoScale.close()
	return(FilteredPointList)