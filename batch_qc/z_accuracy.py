# Python modules
import copy, os
from collections import Counter
import pandas as pd
import networkx as nx
import numpy as np
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

	image_plus = input_image.generate_ImagePlus().duplicate()

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
	RoiList = analyzeParticles(Projected, size_min="10")

	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	for ThisRoi in RoiList:
		Centroid = getRoiMeasurements(ThisRoi, Projected, [batch_qc._java["Measurements"].CENTROID])
		# Must be a tuple to be hashable in dictionary
		PointList.append(tuple([Centroid["X"], Centroid["Y"]]))
	#--------------------------------------------------------------------^

	df = pd.DataFrame(PointList, columns=["X", "Y"])
	df["point"] = df.index

	rows = []

	for index in df.index:
		distance_frame = df.drop(index).copy()
		x1 = df["X"][index]
		y1 = df["Y"][index]
		point1 = df["point"][index]
		distance_frame["Distance"] = np.sqrt(((distance_frame["X"] - x1) ** 2) + ((distance_frame["Y"] - y1) ** 2))
		distance_frame = distance_frame.sort_values(by="Distance")
		# Add two rows: nearest and second nearest, with only coordinate/point columns
		for i in [0, 1]:
			match = distance_frame.iloc[i]
			rows.append({
				"point1": int(point1),
				"x1": x1,
				"y1": y1,
				"point2": int(match["point"]),
				"x2": match["X"],
				"y2": match["Y"]})

	comparison_df = pd.DataFrame(rows)
	comparison_df["angle"] = np.degrees(np.arctan((comparison_df["y1"] - comparison_df["y2"]) / (comparison_df["x1"] - comparison_df["x2"])))
	comparison_df.loc[comparison_df["angle"] >= 180, "angle"] -= 180
	comparison_df["angle"] = comparison_df["angle"].div(10).round(0) * 10
	comparison_df = comparison_df[comparison_df["angle"] == comparison_df["angle"].mode().iloc[0]]
	graph = nx.from_pandas_edgelist(comparison_df, source="point1", target="point2")
	components = [list(c) for c in nx.connected_components(graph)]
	feducial_start = df[df["point"] == components[0][0]].reset_index()
	feducial_end = df[df["point"] == components[0][-1]].reset_index()

	FeducialLine = batch_qc._java["Line"](feducial_start["X"][0], feducial_start["Y"][0], feducial_end["X"][0], feducial_end["Y"][0])
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
	LineCentroid = getRoiMeasurements(RotatedLineRoi, Projected, [batch_qc._java["Measurements"].CENTROID])

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
	results["AxialStep"] = results["Y"] * 0.05
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
