# Python modules
import copy, os
from collections import Counter
import pandas as pd
import networkx as nx
import numpy as np
import batch_qc
from batch_qc.imagej_utils import *

def closest_x_points(df, num_points=2, identifier_col="point"):
	"""Takes a pandas dataframe with X and Y coordinates for each point and returns a dataframe with the closest x points for each point.
	This contains the index and coordinates of the original and matching points

	Args:
		df (pandas.DataFrame): DataFrame with X and Y coordinates for each point. Must contain columns "X", "Y" and an identifier column where the identifier is a unique identifier for each point.
		num_points (int, optional): Number of closest points to return for each point. Defaults to 2.
		identifier_col (str, optional): Name of the column containing the unique identifier for each point. Defaults to "point".

	Returns:
		pandas.DataFrame: DataFrame with the closest x points for each point. This contains the index and coordinates of the original and matching points
	"""
	rows = []
	for index in df.index:
		distance_frame = df.drop(index).copy()
		x1 = df["X"][index]
		y1 = df["Y"][index]
		point1 = df[identifier_col][index]
		distance_frame["Distance"] = np.sqrt(((distance_frame["X"] - x1) ** 2) + ((distance_frame["Y"] - y1) ** 2))
		distance_frame = distance_frame.sort_values(by="Distance")
		if len(distance_frame) < num_points:
			raise ValueError(f"num_points is set to {num_points} but there are only {len(distance_frame)} other points in the dataframe.")
		# Add two rows: nearest and second nearest, with only coordinate/point columns
		for i in range(num_points):
			match = distance_frame.iloc[i]
			rows.append({
				"point1": int(point1),
				"x1": x1,
				"y1": y1,
				"point2": int(match[identifier_col]),
				"x2": match["X"],
				"y2": match["Y"]})
	return pd.DataFrame(rows)

def get_feducial_points(df):
	"""Gets the start and end coordinates of one of the Z ladder lines

	Args:
		df (pandas.DataFrame): DataFrame containing paired points with columns "point1", "x1", "y1", "point2", "x2", "y2". This should be the output of closest_x_points function.

	Returns:
		tuple: A tuple containing the start and end coordinates of the Z ladder line in the format (X1, Y1, X2, Y2)
	"""
	# Calculates the angle between each pair of points
	df["angle"] = np.degrees(np.arctan2((df["y1"] - df["y2"]), (df["x1"] - df["x2"])))
	# Means parallel lines will have the same angle even if they are in opposite directions.
	df.loc[df["angle"] >= 180, "angle"] -= 180
	# Rounds the angles to the nearest 10 degrees to find the most common angle
	df["angle"] = df["angle"].div(10).round(0) * 10
	# Gets most common angle and filters the dataframe to only include pairs of points with this angle
	mode_angle = df["angle"].mode().iloc[0]
	df = df[df["angle"] == mode_angle]
	# Creates a graph where each point is a node and there is an edge between points that are close to each other.
	graph = nx.from_pandas_edgelist(df, source="point1", target="point2")
	components = [list(c) for c in nx.connected_components(graph)]
	# First node in the graph will be the start of the ladder and the last node will be the end of the ladder
	feducial_start = df[df["point1"] == components[0][0]].reset_index()
	feducial_end = df[df["point1"] == components[0][-1]].reset_index()
	X1 = feducial_start["x1"][0]
	Y1 = feducial_start["y1"][0]
	X2 = feducial_end["x2"][0]
	Y2 = feducial_end["y2"][0]
	return X1, Y1, X2, Y2

