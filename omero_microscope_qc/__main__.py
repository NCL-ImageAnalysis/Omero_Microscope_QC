import json
import sys
import os
import omero_microscope_qc
from omero_microscope_qc import metroloJ_access, omero_objects, z_accuracy
import click
import pathlib
import shutil
import Ice
import traceback
import logging

def Bool_or_Missing(dict_item, key):
	if key not in dict_item:
		return False
	if type(dict_item[key]) == bool:
		return dict_item[key]
	else:
		raise ValueError(f"Key '{key}' found in key value pairs but value is of type {type(dict_item[key])} rather than bool.")
	
def clear_empty_directories(path):
	if isinstance(path, str):
		path = pathlib.Path(path)
	for root, dirs, files in os.walk(path, topdown=False):
		rootpath = pathlib.Path(root)
		if rootpath != path and not any(rootpath.iterdir()):
			rootpath.rmdir()

def run_analysis(image, output_directory, method, thresholding_method="Otsu", center_dectection_method="centroid", connection=None, save_pdf=False, save_csv=False, save_images=False):
	"""Run QC analysis on a single image using MetroloJ or z_accuracy methods, depending on the dataset it belongs to, and save the results to the specified output directory.

	Args:
		image (batch_qc.omero_objects.ImageObject): Image to be processed.
		output_directory (str): Path to the directory where output files used as attachments will be saved.
		method (str): The method to use for QC analysis.
		thresholding_method (str): The thresholding method to use. Default is "Otsu". Must be one of "Legacy", "Li", "Minimum", "Otsu".
		center_dectection_method (str): The center detection method to use. Default is "centroid". Must be one of "ellipses", "centroid", "max".
		connection (gateway.BlitzGateway): The connection to the OMERO server. Default is None, but required if ROIs need to be generated for the image.
		save_pdf (bool): Whether to save PDF reports. Default is False.
		save_csv (bool): Whether to save CSV files. Default is False.
		save_images (bool): Whether to save image files. Default is False.

	Raises:
		KeyError: If a required key is missing from the image's key-value pairs.
		ValueError: If the value for a required key is of the wrong type or if connection is needed but not provided

	Returns:
		pathlib.Path: The output directory as a pathlib.Path object.
	"""
	# Generates output directory for image based on project, dataset and image names
	project_name = image.parent.parent.name
	dataset_name = image.parent.name
	image_output_directory = pathlib.Path(output_directory) / project_name / dataset_name / image.name
	image_output_directory.mkdir(parents=True, exist_ok=True)
	# Need a separator at the end of the output directory string for metroloJ
	image_output_directory_str = str(image_output_directory) + os.path.sep

	generate_rois = Bool_or_Missing(image.key_value_pairs, "generate_rois")
	# Only will use/generate rois if it is in one of those two sets of key value pairs
	if Bool_or_Missing(image.key_value_pairs, "use_rois") or generate_rois:
		# Rois are only generated if there are no existing rois
		if len(image.rois) == 0:
			if generate_rois:
				# Need connection to generate ROIs as this requires reloading the image in batches to access the pixel data
				if connection is None:
					raise ValueError("Connection object must be provided to generate ROIs.")
				print(f"Generating ROIs for image {image.name} (ID: {image.id}).")
				# Getting crop size in scaled units from key value pairs
				try:
					crop_size = float(image.key_value_pairs["crop_size"])
				except KeyError:
					raise KeyError("Crop size not found in image key value pairs. Please ensure that the image has a key 'crop_size' with the desired crop size in scaled units as the value.")
				except ValueError:
					raise ValueError("'crop_size' value is not a valid number.")
				# Generates bead ROIs
				image.generate_bead_rois(crop_size, crop_size, connection)
				# Skip if that step failed to generate any ROIs
				if len(image.rois) == 0:
					print(f"Failed to generate ROIs for image {image.name} (ID: {image.id}). Skipping analysis for this image.")
					return None			
			else:
				# Skips analysis if no ROIs found but image is marked as using ROIs
				print(f"Skipping image {image.name} (ID: {image.id}) as marked as using ROIs but no ROIs found.")
				print(f"To generate ROIs for this image, add a key 'generate_rois' with value 'True' to the image key value pairs and ensure there is a key 'crop_size' with the desired crop size in scaled units as the value.")
				return None
		roi_list = image.rois
	else:
		# If not using Rois will return list with None so that at least one round of analysis will be run on the whole image without ROIs
		roi_list = [None]

	# Will still run analysis even if not using ROIs as have list with a None Value in in that case
	for roi in roi_list:
		if roi is not None:
			# Loads in just the roi tile into memory
			roi.load_tile_data()
			# Needed so multiple duplicate outputs don't have the same name if there are multiple ROIs for an image
			save_suffix = f"_ROI{roi.id}"
		else:
			# No suffix needed if processing whole image
			save_suffix = ""
		# Processing with metroloJ
		if method in ["registration", "psf", "drift"]:
			print(f"Processing image {image.name} (ID: {image.id}) from microscope {project_name} using {method} method.")
			print("Loading image data and initialising metroloJ dialog...")
			# Builds the dialog
			Dialog = metroloJ_access.initialize_MetroloJDialog(
				method,
				image, 
				thresholding_method=thresholding_method, 
				center_dectection_method=center_dectection_method, 
				save_pdf=save_pdf, 
				save_csv=save_csv, 
				save_images=save_images)
			print("Running metroloJ analysis...")
			# Runs the actual analysis
			ex_instance = metroloJ_access.execute_MetroloJ_process(Dialog, image_output_directory_str, image.name + save_suffix, image.acquisition_date)
		# Processing with custom z accuracy script
		elif method == "z_accuracy":
			print(f"Processing image {image.name} (ID: {image.id}) from microscope {project_name} using z_accuracy method.")
			z_accuracy.run_z_accuracy(image, image_output_directory_str, save_suffix=save_suffix)
		else:
			raise ValueError(f"Unknown method '{method}'. Method must be one of 'registration', 'psf', 'drift' or 'z_accuracy'.")
	return image_output_directory

