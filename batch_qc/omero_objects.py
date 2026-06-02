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
	"""Downloads annotation file from omero

	Args:
		annotation_file (omero.model.FileAnnotationI): File annotation to download
		output_directory (str): Path to the directory where the annotation file should be downloaded
	"""
	with open(os.path.join(output_directory, annotation_file.getName()), "wb") as f:
		for chunk in annotation_file.getFileInChunks():
			f.write(chunk)

class OmeroObject:
	"""Base class for OMERO objects (images, datasets, projects). Contains common methods for attaching annotations/key value pairs and for reloading the object from the server.
	Should not be initialised directly, use the from_omero_entity class method to create the appropriate object type based on the OMERO entity provided."""
	@classmethod
	def from_omero_entity(cls, omero_entity, parent=None):
		"""Factory method to create the appropriate OmeroObject subclass based on the OMERO entity provided

		Args:
			omero_entity (omero.model.IObject): OMERO entity to create the object from
			parent (OmeroObject, optional): Parent of the object e.g. a dataset or project. Defaults to None.
		"""
		if omero_entity.OMERO_CLASS == "Image":
			return ImageObject(omero_entity, parent=parent)
		else:
			return ParentObject(omero_entity, parent=parent)

	def __init__(self, omero_entity, parent=None):
		"""Initialises the OmeroObject with the given OMERO entity and parent object (if applicable).

		Args:
			omero_entity (omero.model.IObject): OMERO entity to create the object from
			parent (OmeroObject, optional): Parent of the object e.g. a dataset or project. Defaults to None.
		"""
		self.core = omero_entity
		self.name = omero_entity.getName()
		self.id = omero_entity.getId()
		self.parent = parent
		self.omero_class = omero_entity.OMERO_CLASS
		self.update_annotations()
		
	def attach_annotation(self, conn, annotation_path, ns, mimetype=None, desc=""):
		"""Attaches a file annotation to the object

		Args:
			conn (gateway.BlitzGateway): Connected BlitzGateway
			annotation_path (str): Path to the annotation file to attach
			ns (str): Namespace for the annotation
			mimetype (str, optional): MIME type of the annotation file. If None, it will be inferred from the file extension. Defaults to None.
			desc (str, optional): Description of the annotation. Defaults to "".
		"""
		# If mimetype is not provided, infer from file extension
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
		# Creates the file annotation
		new_ann = conn.createFileAnnfromLocalFile(annotation_path, mimetype=mimetype, ns=ns, desc=desc)
		# Links the annotation to the object
		self.core.linkAnnotation(new_ann)
		# Updates the annotations of the object to include the new annotation
		self.update_annotations()

	def add_key_values(self, conn, key_values, namespace=None):
		"""Adds key value pair to the omero object

		Args:
			conn (gateway.BlitzGateway): Connected BlitzGateway
			key_values (dict): Dictionary of key-value pairs to add
			namespace (str, optional): Namespace for the key-value pairs. Defaults to None.
		"""
		# Creates list of two item lists from the key_values dictionary to use for creating the map annotation
		key_value_data = [[k, key_values[k]] for k in key_values]
		map_annotation = omero.gateway.MapAnnotationWrapper(conn)
		if namespace is not None:
			map_annotation.setNs(namespace)
		map_annotation.setValue(key_value_data)
		# Needs to be saved before it can be linked to the object
		map_annotation.save()
		self.core.linkAnnotation(map_annotation)
		# Updates the annotations of the object to include the new annotation
		self.update_annotations()
	
	def remove_key_value(self, conn, key):
		"""Removes a key value pair from the object. Will only work if only one key value pair is present in that annotation currently

		Args:
			conn (gateway.BlitzGateway): Connected BlitzGateway
			key (str): Key of the value to remove

		Raises:
			ValueError: If there are multiple key value pairs in the annotation containing the key, as ability to remove a single key value pair from an annotation is not currently supported
		"""
		for ann in self.annotations:
			if ann.OMERO_TYPE == omero.model.MapAnnotationI:
				ann_dict = dict(ann.getValue())
				if key in ann_dict:
					if len(ann_dict) > 1:
						raise ValueError(f"Map annotation with id {ann.id} contains multiple key value pairs. Cannot remove key value pair without deleting entire annotation.")
					conn.deleteObjects("MapAnnotation", [ann.id])
		# Updates the annotations of the object to include the lack of this annotation
		self.update_annotations()

	def update_annotations(self):
		"Gets all annotations from omero. Key value annotations are converted into a single dictionary with lowest level instances of keys retained"
		self.annotations = [ann for ann in self.core.listAnnotations()]
		# Subset of annotations that are file annotations stored for ease of access when downloading annotations.
		self.file_annotations = [ann for ann in self.annotations if ann.OMERO_TYPE == omero.model.FileAnnotationI]
		# Gets key value pairs from annotations and stores in a dictionary. 
		# If multiple annotations contain the same key, the value from the lowest level instance of the key is retained.
		# This allows for inheritance of key value pairs down the object hierarchy while still allowing for specific overrides at lower levels.
		self.key_value_pairs = {}
		for ann in self.annotations:
			if ann.OMERO_TYPE == omero.model.MapAnnotationI:
				self.key_value_pairs.update(dict(ann.getValue()))
		# Updates parent object if applicable to ensure any changes to key value pairs are reflected in parent and child objects.
		if self.parent:
			self.parent.update_annotations()
			if self.parent.key_value_pairs:
				# Merges parent key value pairs with own key value pairs, with own key value pairs taking precedence in the case of duplicate keys. 
				self.key_value_pairs = {**self.parent.key_value_pairs, **self.key_value_pairs}
		# Converts any string boolean values to actual booleans for ease of use in other functions
		for k, v in self.key_value_pairs.items():
			if v == "True":
				self.key_value_pairs[k] = True
			elif v == "False":
				self.key_value_pairs[k] = False
	
	def reload(self, connection):
		"""Used to reload the object in case of connection loss

		Args:
			connection (gateway.BlitzGateway): Connected BlitzGateway to use for reloading the object
		"""
		self.__init__(connection.getObject(self.omero_class, self.id), parent=self.parent)
		if self.children:
			[child.reload(connection) for child in self.children]

