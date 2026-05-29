import batch_qc
from batch_qc.imagej_utils import *
	
def crop_points(img, xy, cropsize, cropsize_um):
	img.setRoi(xy[0]-(cropsize/2), xy[1]-(cropsize/2), cropsize, cropsize)
	out = img.crop("stack")
	# check crop is square, not too near the edge
	CropProject = batch_qc._java["ZProjector"].run(out, "max")
	dim = round((CropProject.getStatistics().area**0.5), 0)
	# Gaussian blur image
	blur = CropProject.getProcessor()
	gb = batch_qc._java["GaussianBlur"]()
	gb.blurGaussian(blur, 2.0)
	CropProject.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	batch_qc._java["IJ"].setAutoThreshold(CropProject, "Otsu dark")
	batch_qc._java["IJ"].run(CropProject, "Convert to Mask", "")
	RoiList = analyzeParticles(CropProject, False)
	if len(RoiList) == 1 and dim == cropsize_um:
		return(xy)

def main(Imp, cropsize_um):
	Projected = batch_qc._java["ZProjector"].run(Imp, "max")
	# calculate desired crop size in pixels
	cropsize_px = int(Projected.getCalibration().getRawX(cropsize_um))
	Projected.removeScale()
	# Gaussian blur image
	blur = Projected.getProcessor()
	gb = batch_qc._java["GaussianBlur"]()
	gb.blurGaussian(blur, 2.0)
	Projected.updateAndDraw()
	# calculate treshold from background
	# Thresholds the image to get the ladder
	batch_qc._java["IJ"].setAutoThreshold(Projected, "Otsu dark")
	batch_qc._java["IJ"].run(Projected, "Convert to Mask", "")
	RoiList = analyzeParticles(Projected)
	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]
	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	FilteredPointList = []
	for ThisRoi in RoiList:
		Centroid_dict = getRoiMeasurements(ThisRoi, Projected, batch_qc._java["Measurements"].CENTROID)
		PointList.append((round(Centroid_dict["X"]), round(Centroid_dict["Y"])))
	Projected.close()
	for i in range(len(PointList)):
		goodpoint = crop_points(Imp, PointList[i], cropsize_px, cropsize_um)
		if goodpoint is not None:
			FilteredPointList.append(goodpoint)
	FilteredPointList.append(cropsize_px)
	return(FilteredPointList)