def attach_results(image, output_directory, connection, method, clear_local_output=False):
	"""Used to attach all files in a folder to an image in OMERO as annotations

	Args:
		image (batch_qc.omero_objects.ImageObject): The image to which the results will be attached.
		output_directory (str or pathlib.Path): The directory containing the output files.
		connection (gateway.BlitzGateway): The connection to the OMERO server.
		method (str): The method used for processing.
		clear_local_output (bool, optional): Whether to clear the local output directory after processing. Defaults to False.
	"""
	print("Attaching results to OMERO...")
	# Walks through output directory and attaches all files to the image with a tag indicating the method used for processing
	for root, dirs, files in os.walk(output_directory, topdown=False):
		rootpath = pathlib.Path(root)
		for f in files:
			image.attach_annotation(connection, str(rootpath / f), f"qc.{method}")

	# If enabled, will clear the output directory after processing each image to save local storage space
	if clear_local_output:
		print("Clearing local output directory...")
		shutil.rmtree(output_directory)
	print(f"Finished processing image {image.name} (ID: {image.id}).")

def reconnect_and_reload(image_list, connection_parameters, current_connection=None):
	"""Attempts to reconnect to the OMERO server and reloads the given list of images. Should be used in the case of a lost connection to the OMERO server, which can happen if processing takes a long time."

	Args:
		image_list ([batch_qc.omero_objects.ImageObject]): The list of images to reload.
		connection_parameters (tuple): The parameters for connecting to the OMERO server. Should be a tuple in the form (hostname, username, password).
		current_connection (gateway.BlitzGateway, optional): The current OMERO gateway connection. Defaults to None.

	Returns:
		gateway.BlitzGateway: The reconnected OMERO gateway connection.
	"""
	if current_connection is not None:
		try:
			current_connection.close()
		except Exception:
			pass
	conn = omero_objects.connect(*connection_parameters)
	for image in image_list:
		image.reload(conn)
	return conn

