# Python modules
import copy, os
from collections import Counter
import batch_qc
from batch_qc.imagej_utils import *

def run_z_accuracy(input_image,
		output_directory, save_suffix=""):
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	
	if not input_image.size_z > 1:
			raise ValueError(f"Image {input_image.name} (ID: {input_image.id}) requires a Z stack for z accuracy analysis but sizeZ is {input_image.size_z}.")
	
	# This section sets the measurements that will be used
	AnalyzerClass = batch_qc._java["Analyzer"]()
	# Gets original measurements to reset later
	OriginalMeasurements = AnalyzerClass.getMeasurements()

	# Sets the measurements to be used
	AnalyzerClass.setMeasurements(
		batch_qc._java["Measurements"].SHAPE_DESCRIPTORS 
		+ batch_qc._java["Measurements"].CENTROID
	)

	image_plus = input_image.generate_ImagePlus()

	# Gets the needed paths and filenames for input and output
	FileName = input_image.name
	FileNameNoExtension = ".".join(FileName.split(".")[:-1])
	OutputPath = output_directory
	#------------------------------------------------------^

	Calibration = image_plus.getCalibration()
	ZDepth = Calibration.pixelDepth

	# Max intensity of the image to get all of the ladder
	Projected = batch_qc._java["ZProjector"].run(image_plus, "max")
	# Removes the scale so ROI coordinates are correct
	Projected.removeScale()
	# Thresholds the image to get the ladder
	batch_qc._java["IJ"].setAutoThreshold(Projected, "Default dark")
	batch_qc._java["IJ"].run(Projected, "Convert to Mask", "")
	# Runs analyze particles to get a list of ROIs
	RoiList = analyzeParticles(Projected, "10-Infinity", "0.00-1.00")

	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]

	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	for ThisRoi in RoiList:
		Centroid = getRoiMeasurements(ThisRoi, Projected, CentroidString)
		# Must be a tuple to be hashable in dictionary
		PointList.append(tuple(Centroid))
	#--------------------------------------------------------------------^

	# For each point it will get the angle of the line between it and the closest point-v
	# This will be used to eliminate the points that are not part of the ladder
	# As these points will all be running parallel to each other
	PointDict = {}
	RoundedAngleList = []
	for Index, PointItem in enumerate(PointList):
		# Need to deep copy the list to avoid modifying the original
		InputList = copy.copy(PointList)
		# Need to remove the current point from the list to avoid finding itself
		del InputList[Index]
		# Finds the closest point to the current point
		ClosestPoint = closestPoint(PointItem, InputList)
		# Gets the angle between the two points
		LineAngle = getAngleBetweenPoints(PointItem, ClosestPoint)
		# Rounds the angle to the nearest 5 degrees
		# Has to be absolute as the lines can be in either direction
		RoundedAngle = abs(roundToBase(LineAngle, 5))
		if RoundedAngle >= 180:
			RoundedAngle -= 180
		# Adds the angle to a dictionary with the point as the key
		PointDict[PointItem] = RoundedAngle
		# Adds the angle to a list of all angles to find the mode
		RoundedAngleList.append(RoundedAngle)
	#-----------------------------------------------------------------------------------^

	# Gets the mode angle
	ModeAngle = Counter(RoundedAngleList).most_common(1)[0][0]
	# Gets the points that have the mode angle--------v
	# These are the points that are part of the ladder
	LadderList = []
	for PointItem in PointDict:
		if ModeAngle == PointDict[PointItem]:
			LadderList.append(PointItem)
	#-------------------------------------------------^

	# Gets the two points that are furthest apart but are still parallel to each other--------------------------v
	MaxLadderDistance = 0
	for Index, FirstPoint in enumerate(LadderList):
		# Need to deep copy the list to avoid modifying the original
		SecondList = copy.copy(LadderList)
		# Need to remove the current point from the list to avoid finding itself
		del SecondList[Index]
		# Loops though every other list of points to find the furthest apart
		for SecondPoint in SecondList:
			# Gets the angle between the two points, has to be absolute as the lines can be in either direction
			if FirstPoint[0] <= SecondPoint[0]:
				LadderAngle = getAngleBetweenPoints(FirstPoint, SecondPoint)
			else:
				LadderAngle = getAngleBetweenPoints(SecondPoint, FirstPoint)
			# Gets the distance between the two points
			LadderDistance = distanceBetweenPoints(FirstPoint[0], FirstPoint[1], SecondPoint[0], SecondPoint[1])
			# Rounds the angle to the nearest 5 degrees
			RoundedLadderAngle = abs(roundToBase(LadderAngle, 5)
)
			if RoundedLadderAngle >= 180:
				RoundedLadderAngle -= 180
			# If the angle is the same as the mode angle and the distance is greater than the current max
			# Then these are the new furthest apart points
			if RoundedLadderAngle == ModeAngle and LadderDistance > MaxLadderDistance:
				FeducialLine = batch_qc._java["Line"](FirstPoint[0], FirstPoint[1], SecondPoint[0], SecondPoint[1])
				# This angle is not rounded as it is used to rotate the image
				FeducialAngle = LadderAngle
				MaxLadderDistance = LadderDistance
	#-----------------------------------------------------------------------------------------------------------^

	# Need to use an overlay so it will rotate with the image
	LineOverlay = batch_qc._java["Overlay"](FeducialLine)
	image_plus.setOverlay(LineOverlay)
	
	# Rotates the image so the ladder is horizontal
	batch_qc._java["IJ"].run(image_plus, "Arbitrarily...", "angle=" + str(-FeducialAngle) + " interpolate stack")
	# Gets the Rotated Roi from the overlay
	RotatedLineOverlay = image_plus.getOverlay()
	RotatedLineRoi = RotatedLineOverlay.get(0)
	
	# Removes the overlay to clean up the image
	image_plus.setOverlay(None)

	# Gets the centroid of the rotated line
	LineCentroid = getRoiMeasurements(RotatedLineRoi, Projected, CentroidString)

	# Gets the width of the image
	Width = image_plus.getWidth()
	# Creates a box roi that is 1 pixel high and the width of the image centred on the line centroid
	BoxRoi = batch_qc._java["Roi"](0, LineCentroid[1], Width, 1)

	# Crops the image to the single line
	image_plus.setRoi(BoxRoi)
	LineImage = image_plus.crop("stack")
	# Closes the original image to save memory
	image_plus.close()

	# Runs the reslice command to get the XZ image similar to orthagonal view
	batch_qc._java["IJ"].run(LineImage, "Reslice [/]...", "output=" + str(ZDepth) +" start=Top avoid")

	# Gets the resliced image
	batch_qc._java["IJ"].selectWindow("Reslice ")
	OriginalSlicedImp = batch_qc._java["IJ"].getImage()
	# Duplicates the image to only get one slice
	SlicedImp = OriginalSlicedImp.crop()
	# Close the original image to save memory
	OriginalSlicedImp.close()

	# Performs gaussian blur to smooth the image
	batch_qc._java["IJ"].run(SlicedImp, "Gaussian Blur...", "sigma=6")
	# Gets the statistics which includes the minimum and maximum intensity of the image
	ImpStats = SlicedImp.getStatistics()
	# Sets the prominence for the find maxima command to be half the difference between the min and max intensity
	Prominence = str((ImpStats.max - ImpStats.min)/2)
	# Finds the maxima in the image and outputs to a results table
	batch_qc._java["IJ"].run(SlicedImp, "Find Maxima...", "prominence=" + Prominence + " output=List")

	# Resets the contrast for easier viewing
	SlicedImp.resetDisplayRange()
	# Saves the XZ image and closes to save memory
	batch_qc._java["FileSaver"](SlicedImp).saveAsTiff(os.path.join(OutputPath, FileNameNoExtension + save_suffix + "_XZ.tif"))
	SlicedImp.close()

	# Gets the results table and copies it so the displayed one can be closed
	Results = batch_qc._java["ResultsTable"]().getResultsTable()
	MaximaResults = Results.clone()
	# Needs to reset the table to avoid dialog asking to save
	Results.reset()
	# Closes the results table
	batch_qc._java["WindowManager"].getWindow("Results").close()

	# Calculates the axial step size for each maxima
	for Row in range(0, MaximaResults.size()):
		AxialStep = MaximaResults.getValue("Y", Row) * ZDepth
		MaximaResults.setValue("AxialStep", Row, AxialStep)

	# Sorts the results table by the X coordinate
	MaximaResults.sort("X")

	# Calculates the axial difference between each maxima
	for SortedRow in range(1, MaximaResults.size()):
		AxialDiff = abs(MaximaResults.getValue("AxialStep", SortedRow) - MaximaResults.getValue("AxialStep", SortedRow - 1))
		MaximaResults.setValue("AxialDiff", SortedRow, AxialDiff)

	# Saves the results table
	MaximaResults.saveAs(os.path.join(OutputPath, FileNameNoExtension + save_suffix + "_XZ.csv"))

	# Resets the measurements to the original settings
	AnalyzerClass.setMeasurements(OriginalMeasurements)
