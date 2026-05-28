import re
import batch_qc

def analyzeParticles(
		Binary_Image, 
		Size_Setting, 
		Circularity_Setting):
	"""Runs analyze particles on the binary image, returning the ROI

	Args:
		Binary_Image (ij.ImagePlus): Segmented binary image
		Size_Setting (str): Min/Max size settings for analyse particles
		Circularity_Setting (str): Min/Max circularity settings for analyse particles

	Returns:
		[PolygonRoi]: Outputted Rois
	"""	

	# Defines analyse particles settings
	AnalyzeParticlesSettings = (
		"size=" 
		+ Size_Setting 
		+ " circularity=" 
		+ Circularity_Setting 
		+ " clear overlay exclude"
	)
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
		Measurement_Options ([str]): ij.Measure.Measurements to be taken

	Returns:
		[float]: List of measurements in same order as Measurement_Options
	"""	
	
	# Initialises a new empty results table
	RTable = batch_qc._java["ResultsTable"]()
	# Initialises an Analyzer object using 
	# the image and the empty results table
	An = batch_qc._java["Analyzer"](Image, RTable)
	# Selects the roi on the image
	Image.setRoi(SampleRoi)
	# Takes the measurements
	An.measure()
	# Takes the desired results from 
	# the results table and adds to a list
	OutputList = []
	for Option in Measurement_Options:
		OutputList.append(RTable.getValue(Option, 0))
	# Clears the results table
	RTable.reset()
	# Clears the roi from the image
	Image.resetRoi()
	return OutputList


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