class ParentObject(OmeroObject):
	"Class for OMERO objects that can have child objects e.g. datasets and projects. Contains a list of child objects that are automatically updated when the parent object is reloaded."
	def __init__(self, omero_entity, parent=None):
		"""Initialises the ParentObject with the given OMERO entity and its own parent (if applicable).

		Args:
			omero_entity (omero.model.IObject): OMERO entity to create the object from
			parent (OmeroObject, optional): Parent of the object e.g. a dataset or project. Defaults to None.
		"""
		super().__init__(omero_entity, parent=parent)
		self.children = [OmeroObject.from_omero_entity(child, parent=self) for child in omero_entity.listChildren()]

class ImageObject(OmeroObject):
	"Class for OMERO image objects. Contains methods for loading and managing image data and metadata"
	def __init__(self, image, load_data=False, parent=None, reload=False):
		"""Initialises the ImageObject. Will populate with metadata and, if enabled, load the image into memory

		Args:
			image (omero.model.ImageI): OMERO image entity to create the object from
			load_data (bool, optional): Whether to load the image data into memory. Defaults to False.
			parent (OmeroObject, optional): Parent of the object. Defaults to None.
			reload (bool, optional): Whether to reload the object in case of loss of connection. Defaults to False.
		"""
		super().__init__(image, parent=parent)
		self.children = None
		# Gets axis sizes
		self.size_x = image.getSizeX()
		self.size_y = image.getSizeY()
		self.size_z = image.getSizeZ()
		self.size_c = image.getSizeC()
		self.size_t = image.getSizeT()
		# Omero object where pixel data is stored
		self.pixels = image.getPrimaryPixels()
		# Scaling information
		self.scale_x = self.pixels.getPhysicalSizeX()
		self.scale_y = self.pixels.getPhysicalSizeY()
		self.scale_z = self.pixels.getPhysicalSizeZ()
		# Dimension order is always TCZYX for the image data loaded by this module
		self.dim_order = "TCZYX"
		self.acquisition_date = image.getAcquisitionDate()
		# Used to get objective information for metroloJ
		self.objective = image.getObjectiveSettings()
		# Immersion refractive index
		self.refractive_index = self.objective.getRefractiveIndex()
		self.NA = self.objective.getObjective().getLensNA()
		# Channel information is stored as their own OmeroObjects
		self.channels = [ChannelObject(ch) for ch in image.getChannels()]
		self.shape = (self.size_t, self.size_c, self.size_z, self.size_y, self.size_x)
		# Rois are stored as their own OmeroObjects and linked to the image object as their parent.
		self.rois = [RoiObject(roi, parent=self) for roi in image.getROIs()]
		# If reload is enabled, then the image data will not be set to None so it would not require redownloading
		if not reload:
			self.image_data = None
			self.image_plus = None
		# Image data is not downloaded by default as this can be slow and memory intensive, but can be enabled by setting load_data to True.
		if load_data:
			self.load_image_data()

	def reload(self, connection):
		"Need own implementation of reload so reload param can be passed to __init__ to avoid having to redownload image data"
		super().reload(connection)
		self.__init__(self.core, parent=self.parent, reload=True)

	def load_image_data(self, c=None, t=None, z=None, tile=None):
		"""Loads image data into memory from the OMERO server. Can specify subsets of the data to load by providing channel, time and z-stack indices and/or tile coordinates.

		Args:
				c ([int], optional): List of channel indices to load. Defaults to None.
				t ([int], optional): List of time indices to load. Defaults to None.
				z ([int], optional): List of z-stack indices to load. Defaults to None.
			tile ([tuple], optional): Tile coordinates to load consisting of a tuple of (x, y, width, height). Defaults to None.
		"""
		if c is None:
			c = list(range(self.size_c))
		if t is None:
			t = list(range(self.size_t))
		if z is None:
			z = list(range(self.size_z))

		# Initialises empty array with shape of image data
		if tile is None:
			self.image_data = np.zeros((len(t), len(c), len(z), self.size_y, self.size_x))
		else:
			self.image_data = np.zeros((len(t), len(c), len(z), round(tile[3]), round(tile[2])))
		
		# This gets a list of all combinations of Z, C and T indices to load
		all_iterations = list(itertools.product(z, c, t))
		# If tile exists then will use getTiles
		if tile is not None:
			all_iterations = [(z, c, t, tile) for z, c, t in all_iterations]
			pixel_iterator = self.pixels.getTiles(all_iterations)
		# Otherwise will use getPlanes
		else:
			pixel_iterator = self.pixels.getPlanes(all_iterations)
		# Iterates through the pixel data and fills the image data array with the pixel values. 
		for i, pixel_values in enumerate(pixel_iterator):
			indexes = all_iterations[i]
			self.image_data[indexes[2], indexes[1], indexes[0], :, :] = np.array(pixel_values)
		# Converts the image data to an xarray to store the axis information which is used by pyImageJ
		self.image_data = xarray.DataArray(self.image_data, dims=["t", "c", "z", "y", "x"], name=self.name)
		# Updates the shape to reflect the true shape of the loaded image
		self.shape = self.image_data.shape
	
	def generate_ImagePlus(self):
		"Generates an ImagePlus object from the python image data"
		# Requires ImageJ to be initialised to work
		if batch_qc._ij is None:
			raise RuntimeError("ImageJ has not been initialised. Please call batch_qc.initialise() before use.")
		# If the image data has not been loaded, it will be loaded now.
		if self.image_data is None:
			self.load_image_data()
		# Converts the image to an ImagePlus. This is just a wrapper so does not involve data duplication in memory
		image_plus = batch_qc._ij.py.to_imageplus(self.image_data)
		# Sets the calibration from stored OMERO metadata
		CalibrationObj = batch_qc._java["Calibration"]()
		CalibrationObj.setXUnit(str(self.scale_x.getUnit()))
		CalibrationObj.setYUnit(str(self.scale_y.getUnit()))
		CalibrationObj.pixelWidth = float(self.scale_x.getValue())
		CalibrationObj.pixelHeight = float(self.scale_y.getValue())
		# Only set z scaling if it exists in the original image
		if self.scale_z:
			CalibrationObj.setZUnit(str(self.scale_z.getUnit()))
			CalibrationObj.pixelDepth = float(self.scale_z.getValue())
		image_plus.setCalibration(CalibrationObj)
		self.image_plus = image_plus
		return image_plus
	
	def add_roi(self, conn, x, y, width, height):
		"""Adds an Roi object to the ImageObject and uploads it to OMERO

		Args:
			conn (gateway.BlitzGateway): Connected BlitzGateway to use for uploading the ROI
			x (float): X coordinate of the top left corner of the ROI
			y (float): Y coordinate of the top left corner of the ROI
			width (float): Width of the ROI in pixels
			height (float): Height of the ROI in pixels
		"""
		# Creates a shape object that will be added to the roi
		rect = omero.model.RectangleI()
		# OMERO expects the coords, width and height to be in type omero.rtypes.rdouble
		rect.x = rdouble(x)
		rect.y = rdouble(y)
		rect.width = rdouble(width)
		rect.height = rdouble(height)
		# Actually creates the roi
		roi = omero.model.RoiI()
		# Adds the shape object to the roi
		roi.addShape(rect)
		# Assigns it to the image and saves it to the server
		roi.setImage(self.core._obj)
		conn.getUpdateService().saveObject(roi)
		# Adds the new roi as an RoiObject to the list of rois for the image object
		self.rois = [RoiObject(roi, parent=self) for roi in self.core.getROIs()]

	def generate_bead_rois(self, scaled_width, scaled_height, conn):
		"""In case of multi bead images this can be called to generate a number of roi each containing a single bead. Requires initialised ImageJ

		Args:
			scaled_width (float): Width of each bead ROI in scaled units
			scaled_height (float): Height of each bead ROI in scaled units
			conn (gateway.BlitzGateway): Connected BlitzGateway to use for uploading the ROIs
		"""
		# ImagePlus is required for generating the rois
		if self.image_plus is None:
			self.generate_ImagePlus()
		# Calls the function from imagej_utils
		rois = batch_qc.imagej_utils.get_crop_roi_params(self.image_plus, scaled_width, scaled_height)
		for roi in rois:
			self.add_roi(conn, *roi)
		
	def close(self):
		"Closes the image data and ImagePlus to free up memory."
		if self.image_plus is not None:
			self.image_plus.close()
		self.image_data = None
		self.image_plus = None
	