def run_z_accuracy(input_image,
		output_directory, save_suffix=""):
	"""Used to measure accuracy of the z stage using a z-stack image of an Argolite Z-ladder.

	Args:
		input_image (ij.ImagePlus): ImagePlus object containing a z-stack image of an Argolite Z-ladder.
		output_directory (str): Path to the directory where output files will be saved.
		save_suffix (str, optional): Suffix to append to the output filenames. Defaults to "".

	Raises:
		RuntimeError: Function called without initialising ImageJ.
		ValueError: Input image is not a Z stack.
	"""
	# ImageJ must be initialised to use this function as it relies on ImageJ functions and classes
	if batch_qc._ij is None:
		raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
	# Z stack is needed for this analysis
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

	image_plus = input_image.generate_ImagePlus().duplicate()

	# Gets the needed paths and filenames for input and output
	FileName = input_image.name
	FileNameNoExtension = ".".join(FileName.split(".")[:-1])
	OutputPath = output_directory

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
	RoiList = analyzeParticles(Projected, size_min="10")

	# Gets the centroid of each ROI and adds to a list
	PointList = []
	for ThisRoi in RoiList:
		Centroid = getRoiMeasurements(ThisRoi, Projected, [batch_qc._java["Measurements"].CENTROID])
		PointList.append([Centroid["X"], Centroid["Y"]])

	# Creates a pandas dataframe of the points
	df = pd.DataFrame(PointList, columns=["X", "Y"])
	df["point"] = df.index

	# Gets a dataframe with the closest 2 points for each point which will be used to find the coordinates of the start and end of the ladder
	comparison_df = closest_x_points(df, num_points=2, identifier_col="point")
	# Gets the coordinates of the start and end of the ladder to act as a feducial line for the rest of the analysis
	line_args = get_feducial_points(comparison_df)
	
	# Creates an ImageJ line roi 
	FeducialLine = batch_qc._java["Line"](*line_args)
	# This angle is not rounded as it is used to rotate the image
	FeducialAngle = FeducialLine.getAngle()

	# Need to use an overlay so it will rotate with the image
	LineOverlay = batch_qc._java["Overlay"](FeducialLine)
	image_plus.setOverlay(LineOverlay)
	
	# Rotates the image so the ladder is horizontal
	batch_qc._java["IJ"].run(image_plus, "Arbitrarily...", "angle=" + str(FeducialAngle) + " interpolate stack")
	# Gets the Rotated Roi from the overlay
	RotatedLineOverlay = image_plus.getOverlay()
	RotatedLineRoi = RotatedLineOverlay.get(0)
	
	# Removes the overlay to clean up the image
	image_plus.setOverlay(None)

	# Gets the centroid of the rotated line
	LineCentroid = getRoiMeasurements(RotatedLineRoi, image_plus, [batch_qc._java["Measurements"].CENTROID])

	# Gets the width of the image
	Width = image_plus.getWidth()
	# Creates a box roi that is 1 pixel high and the width of the image centred on the line centroid
	BoxRoi = batch_qc._java["Roi"](0, LineCentroid["Y"], Width, 1)

	# Crops the image to the single line
	image_plus.setRoi(BoxRoi)
	LineImage = image_plus.crop("stack")
	# Closes the original image to save memory
	image_plus.close()

	# Runs the reslice command to get the XZ image similar to orthagonal view
	SlicedImp = batch_qc._java["Slicer"]().reslice(LineImage)

	# Performs gaussian blur to smooth the image
	batch_qc._java["IJ"].run(SlicedImp, "Gaussian Blur...", "sigma=6")
	# Gets the statistics which includes the minimum and maximum intensity of the image
	ImpStats = SlicedImp.getStatistics()
	# Sets the prominence for the find maxima command to be half the difference between the min and max intensity
	Prominence = (ImpStats.max - ImpStats.min)/2
	# Finds the maxima in the image and outputs to a results table
	polygon = batch_qc._java["MaximumFinder"]().getMaxima(SlicedImp.getProcessor(), Prominence, False)

	results = pd.DataFrame({"X": polygon.xpoints[:polygon.npoints], "Y": polygon.ypoints[:polygon.npoints]})
	results["AxialStep"] = results["Y"] * float(input_image.scale_z.getValue())
	results = results.sort_values(by="X")
	results = results.reset_index(drop=True)
	results["AxialDiff"] = results["AxialStep"] - results["AxialStep"].shift(1)
	results["AxialDiff"] = results["AxialDiff"].abs()
	results.at[0, "AxialDiff"] = 0
	# Saves the results table
	results.to_csv(os.path.join(OutputPath, f"{FileNameNoExtension}{save_suffix}_XZ.csv"), index=False)

	# Resets the contrast for easier viewing
	SlicedImp.resetDisplayRange()
	# Saves the XZ image and closes to save memory
	batch_qc._java["FileSaver"](SlicedImp).saveAsTiff(os.path.join(OutputPath, f"{FileNameNoExtension}{save_suffix}_XZ.tif"))
	SlicedImp.close()

	# Resets the measurements to the original settings
	AnalyzerClass.setMeasurements(OriginalMeasurements)
