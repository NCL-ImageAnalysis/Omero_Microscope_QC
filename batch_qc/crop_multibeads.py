import batch_qc
from batch_qc.imagej_utils import *

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

def main(Imp, scaled_width, scaled_height):
	# calculate desired crop size in pixels
	Calibration = Imp.getCalibration()
	width_px = round(Calibration.getRawX(scaled_width))
	height_px = round(Calibration.getRawY(scaled_height))

	RoiList = getProjectedBeads(Imp)
	# String needed to get the centroid of the ROI
	CentroidString = ["X", "Y"]
	# Gets the centroid of each ROI and adds to a list-------------------v
	PointList = []
	FilteredPointList = []
	NoScale = Imp.crop()
	NoScale.removeScale()
	for ThisRoi in RoiList:
		Centroid_dict = getRoiMeasurements(ThisRoi, NoScale, batch_qc._java["Measurements"].CENTROID)
		goodpoint = crop_points(Imp, [round(Centroid_dict["X"]), round(Centroid_dict["Y"])], width_px, height_px)
		if goodpoint is not None:
			goodpoint += [width_px, height_px]
			FilteredPointList.append(goodpoint)
	NoScale.close()
	return(FilteredPointList)