@click.command()
@click.argument("output_directory", type=click.Path(file_okay=False, writable=True), default=".")
@click.option("--config_path", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True), required=True, help="Path to JSON config file containing OMERO connection details and Fiji path.")
@click.option("--coreg_name", default="Coregistration", help="Name of datasets containing coregistration images to look for in OMERO.")
@click.option("--psf_name", default="PSF", help="Name of datasets containing PSF images to look for in OMERO.")
@click.option("--drift_name", default="Stage", help="Name of datasets containing drift images to look for in OMERO.")
@click.option("--z_accuracy_name", default="Z-drive", help="Name of datasets containing Z accuracy images to look for in OMERO.")
@click.option("--thresholding_method", default="Otsu", type=click.Choice(["Legacy", "Li", "Minimum", "Otsu"]), help="Thresholding method to use for bead detection in MetroloJ.")
@click.option("--center_dectection_method", default="centroid", type=click.Choice(["ellipses", "centroid", "max"]), help="Method to use for center detection in MetroloJ.")
@click.option("--save_pdf/--no_save_pdf", default=True, help="Whether to save the MetroloJ report as a PDF and attach to OMERO.")
@click.option("--save_csv/--no_save_csv", default=True, help="Whether to save the MetroloJ results as a CSV and attach to OMERO.")
@click.option("--save_images/--no_save_images", default=True, help="Whether to save the MetroloJ output images and attach to OMERO.")
@click.option("--clear_local_output", default=False, is_flag=True, help="Whether to clear the local output directory after processing each image.")
@click.option("--memory", default="6g", type=str, help="Amount of memory to allocate to Fiji (e.g. '6g' for 6 gigabytes).")
@click.option("--debug", default=False, is_flag=True, help="Whether to run in debug mode, which will print full tracebacks.")

