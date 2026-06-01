import os
import numpy as np
import xarray
import itertools
import batch_qc

import omero
from omero import gateway
from omero.rtypes import rdouble

def connect(hostname, username, password, *, keep_alive=None, secure=None, port=None):
	"""
	Connect to an OMERO server
	:param hostname: Host name
	:param username: User
	:param password: Password
	:param keep_alive: Keep-alive interval in seconds (None/0 disables)
	:param secure: Whether to use secure connection; None uses BlitzGateway default
	:param port: OMERO server port; None uses BlitzGateway default
	:return: Connected BlitzGateway
	"""
	gateway_kwargs = {"host": hostname}
	if secure is not None:
		gateway_kwargs["secure"] = secure
	if port is not None:
		gateway_kwargs["port"] = int(port)

	conn = gateway.BlitzGateway(username, password, **gateway_kwargs)
	conn.connect()
	if keep_alive:
		conn.c.enableKeepAlive(int(keep_alive))
	try:
		conn.getSession()
	except omero.ClientError:
		conn.close()
		raise ConnectionError("Failed to connect to OMERO server. Please check your credentials and connection details.")
	print (f"Connected to OMERO server at {hostname} as user {username}")
	return conn

def download_annotation_file(annotation_file, output_directory):
	with open(os.path.join(output_directory, annotation_file.getName()), "wb") as f:
		for chunk in annotation_file.getFileInChunks():
			f.write(chunk)

class OmeroObject:
	@classmethod
	def from_omero_entity(cls, omero_entity, parent=None):
		if omero_entity.OMERO_CLASS == "Image":
			return ImageObject(omero_entity, parent=parent)
		else:
			return ParentObject(omero_entity, parent=parent)

	def __init__(self, omero_entity, parent=None):
		self.core = omero_entity
		self.name = omero_entity.getName()
		self.id = omero_entity.getId()
		self.parent = parent
		self.omero_class = omero_entity.OMERO_CLASS
		self.update_annotations()
		
	def attach_annotation(self, conn, annotation_path, ns, mimetype=None, desc=""):
		if mimetype is None:
			extension = os.path.splitext(annotation_path)[1].lower()
			if extension in [".txt"]:
				mimetype = "text/plain"
			elif extension in [".pdf"]:
				mimetype = "application/pdf"
			elif extension in [".png", ".jpg", ".jpeg"]:
				mimetype = "image/" + extension[1:]
			elif extension in [".csv"]:
				mimetype = "text/csv"
			elif extension in [".xls", ".xlsx"]:
				mimetype = "application/vnd.ms-excel"
		new_ann = conn.createFileAnnfromLocalFile(annotation_path, mimetype=mimetype, ns=ns, desc=desc)
		self.core.linkAnnotation(new_ann)
		self.update_annotations()

	def add_key_values(self, conn, key_values, namespace=None):
		key_value_data = [[k, key_values[k]] for k in key_values]
		map_annotation = omero.gateway.MapAnnotationWrapper(conn)
		if namespace is not None:
			map_annotation.setNs(namespace)
		map_annotation.setValue(key_value_data)
		map_annotation.save()
		self.core.linkAnnotation(map_annotation)
		self.update_annotations()

	def update_annotations(self):
		self.annotations = [ann for ann in self.core.listAnnotations()]
		self.file_annotations = [ann for ann in self.annotations if ann.OMERO_TYPE == omero.model.FileAnnotationI]
		self.key_value_pairs = {}
		for ann in self.annotations:
			if ann.OMERO_TYPE == omero.model.MapAnnotationI:
				self.key_value_pairs.update(dict(ann.getValue()))
		if self.parent:
			self.parent.update_annotations()
			if self.parent.key_value_pairs:
				self.key_value_pairs = {**self.parent.key_value_pairs, **self.key_value_pairs}
		for k, v in self.key_value_pairs.items():
			if v == "True":
				self.key_value_pairs[k] = True
			elif v == "False":
				self.key_value_pairs[k] = False
	
	def reload(self, connection):
		self.core = connection.getObject(self.omero_class, self.id)
		if self.children:
			[child.reload(connection) for child in self.children]

class ParentObject(OmeroObject):
	def __init__(self, omero_entity, parent=None):
		super().__init__(omero_entity, parent=parent)
		self.children = [OmeroObject.from_omero_entity(child, parent=self) for child in omero_entity.listChildren()]

