import os
import numpy as np
import xarray
import itertools
import scyjava

from omero import gateway

def connect(hostname, username, password):
    """
    Connect to an OMERO server
    :param hostname: Host name
    :param username: User
    :param password: Password
    :return: Connected BlitzGateway
    """
    conn = gateway.BlitzGateway(username, password,
                        host=hostname, secure=True, port=4063)
    conn.connect()
    conn.c.enableKeepAlive(60)
    return conn


def disconnect(conn):
    """
    Disconnect from an OMERO server
    :param conn: The BlitzGateway
    """
    conn.close()

def download_annotation_file(annotation_file, output_directory):
	with open(os.path.join(output_directory, annotation_file.getName()), "wb") as f:
		for chunk in annotation_file.getFileInChunks():
			f.write(chunk)

class OmeroObject:
	def __init__(self, omero_entity):
		self.core = omero_entity
		self.name = omero_entity.getName()
		self.id = omero_entity.getId()

	def attach_annotation(self, conn, annotation_path, mimetype, ns, desc=""):
		new_ann = conn.createFileAnnfromLocalFile(annotation_path, mimetype=mimetype, ns=ns, desc=desc)
		self.core.linkAnnotation(new_ann)

class ProjectObject(OmeroObject):
	def __init__(self, project):
		super().__init__(project)
		self.project = project
		self.datasets = [DatasetObject(ds, parent_project=self) for ds in project.listChildren()]

class DatasetObject(OmeroObject):
	def __init__(self, dataset, parent_project=None):
		super().__init__(dataset)
		self.project = parent_project
		self.dataset = dataset
		self.images = [ImageObject(img) for img in dataset.listChildren()]

class ImageObject(OmeroObject):
	def __init__(self, image, load_data=False):
		super().__init__(image)
		self.size_x = image.getSizeX()
		self.size_y = image.getSizeY()
		self.size_z = image.getSizeZ()
		self.size_c = image.getSizeC()
		self.size_t = image.getSizeT()
		self.pixels = image.getPrimaryPixels()
		self.scale_x = self.pixels.getPhysicalSizeX()
		self.scale_y = self.pixels.getPhysicalSizeY()
		self.scale_z = self.pixels.getPhysicalSizeZ()
		self.dim_order = "TCZYX"
		self.objective = image.getObjectiveSettings()
		self.refractive_index = self.objective.getRefractiveIndex()
		self.NA = self.objective.getObjective().getLensNA()
		self.channels = [ChannelObject(ch) for ch in image.getChannels()]
		self.shape = (self.size_t, self.size_c, self.size_z, self.size_y, self.size_x)
		self.image_data = None
		if load_data:
			self.load_image_data()

	def load_plane(self, c, t, z):
		self.image_data[t, c, z, :, :] = np.array(self.pixels.getPlane(z, c, t))

	def load_image_data(self, c=None, t=None, z=None):
		if c is None:
			c = list(range(self.size_c))
		if t is None:
			t = list(range(self.size_t))
		if z is None:
			z = list(range(self.size_z))

		self.image_data = np.zeros((len(t), len(c), len(z), self.size_y, self.size_x))
		all_iterations = list(itertools.product(c, t, z))
		for args in all_iterations:
			self.load_plane(*args)
		self.image_data = xarray.DataArray(self.image_data, dims=["t", "ch", "pln", "row", "col"], name=self.name)
		self.shape = self.image_data.shape
	
	def generate_ImagePlus(self):
		if self.image_data is None:
			self.load_image_data()
		image_plus = ij.py.to_imageplus(self.image_data)
		CalibrationObj = Calibration()
		CalibrationObj.setXUnit(str(self.scale_x.getUnit()))
		CalibrationObj.setYUnit(str(self.scale_y.getUnit()))
		CalibrationObj.setZUnit(str(self.scale_z.getUnit()))
		CalibrationObj.pixelWidth = float(self.scale_x.getValue())
		CalibrationObj.pixelHeight = float(self.scale_y.getValue())
		CalibrationObj.pixelDepth = float(self.scale_z.getValue())
		image_plus.setCalibration(CalibrationObj)
		self.image_plus = image_plus
		return image_plus
	
class ChannelObject(OmeroObject):
	def __init__(self, channel):
		super().__init__(channel)
		self.emission_wave = channel.getEmissionWave()
		self.excitation_wave = channel.getExcitationWave()
		try:
			self.mode = channel.getLogicalChannel().getMode().value
		except AttributeError:
			self.mode = None
	def attach_annotation(*args, **kwargs):
		raise NotImplementedError("Attaching annotations to channels is not supported")