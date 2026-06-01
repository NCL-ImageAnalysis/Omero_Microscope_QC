import json
import sys
sys.path.insert(0, "D:/GitDir/Batch_QC")
import batch_qc
from batch_qc import metroloJ_access, omero_objects, z_accuracy
import click
import pathlib
import shutil
import Ice
import traceback
import logging

DEFAULT_CONFIG_PATH= pathlib.Path(__file__).resolve().parent / ".omero_config"

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
	for root, dirs, files in path.walk(top_down=False):
		if root != path and not any(path.iterdir()):
			root.rmdir()

def run_analysis(image, output_directory, to_method_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, z_accuracy_name):
	project_name = image.parent.parent.name
	dataset_name = image.parent.name
	image_output_directory = pathlib.Path(output_directory) / project_name / dataset_name / image.name
	image_output_directory.mkdir(parents=True, exist_ok=True)

	if Bool_or_Missing(image.key_value_pairs, "use_rois"):
		if len(image.rois) == 0:
			print(f"Skipping image {image.name} (ID: {image.id}) as marked as using ROIs but no ROIs found.")
			return None, None
		roi_list = image.rois
	else:
		roi_list = [None]

	for roi in roi_list:
		if roi is not None:
			roi.load_tile_data()
			save_suffix = f"_ROI{roi.id}"
		else:
			save_suffix = ""
		if dataset_name in to_method_name:
			method = to_method_name[dataset_name]
			print(f"Processing image {image.name} (ID: {image.id}) from microscope {project_name} using {method} method.")
			print("Loading image data and initialising metroloJ dialog...")
			Dialog = metroloJ_access.initialize_MetroloJDialog(
				method,
				image, 
				thresholding_method=thresholding_method, 
				center_dectection_method=center_dectection_method, 
				save_pdf=save_pdf, 
				save_csv=save_csv, 
				save_images=save_images)
			print("Running metroloJ analysis...")
			ex_instance = metroloJ_access.execute_MetroloJ_process(Dialog, str(image_output_directory), image.name + save_suffix, image.acquisition_date)

		elif dataset_name == z_accuracy_name:
			method = "z_accuracy"
			print(f"Processing image {image.name} (ID: {image.id}) from microscope {project_name} using z_accuracy method.")
			z_accuracy.run_z_accuracy(image, str(image_output_directory), save_suffix=save_suffix)
		return method, image_output_directory

def attach_results(image, output_directory, connection, method, clear_local_output=False):
	print("Attaching results to OMERO...")
	for root, dirs, files in output_directory.walk():
		for f in files:
			image.attach_annotation(connection, str(root / f), f"qc.{method}")
	image.add_key_values(connection, {"QC_Processed": "True"}, namespace="QC")

	if clear_local_output:
		print("Clearing local output directory...")
		shutil.rmtree(output_directory)
	print(f"Finished processing image {image.name} (ID: {image.id}).")

def reconnect_and_reload(image_list, connection_parameters, current_connection=None):
	if current_connection is not None:
		try:
			current_connection.close()
		except Exception:
			pass
	conn = batch_qc.omero_objects.connect(*connection_parameters)
	for image in image_list:
		image.reload(conn)
	return conn

@click.command()
@click.argument("output_directory", type=click.Path(file_okay=False, writable=True), default=".")
@click.option("--config_path", default=DEFAULT_CONFIG_PATH, type=click.Path(exists=True), help="Path to JSON config file containing OMERO connection details and Fiji path.")
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
@click.option("--debug/--no_debug", default=False, help="Whether to run in debug mode, which will print full tracebacks.")

def main(output_directory, config_path, coreg_name, psf_name, drift_name, z_accuracy_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, clear_local_output, memory, debug):
	with open(config_path, "r") as f:
		config = json.load(f)
	omero_hostname = config["hostname"]
	omero_username = config["username"]
	omero_password = config["password"]
	fiji_path = config["fiji_path"]

	if not debug:
		logging.getLogger("omero.gateway").setLevel(logging.CRITICAL)

	conn_params = (omero_hostname, omero_username, omero_password)
	try:
		conn = batch_qc.omero_objects.connect(*conn_params)
	except ConnectionError:
		print("Failed to connect to OMERO server. Please check your credentials and connection details.")
		return
	
	if not pathlib.Path(fiji_path).is_dir():
		print(f"Fiji path {fiji_path} is not a directory. Please check the path in the config file.")
		conn.close()
		return
	
	print ("Initialising Fiji...")
	try:
		batch_qc.initialise(fiji_path, mode="interactive", memory=memory)
	except RuntimeError as e:
		print(f"Failed to initialise Fiji. Please check the Fiji path and ensure it is correct.")
		conn.close()
		return
	print("Fiji initialised successfully.")
	
	to_process = []
	to_method_name = {coreg_name: "registration", psf_name: "psf", drift_name: "drift"}

	for microscope_project in conn.getObjects("Project"):
		project = omero_objects.OmeroObject.from_omero_entity(microscope_project)
		for dataset in project.children:
			if dataset.name in [coreg_name, psf_name, drift_name, z_accuracy_name]:
				to_process += [image for image in dataset.children if not Bool_or_Missing(image.key_value_pairs, "QC_Processed")]
	
	print(f"Found {len(to_process)} images to process.")
	print(f"Coregistration: {len([image for image in to_process if image.parent.name == coreg_name])}")
	print(f"PSF: {len([image for image in to_process if image.parent.name == psf_name])}")
	print(f"Drift: {len([image for image in to_process if image.parent.name == drift_name])}")
	print(f"Z-Accuracy: {len([image for image in to_process if image.parent.name == z_accuracy_name])}")

	for index, image in enumerate(to_process):
		try:
			try:
				method, image_output_directory = run_analysis(image, output_directory, to_method_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, z_accuracy_name)
			except (ConnectionError, Ice.ConnectionLostException):
				print("Connection to OMERO server lost. Attempting to reconnect and retry...")
				conn = reconnect_and_reload(to_process[index:], conn_params, current_connection=conn)
				method, image_output_directory = run_analysis(image, output_directory, to_method_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, z_accuracy_name)
				if method is None:
					image.close()
					continue  # Skip attaching results if analysis was not run due to missing ROIs
			try:
				attach_results(image, image_output_directory, conn, method, clear_local_output=clear_local_output)
			except (ConnectionError, Ice.ConnectionLostException):
				print("Connection to OMERO server lost while attaching results. Attempting to reconnect and retry...")
				conn = reconnect_and_reload(to_process[index:], conn_params, current_connection=conn)
				attach_results(image, image_output_directory, conn, method, clear_local_output=clear_local_output)
		except Exception as e:
			print(f"Failed to process image {image.name} (ID: {image.id}). Error: {str(e)}")
			if debug:
				traceback.print_exc()
		finally:
			image.close()

		if clear_local_output:
			clear_empty_directories(output_directory)
	try:
		conn.close()
	except Exception:
		pass

if __name__ == "__main__":
	main()