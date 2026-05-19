import json
import sys
sys.path.insert(0, "D:/GitDir/Batch_QC")
import batch_qc
from batch_qc import omero_images, metroloJ_access, z_accuracy
import click
import pathlib
import shutil

DEFAULT_CONFIG_PATH= pathlib.Path(__file__).resolve().parent / ".omero_config"

def False_or_Missing(dict_item, key):
	if key not in dict_item:
		return True
	elif dict_item[key] == False:
		return True
	else:
		return False
	
def clear_empty_directories(path):
	if isinstance(path, str):
		path = pathlib.Path(path)
	for root, dirs, files in path.walk(top_down=False):
		if root != path and not any(path.iterdir()):
			root.rmdir()

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

def main(output_directory, config_path, coreg_name, psf_name, drift_name, z_accuracy_name, thresholding_method, center_dectection_method, save_pdf, save_csv, save_images, clear_local_output, memory):
	with open(config_path, "r") as f:
		config = json.load(f)
	omero_hostname = config["hostname"]
	omero_username = config["username"]
	omero_password = config["password"]
	fiji_path = config["fiji_path"]
	try:
		conn = batch_qc.omero_images.connect(omero_hostname, omero_username, omero_password, keep_alive=60*20)
	except ConnectionError:
		print("Failed to connect to OMERO server. Please check your credentials and connection details.")
		return
	
	if not pathlib.Path(fiji_path).is_dir():
		print(f"Fiji path {fiji_path} is not a directory. Please check the path in the config file.")
		return
	
	print ("Initialising Fiji...")
	try:
		batch_qc.initialise(fiji_path, mode="interactive", memory=memory)
	except RuntimeError as e:
		print(f"Failed to initialise Fiji. Please check the Fiji path and ensure it is correct.")
		return
	print("Fiji initialised successfully.")
	
	to_process = []
	to_method_name = {coreg_name: "registration", psf_name: "psf", drift_name: "drift"}

	for microscope_project in conn.getObjects("Project"):
		project = omero_images.ProjectObject(microscope_project)
		for dataset in project.datasets:
			if dataset.name in [coreg_name, psf_name, drift_name, z_accuracy_name]:
				to_process += [image for image in dataset.images if False_or_Missing(image.key_value_pairs, "QC_Processed")]
	
	print(f"Found {len(to_process)} images to process.")
	print(f"Coregistration: {len([image for image in to_process if image.parent.name == coreg_name])}")
	print(f"PSF: {len([image for image in to_process if image.parent.name == psf_name])}")
	print(f"Drift: {len([image for image in to_process if image.parent.name == drift_name])}")
	print(f"Z-Accuracy: {len([image for image in to_process if image.parent.name == z_accuracy_name])}")

	for image in to_process:
		try:
			conn = batch_qc.omero_images.connect(omero_hostname, omero_username, omero_password, keep_alive=60*20) # Reconnect for each image to avoid timeout issues
			project_name = image.parent.parent.name
			dataset_name = image.parent.name
			image_output_directory = pathlib.Path(output_directory) / project_name / dataset_name / image.name
			image_output_directory.mkdir(parents=True, exist_ok=True)

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
				ex_instance = metroloJ_access.execute_MetroloJ_process(Dialog, str(image_output_directory), image.name)
		
			elif dataset_name == z_accuracy_name:
				method = "z_accuracy"
				print(f"Processing image {image.name} (ID: {image.id}) from microscope {project_name} using z_accuracy method.")
				z_accuracy.run_z_accuracy(image, str(image_output_directory))
			
			print("Attaching results to OMERO...")
			for root, dirs, files in image_output_directory.walk():
				for f in files:
					image.attach_annotation(conn, str(root / f), f"qc.{method}")
			image.add_key_values(conn, {"QC_Processed": "True"}, namespace="QC")

			if clear_local_output:
				print("Clearing local output directory...")
				shutil.rmtree(image_output_directory)
			print(f"Finished processing image {image.name} (ID: {image.id}).")

		except Exception as e:
			print(f"Failed to process image {image.name} (ID: {image.id}) using {method} method in dataset {dataset_name}. Error: {str(e)}")
		finally:
			image.close()

		if clear_local_output:
			clear_empty_directories(output_directory)
	conn.close()

if __name__ == "__main__":
	main()