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

def open_image(input_image):
	# Imports the image using Bioformats-------------------v
	Options = ImporterOptions()
	Options.setId(input_image.getPath())
	# Ensures that the image is not split into focal planes
	Options.setSplitFocalPlanes(False)
	Options.setAutoscale(True)
	Imp = BF.openImagePlus(Options)[0]
	return(Imp)

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
		RoiList = IJ.run(Binary_Image, "Analyze Particles...", "exclude overlay")
	else:
		RoiList = IJ.run(Binary_Image, "Analyze Particles...", "include overlay")
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
	
def crop_points(img, xy, cropsize, cropsize_um):
	img.setRoi(xy[0]-(cropsize/2), xy[1]-(cropsize/2), cropsize, cropsize)
	out = img.crop("stack")
	# check crop is square, not too near the edge
	CropProject = ZProjector.run(out, "max")
	dim = round((CropProject.getStatistics().area**0.5), 0)
	# Gaussian blur image
	blur = CropProject.getProcessor()
	gb = GaussianBlur()
	gb.blurGaussian(blur, 2.0)
	CropProject.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	IJ.setAutoThreshold(CropProject, "Otsu dark")
	IJ.run(CropProject, "Convert to Mask", "")
	RoiList = analyzeParticles(CropProject, False)
	if len(RoiList) == 1 and dim == cropsize_um:
		return(xy)

def write_out_file(img, xy, input_image, output_directory):
	saveto = output_directory.getPath()
	FileName = input_image.getName()
	FileNameNoExtension = FileName.split(".")[0]
	cropsize = xy[len(xy)-1]
	xy = xy[0:(len(xy)-1)]
	for xyi in range(len(xy)):
		img.setRoi(xy[xyi][0]-(cropsize/2), xy[xyi][1]-(cropsize/2), cropsize, cropsize)
		out = img.crop("stack")
		writer = AVI_Writer()
		outpath = saveto+"\\"+FileNameNoExtension +"_"+str(xyi+1)+".avi"
		writer.writeImage(out, outpath, AVI_Writer.NO_COMPRESSION, 0)

def main(Imp, output_directory, cropsize_um):
	AnalyzerClass = Analyzer()
	Projected = ZProjector.run(Imp, "max")
	# calculate desired crop size in pixels
	cropsize_px = int(Projected.getCalibration().getRawX(cropsize_um))
	Projected.removeScale()
	# Gaussian blur image
	blur = Projected.getProcessor()
	gb = GaussianBlur()
	gb.blurGaussian(blur, 2.0)
	Projected.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	IJ.setAutoThreshold(Projected, "Otsu dark")
	IJ.run(Projected, "Convert to Mask", "")
	AnalyzerClass.setMeasurements(Measurements.CENTROID)
	RoiList = analyzeParticles(Projected, True)
	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]
	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	FilteredPointList = []
	for ThisRoi in RoiList:
		Centroid = tuple(getRoiMeasurements(ThisRoi, Projected, CentroidString))
		Centroid = tuple([int(x) if isinstance(x, float) else x for x in Centroid])
		# Must be a tuple to be hashable in dictionary
		PointList.append(Centroid)
	Projected.close()
	for i in range(len(PointList)):
		goodpoint = crop_points(Imp, PointList[i], cropsize_px, cropsize_um)
		if goodpoint is not None:
			FilteredPointList.append(goodpoint)
	FilteredPointList.append(cropsize_px)
	return(FilteredPointList)
	Imp.close()

	#--------------------------------------------------------------------^
picture = open_image(InputImage)

if __name__ == "__main__":
	out = main(picture, OutputDirectory, 15)
	
write_out_file(picture, out, InputImage, OutputDirectory)