def main(output_directory, config_path, coreg_name, psf_name, drift_name, z_accuracy_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, clear_local_output, memory, debug):
	# Gets connection details and Fiji path from config file
	with open(config_path, "r") as f:
		config = json.load(f)
	omero_hostname = config["hostname"]
	omero_username = config["username"]
	omero_password = config["password"]
	fiji_path = config["fiji_path"]
	conn_params = (omero_hostname, omero_username, omero_password)

	# Sets logging level for omero.gateway to CRITICAL to suppress connection lost error messages unless in debug mode, where full tracebacks will be printed
	if not debug:
		logging.getLogger("omero.gateway").setLevel(logging.CRITICAL)

	# Connects to the OMERO server
	try:
		conn = omero_objects.connect(*conn_params)
	except ConnectionError:
		print("Failed to connect to OMERO server. Please check your credentials and connection details.")
		return
	
	# Checks that the Fiji path is a valid directory before attempting to initialise Fiji
	if not pathlib.Path(fiji_path).is_dir():
		print(f"Fiji path {fiji_path} is not a directory. Please check the path in the config file.")
		conn.close()
		return
	
	print ("Initialising Fiji...")
	try:
		omero_microscope_qc.initialise(fiji_path, mode="interactive", memory=memory)
	except RuntimeError as e:
		print(f"Failed to initialise Fiji. Please check the Fiji path and ensure it is correct.")
		conn.close()
		return
	print("Fiji initialised successfully.")
	
	# Dictionary to map dataset names to method names for processing
	to_method_name = {coreg_name: "registration", psf_name: "psf", drift_name: "drift", z_accuracy_name: "z_accuracy"}

	# Searches through all projects and datasets in OMERO to find images that need to be processed.
	# This is based on whether they are in a dataset with an expected name and whether they have already been processed 
	# (indicated by the presence of a key "QC_Processed" in the image key value pairs). 
	# Compiles a list of images to be processed and prints out a summary of how many images were found for each method.
	to_process = []
	for microscope_project in conn.getObjects("Project"):
		project = omero_objects.OmeroObject.from_omero_entity(microscope_project)
		for dataset in project.children:
			if dataset.name in [coreg_name, psf_name, drift_name, z_accuracy_name]:
				to_process += [image for image in dataset.children if not Bool_or_Missing(image.key_value_pairs, "QC_Processed") and not Bool_or_Missing(image.key_value_pairs, "Skip_Analysis")]
	print(f"Found {len(to_process)} images to process.")
	print(f"Coregistration: {len([image for image in to_process if image.parent.name == coreg_name])}")
	print(f"PSF: {len([image for image in to_process if image.parent.name == psf_name])}")
	print(f"Drift: {len([image for image in to_process if image.parent.name == drift_name])}")
	print(f"Z-Accuracy: {len([image for image in to_process if image.parent.name == z_accuracy_name])}")

	for index, image in enumerate(to_process):
		try:
			# Gets method string needed for processing based on the dataset the image belongs to
			method = to_method_name[image.parent.name]
			# This try except is in case connection has been lost to the OMERO server
			# This often happens when processing the previous image took a long time
			try:
				image_output_directory = run_analysis(image, 
										  output_directory, 
										  method, 
										  thresholding_method=thresholding_method, 
										  center_dectection_method=center_dectection_method, 
										  connection=conn, 
										  save_pdf=save_pdf, 
										  save_csv=save_csv, 
										  save_images=save_images)
			except (ConnectionError, Ice.ConnectionLostException):
				print("Connection to OMERO server lost. Attempting to reconnect and retry...")
				conn = reconnect_and_reload(to_process[index:], conn_params, current_connection=conn)
				image_output_directory = run_analysis(image, 
										  output_directory, 
										  method, 
										  thresholding_method=thresholding_method, 
										  center_dectection_method=center_dectection_method, 
										  connection=conn, 
										  save_pdf=save_pdf, 
										  save_csv=save_csv, 
										  save_images=save_images)
			if image_output_directory is None:
				image.close()
				continue  # Skip attaching results if analysis was not completed successfully
			# This try except is in case connection has been lost to the OMERO server
			# This often happens when the processing of this image took a long time
			try:
				attach_results(image, image_output_directory, conn, method, clear_local_output=clear_local_output)
				# Marks the image as being successfully processed
				image.add_key_values(conn, {"QC_Processed": "True"}, namespace="QC")
			except (ConnectionError, Ice.ConnectionLostException):
				print("Connection to OMERO server lost while attaching results. Attempting to reconnect and retry...")
				conn = reconnect_and_reload(to_process[index:], conn_params, current_connection=conn)
				attach_results(image, image_output_directory, conn, method, clear_local_output=clear_local_output)
				# Marks the image as being successfully processed
				image.add_key_values(conn, {"QC_Processed": "True"}, namespace="QC")
		# If any error occurs during processing or attaching results for an image, it will be caught here and printed out, 
		# but the script will continue to the next image rather than stopping completely. 
		except Exception as e:
			print(f"Failed to process image {image.name} (ID: {image.id}). Error: {str(e)}")
			# Only prints out full traceback when in debug mode
			if debug:
				traceback.print_exc()
		# Ensures that the image is closed after processing to free up memory, even if an error occurs
		finally:
			image.close()

		# Clears empty directories in the output that may have been cleared by clear_local_output
		if clear_local_output:
			clear_empty_directories(output_directory)
	
	# ImageJ has a tendency to keep running causing script to never terminate properly
	# This will basically escilate up options for quitting ImageJ and the script, starting with the normal dispose method, then sys.exit() and finally os._exit() if needed to force quit without cleanup.
	try:
		print("All images processed. Closing connection to OMERO server.")
		conn.close()
		omero_microscope_qc._ij.dispose()
		sys.exit(0)
		os._exit(0)
	except Exception:
		pass

if __name__ == "__main__":
	main()
