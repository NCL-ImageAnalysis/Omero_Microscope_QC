import re
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
		[float]: Dictionary of measurements with column headings as titles
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


def distanceBetweenPoints(X1, Y1, X2, Y2):
	"""Calculates the distance between two coordinates

	Args:
		X1 (float): Start X coordinate
		Y1 (float): Start Y coordinate
		X2 (float): End X coordinate
		Y2 (float): End Y coordinate

	Returns:
		float: Distance between the two points
	"""	
	xdiff = X1 - X2
	ydiff = Y1 - Y2
	Distance = batch_qc._java["Math"].sqrt((xdiff*xdiff) + (ydiff*ydiff))
	return Distance


def closestPoint(Point, Point_List):
	"""Finds the closest two points in a list of ROIs

	Args:
		Roi (ij.gui.Roi): Roi to compare distances to
		RoiList (ij.gui.Roi[]): List of ROIs

	Returns:
		list: List of the two closest ROIs
	"""	
	MinDistance = float("Infinity")
	MinPoint = (None, None)

	for OtherPoint in Point_List:
		Distance = distanceBetweenPoints(Point[0], Point[1], OtherPoint[0], OtherPoint[1])
		if Distance < MinDistance:
			MinDistance = Distance
			MinPoint = OtherPoint
	return MinPoint
	

def roundToBase(Number, Base):
	"""Rounds the given number to the nearest multiple of the given base

	Args:
		Number (float): Number to be rounded
		Base (int): Base to round to

	Returns:
		int: Rounded number
	"""	
	RoundedNumber = (Base * batch_qc._java["Math"].round(Number/Base))
	return RoundedNumber


def getAngleBetweenPoints(Point1, Point2):
	"""Gets the angle between two points in degrees

	Args:
		Point1 (tuple): X and Y coordinates of first point
		Point2 (tuple): X and Y coordinates of second point

	Returns:
		float: Angle between two points in degrees
	"""	
	Angle = batch_qc._java["Math"].toDegrees(batch_qc._java["Math"].atan2(Point2[1] - Point1[1], Point2[0] - Point1[0]))
	return Angle


def selectWindow(Pattern):
	"""Selects the window with the given pattern in the title

	Args:
		Pattern (string): regex pattern to match

	Returns:
		boolean: Whether the given window was found and selected
	"""	
	TitleList = batch_qc._java["WindowManager"].getImageTitles()
	for Title in TitleList:
		Title = str(Title)
		if re.match(Pattern, Title):
			batch_qc._java["IJ"].selectWindow(Title)
			return True
	return False

def getProjectedBeads(Imp, exclude_edges=True):
	Projected = batch_qc._java["ZProjector"].run(Imp, "max")
	# Gaussian blur image
	batch_qc._java["IJ"].run(Projected, "Gaussian Blur...", "sigma=2")
	# Thresholds the image to get the ladder
	batch_qc._java["IJ"].setAutoThreshold(Projected, "Otsu dark")
	batch_qc._java["IJ"].run(Projected, "Convert to Mask", "")
	RoiList = analyzeParticles(Projected, exclude_edges)
	Projected.close()
	return RoiList
	
def crop_points(img, xy, crop_width, crop_height):
	img.setRoi(xy[0]-(crop_width/2), xy[1]-(crop_height/2), crop_width, crop_height)
	out = img.crop("stack")
	if crop_width != out.getWidth() or crop_height != out.getHeight():
		return None
	RoiList = getProjectedBeads(out, exclude_edges=False)
	out.close()
	if len(RoiList) == 1:
		return xy

def get_crop_roi_params(Imp, scaled_width, scaled_height):
	# calculate desired crop size in pixels
	Calibration = Imp.getCalibration()
	width_px = round(Calibration.getRawX(scaled_width))
	height_px = round(Calibration.getRawY(scaled_height))

	RoiList = getProjectedBeads(Imp)
	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]
	# Gets the centroid of each ROI and adds to a list-------------------v
	FilteredPointList = []
	NoScale = Imp.crop()
	NoScale.removeScale()
	for ThisRoi in RoiList:
		Centroid_dict = getRoiMeasurements(ThisRoi, NoScale, [batch_qc._java["Measurements"].CENTROID])
		goodpoint = crop_points(Imp, [round(Centroid_dict["X"]), round(Centroid_dict["Y"])], width_px, height_px)
		if goodpoint is not None:
			goodpoint += [width_px, height_px]
			FilteredPointList.append(goodpoint)
	NoScale.close()
	return(FilteredPointList)