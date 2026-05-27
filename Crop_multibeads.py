#@ File (label="Input Image", style="file") InputImage
#@ File (label="Output Directory", style="directory") OutputDirectory

# Python modules
import copy, re, os
from collections import Counter
import csv
import os
# Java modules
from java.lang import Math
# ImageJ modules

from ij import IJ
from ij.gui import ProfilePlot, Plot
from ij.gui import Overlay
from ij.plugin import Duplicator, RoiRotator, RoiScaler
from ij.plugin import Duplicator
from ij.plugin.filter import GaussianBlur
from ij import ImagePlus
from ij import process
from ij.process import ImageStatistics
from ij.measure import Measurements
from ij.measure import Calibration
from ij import WindowManager
from ij.io import FileSaver
from ij.gui import Line
from ij.gui import Overlay
from ij.gui import Roi
from ij.measure import Measurements
from ij.measure import ResultsTable
from ij.plugin import ZProjector
from ij.plugin.filter import Analyzer, AVI_Writer
# Bioformats modules
from loci.plugins import BF
from loci.plugins.in import ImporterOptions

def analyzeParticles(Binary_Image, exclude_on_edge):
	"""Runs analyze particles on the binary image, returning the ROI

	Args:
		Binary_Image (ij.ImagePlus): Segmented binary image

	Returns:
		[PolygonRoi]: Outputted Rois
	"""	

	# Defines analyse particles settings
	# Runs the analyze particles command to get ROI. 
	# Done by adding to the overlay in order to not have ROIManger shown to user
	if exclude_on_edge:
		RoiList = IJ.run(Binary_Image, "Analyze Particles...", "exclude clear add")
	else:
		RoiList = IJ.run(Binary_Image, "Analyze Particles...", "include clear add")
	# Gets the Overlayed ROIs from analyze particles
	Overlayed_Rois = Binary_Image.getOverlay()
	# Takes the overlay and turns it into an array of ROI
	RoiList = Overlayed_Rois.toArray()
	# Removes this overlay to clean up the image
	IJ.run(Binary_Image, "Remove Overlay", "")
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
	RTable = ResultsTable()
	# Initialises an Analyzer object using 
	# the image and the empty results table
	An = Analyzer(Image, RTable)
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
	
def crop_points(img, xy, cropsize, saveto, filename, index):
	img.setRoi(int(xy[0])-(cropsize/2), int(xy[1])-(cropsize/2), cropsize, cropsize)
	out = img.crop("stack")
	CropProject = ZProjector.run(out, "max")
	bg = CropProject.getStatistics().mode
	maxi = CropProject.getStatistics().max
	# Gaussian blur image
	blur = CropProject.getProcessor()
	gb = GaussianBlur()
	gb.blurGaussian(blur, 2.0)
	CropProject.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	IJ.setThreshold(CropProject, bg*5, maxi)
	IJ.run(CropProject, "Convert to Mask", "")
	RoiList = analyzeParticles(CropProject, False)
	if len(RoiList) == 1:
		writer = AVI_Writer()
		outpath = saveto+"\\"+filename+"_"+str(index+1)+".avi"
		writer.writeImage(out, outpath, AVI_Writer.NO_COMPRESSION, 0)

def main(input_image, output_directory, cropsize_um):
	# This section sets the measurements that will be used
	AnalyzerClass = Analyzer()
	# Gets original measurements to reset later
	OriginalMeasurements = AnalyzerClass.getMeasurements()

	# Sets the measurements to be used
	AnalyzerClass.setMeasurements(Measurements.MODE)

	# Gets the needed paths and filenames for input and output
	FileName = input_image.getName()
	FileNameNoExtension = FileName.split(".")[0]
	OutputPath = output_directory.getPath()

	# Imports the image using Bioformats-------------------v
	Options = ImporterOptions()
	Options.setId(input_image.getPath())
	# Ensures that the image is not split into focal planes
	Options.setSplitFocalPlanes(False)
	Options.setAutoscale(True)
	Imp = BF.openImagePlus(Options)[0]
	Projected = ZProjector.run(Imp, "max")
	# calculate desired crop size in pixels
	cropsize_px = int(Projected.getCalibration().getRawX(cropsize_um))
	mask = Projected.duplicate()
	mask.removeScale()
	bg = mask.getStatistics().mode
	maxi = mask.getStatistics().max
	# Gaussian blur image
	blur = mask.getProcessor()
	gb = GaussianBlur()
	gb.blurGaussian(blur, 2.0)
	mask.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	IJ.setThreshold(mask, bg*5, maxi)
	IJ.run(mask, "Convert to Mask", "")
	AnalyzerClass.setMeasurements(Measurements.CENTROID)
	RoiList = analyzeParticles(mask, True)
	#RoiList = IJ.run(mask, "Analyze Particles...", "exclude clear add");
	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]
	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	for ThisRoi in RoiList:
		Centroid = getRoiMeasurements(ThisRoi, mask, CentroidString)
		# Must be a tuple to be hashable in dictionary
		PointList.append(tuple(Centroid))
	for i in range(len(PointList)):
		crop_points(Imp, PointList[i], cropsize_px, OutputPath, FileNameNoExtension, i)

	#--------------------------------------------------------------------^
if __name__ == "__main__":
	main(InputImage, OutputDirectory, 6)
	
# pseudocode

#1MIP
#2gaussian blur radius 2
#3threshold default, mode*5-max
#4set measurement to include centroid
#5analyse particles, exclude on edges
#6Add 6x6 µm square ROI at each position
#7Crop image to each ROI 
# repeat 1-3
# analyse particles, don't exclude on edges
# if >1 particle, dump this image
# save remaining images