class ImageObject(OmeroObject):
	def __init__(self, image, load_data=False, parent=None, reload=False):
		super().__init__(image, parent=parent)
		self.children = None
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
		self.acquisition_date = image.getAcquisitionDate()
		self.objective = image.getObjectiveSettings()
		self.refractive_index = self.objective.getRefractiveIndex()
		self.NA = self.objective.getObjective().getLensNA()
		self.channels = [ChannelObject(ch) for ch in image.getChannels()]
		self.shape = (self.size_t, self.size_c, self.size_z, self.size_y, self.size_x)
		self.rois = [RoiObject(roi, parent=self) for roi in image.getROIs()]
		if not reload:
			self.image_data = None
			self.image_plus = None
		if load_data:
			self.load_image_data()

	def reload(self, connection):
		super().reload(connection)
		self.__init__(self.core, parent=self.parent, reload=True)

	def load_image_data(self, c=None, t=None, z=None, tile=None):
		if c is None:
			c = list(range(self.size_c))
		if t is None:
			t = list(range(self.size_t))
		if z is None:
			z = list(range(self.size_z))
		
		# Using TCZXY order as Omero outputs X before Y. Swapped later
		if tile is None:
			self.image_data = np.zeros((len(t), len(c), len(z), self.size_y, self.size_x))
		else:
			self.image_data = np.zeros((len(t), len(c), len(z), round(tile[3]), round(tile[2])))
		
		all_iterations = list(itertools.product(z, c, t))
		if tile is not None:
			all_iterations = [(z, c, t, tile) for z, c, t in all_iterations]
			pixel_iterator = self.pixels.getTiles(all_iterations)
		else:
			pixel_iterator = self.pixels.getPlanes(all_iterations)
		
		for i, pixel_values in enumerate(pixel_iterator):
			indexes = all_iterations[i]
			self.image_data[indexes[2], indexes[1], indexes[0], :, :] = np.array(pixel_values)
	
		self.image_data = xarray.DataArray(self.image_data, dims=["t", "c", "z", "y", "x"], name=self.name)
		self.shape = self.image_data.shape
	
	def generate_ImagePlus(self):
		if batch_qc._ij is None:
			raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
		if self.image_data is None:
			self.load_image_data()
		image_plus = batch_qc._ij.py.to_imageplus(self.image_data)
		CalibrationObj = batch_qc._java["Calibration"]()
		CalibrationObj.setXUnit(str(self.scale_x.getUnit()))
		CalibrationObj.setYUnit(str(self.scale_y.getUnit()))
		CalibrationObj.pixelWidth = float(self.scale_x.getValue())
		CalibrationObj.pixelHeight = float(self.scale_y.getValue())
		if self.scale_z:
			CalibrationObj.setZUnit(str(self.scale_z.getUnit()))
			CalibrationObj.pixelDepth = float(self.scale_z.getValue())
		image_plus.setCalibration(CalibrationObj)
		self.image_plus = image_plus
		return image_plus
	
	def add_roi(self, conn, x, y, width, height):
		rect = omero.model.RectangleI()
		rect.x = rdouble(x)
		rect.y = rdouble(y)
		rect.width = rdouble(width)
		rect.height = rdouble(height)
		roi = omero.model.RoiI()
		roi.addShape(rect)
		roi.setImage(self.core._obj)
		conn.getUpdateService().saveObject(roi)
		self.rois = [RoiObject(roi, parent=self) for roi in self.core.getROIs()]
		
	def close(self):
		if self.image_plus is not None:
			self.image_plus.close()
		self.image_data = None
		self.image_plus = None
	
class ChannelObject(OmeroObject):
	def __init__(self, channel):
		super().__init__(channel)
		self.emission_wave = channel.getEmissionWave()
		self.excitation_wave = channel.getExcitationWave()
		try:
			self.mode = channel.getLogicalChannel().getMode().value
		except AttributeError:
			self.mode = None
	def attach_annotation(self, *args, **kwargs):
		raise NotImplementedError("Attaching annotations to channels is not supported")

class RoiObject(OmeroObject):
	def __init__(self, roi, parent=None):
		super().__init__(roi, parent=parent)
		self.shape = roi.copyShapes()[0]
		self.X = self.shape.getX().getValue()
		self.Y = self.shape.getY().getValue()
		self.Width = self.shape.getWidth().getValue()
		self.Height = self.shape.getHeight().getValue()
		self.Tile = (round(self.X), round(self.Y), round(self.Width), round(self.Height))
	
	def load_tile_data(self, c=None, t=None, z=None):
		if self.parent is None:
			raise RuntimeError("Roi does not have a parent image to load data from")
		self.parent.load_image_data(c=c, t=t, z=z, tile=self.Tile)