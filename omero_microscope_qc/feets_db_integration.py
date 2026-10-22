import os
import re
import click
from omero_microscope_qc import omero_objects
from omero_microscope_qc.omero_objects import OmeroObject, Bool_or_Missing
import json
import logging
import traceback
from datetime import datetime

_NS_TO_FOLDER = {
	"qc.registration" : "Coregistration",
	"qc.psf" : "PSF",
	"qc.drift" : "Stage",
	"qc.z_accuracy" : "z-drive",
	"qc.detector" : "Detector"
}

_REGEX_OBJ = re.compile(r".*_results\.(csv|txt|xls)$")

def get_folder_from_namespace(image):
	unique_namespaces = set([attachment.getNs() for attachment in image.file_annotations if attachment.getNs() in _NS_TO_FOLDER])
	if len(unique_namespaces) > 1:
		raise ValueError("Image has multiple file annotations with different namespaces.")
	if len(unique_namespaces) == 0:
		return None
	return _NS_TO_FOLDER[unique_namespaces.pop()]

def download_file_attachments(image, output_dir):
	success = False
	for attachment in image.file_annotations:
		try:
			if _NS_TO_FOLDER.get(attachment.getNs()) == image.folder and _REGEX_OBJ.match(attachment.getFileName()):
				omero_objects.download_annotation_file(attachment, output_dir, name_prefix=f"{image.name}_")
				logging.info(f"Downloaded file attachment {image.name}_{attachment.getFileName()} (ID: {attachment.getId()}) for image {image.name} (ID: {image.id})")
				success = True
		except Exception as e:
			logging.error(f"Failed to download file attachment {attachment.getFileName()} (ID: {attachment.getId()}) for image {image.name} (ID: {image.id}): {e}")
			logging.error(traceback.format_exc())
	return success

def process_image(image, output_directory, id_mapping):
	try:
		microscope_index = image.key_value_pairs["microscope_id"]
	except KeyError:
		logging.debug(f"Image {image.name} (ID: {image.id}) is missing the key-value pair 'microscope_id'")
		return
	try:
		microscope_folder = id_mapping[microscope_index] 
	except KeyError:
		logging.error(f"Microscope ID {image.key_value_pairs['microscope_id']} for image {image.name} (ID: {image.id}) not found in output directory.")
		return
	try:
		acquisition_date = image.acquisition_date.strftime("%Y-%m-%d")
	except AttributeError as e:
		logging.error(f"Image {image.name} (ID: {image.id}) is missing the 'acquisition_date' attribute.")
		return
	output_dir = os.path.join(output_directory, microscope_folder, image.folder, acquisition_date)
	os.makedirs(output_dir, exist_ok=True)
	
	logging.info(f"Downloading file attachments for image {image.name} (ID: {image.id}) to {output_dir}")
	success = download_file_attachments(image, output_dir)
	return success
	

@click.command()
@click.argument("output_directory", type=click.Path(file_okay=False, writable=True, resolve_path=True), default=".")
@click.option("--config_path", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True), required=True, help="Path to JSON config file containing OMERO connection details.")
@click.option("--log_level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), help="Set the logging level for the script. Default is 'INFO'.")
@click.option("--log_files", default=None, type=click.Path(dir_okay=True, file_okay=True, writable=True, resolve_path=True), help="Path to a log file to write logs to. If a directory is provided, a new log file will be created in that directory with a timestamp. If not provided, logs will be printed to the console. Default is None.")

def main(output_directory, config_path, log_level, log_files):
	"""Download processed QC results from OMERO into a FEETS database directory.

	Finds images that have been QC processed but not yet imported into feets-db, and downloads
	their results files into OUTPUT_DIRECTORY, sorted into folders by microscope, QC type
	and acquisition date. OUTPUT_DIRECTORY must contain one folder per microscope, named
	starting with the microscope ID followed by an underscore. Successfully downloaded
	images are marked in OMERO with the key value pair 'Feets_Imported: True'.
	"""
	handlers = []
	if log_files:
		if os.path.isdir(log_files):
			log_files = os.path.join(log_files, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
		handlers.append(logging.FileHandler(log_files))
	
	logging.basicConfig(level=getattr(logging, log_level), handlers=handlers, format='%(asctime)s - %(levelname)s - %(message)s')

	# Gets connection details and Fiji path from config file
	with open(config_path, "r") as f:
		config = json.load(f)
	omero_hostname = config["hostname"]
	omero_username = config["username"]
	omero_password = config["password"]
	omero_group = config.get("group", None)
	conn_params = (omero_hostname, omero_username, omero_password)

	# Connects to the OMERO server
	try:
		conn = omero_objects.connect(*conn_params, group=omero_group)
	except ConnectionError as e:
		logging.error(f"Error: {e}")
		return

	needed_kv_pairs = {"QC_Processed": True, 
	                   "Feets_Imported": False,
					   "microscope_id": omero_objects.EXISTS}
	
	to_process = []
	for microscope_project in conn.getObjects("Project"):
		project = OmeroObject.from_omero_entity(microscope_project, matching_kv_pairs=needed_kv_pairs)
		for dataset in project.children:
			for image in dataset.children:
				image.folder = get_folder_from_namespace(image)
				if image.folder is not None:
					to_process.append(image)

	logging.info(f"Found {len(to_process)} images to process.")

	microscope_dirs = os.listdir(output_directory)
	microscope_id_mapping = {dir_name.split("_")[0]: dir_name for dir_name in microscope_dirs}

	for index, image in enumerate(to_process):
		logging.info(f"Processing image {index + 1}/{len(to_process)}: {image.name} (ID: {image.id})")
		try:
			success = process_image(image, output_directory, microscope_id_mapping)
			if success:
				image.add_key_values(conn, {"Feets_Imported": "True"}, namespace="qc.feets")
			logging.info(f"Image {image.name} (ID: {image.id}) processed successfully.")
		except Exception as e:
			logging.error(f"Error processing image {image.name} (ID: {image.id}): {e}")
			logging.error(traceback.format_exc())
	conn.close()
	logging.info("OMERO connection closed.")

if __name__ == "__main__":
	main()