class ChannelObject(OmeroObject):
	"Class for OMERO channel objects. Contains metadata about the channel such as emission and excitation wavelengths"
	def __init__(self, channel):
		super().__init__(channel)
		self.emission_wave = channel.getEmissionWave()
		self.excitation_wave = channel.getExcitationWave()
		# Mode is not really used as metadata parsing by OMERO often misses it
		try:
			self.mode = channel.getLogicalChannel().getMode().value
		except AttributeError:
			self.mode = None
	def attach_annotation(self, *args, **kwargs):
		raise NotImplementedError("Attaching annotations to channels is not supported")

class RoiObject(OmeroObject):
	"Class for OMERO ROI objects. Contains metadata about the ROI such as its shape and position and a method for loading the image data within the ROI"
	def __init__(self, roi, parent=None):
		"""Used to initialise the RoiObject from an omero.model.RoiI object.

		Args:
			roi (omero.model.RoiI): The OMERO ROI object to initialise from
			parent (ImageObject, optional): The parent image object. Defaults to None.
		"""
		super().__init__(roi, parent=parent)
		self.shape = roi.copyShapes()[0]
		self.X = self.shape.getX().getValue()
		self.Y = self.shape.getY().getValue()
		self.Width = self.shape.getWidth().getValue()
		self.Height = self.shape.getHeight().getValue()
		# Tile is a tuple of the coordinates of the roi in the form (x, y, width, height) that is used for loading the image data within the roi.
		self.Tile = (round(self.X), round(self.Y), round(self.Width), round(self.Height))
	
	def load_tile_data(self, c=None, t=None, z=None):
		"""Used to load just the region selected by the roi into memory. Can specify subsets of the data to load by providing channel, time and z-stack indices.

		Args:
			c ([int], optional): List of channel indices to load. Defaults to None.
			t ([int], optional): List of time indices to load. Defaults to None.
			z ([int], optional): List of z-stack indices to load. Defaults to None.

		Raises:
			RuntimeError: Roi is not attached to a parent image object to load data from
		"""
		if self.parent is None:
			raise RuntimeError("Roi does not have a parent image to load data from")
		self.parent.load_image_data(c=c, t=t, z=z, tile=self.Tile)
		# Need to regenerate the ImagePlus to reflect the loaded tile data
		if self.parent.image_plus is not None:
			self.parent.image_plus.close()
			self.parent.generate_ImagePlus()