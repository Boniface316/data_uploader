import os

import inquirer
import yaml
from google.cloud import storage

data_directory = "data/"
bucket_name = "areaxo-2024"


def upload_file(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the GCP storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name} in bucket {bucket_name}."
    )


def get_directories(data_directory):
    return [
        f
        for f in os.listdir(data_directory)
        if os.path.isdir(os.path.join(data_directory, f))
    ]


def get_files(chosen_block_directory):
    return [
        f
        for f in os.listdir(chosen_block_directory)
        if os.path.isfile(os.path.join(chosen_block_directory, f))
    ]


def choose_directory(data_directory):
    return inquirer.prompt(
        [
            inquirer.List(
                "trial_name",
                message="Select the trial block you want to upload data for",
                choices=get_directories(data_directory),
            )
        ]
    )


def create_yaml_body():
    trial_name = inquirer.text("Trial Name")
    weather = inquirer.text("Weather")
    location = inquirer.text("Location")
    drone_model = inquirer.text("Drone Model")
    drone_serial = inquirer.text("Drone Serial")
    camera_model = inquirer.text("Camera Model")
    radar_model = inquirer.text("Radar Model")
    software_version = inquirer.text("Software Version")

    body = {
        "trial_name": trial_name,
        "weather": weather,
        "location": location,
        "drone": {
            "model": drone_model,
            "serial": drone_serial,
        },
        "camera": {
            "model": camera_model,
        },
        "radar": {
            "model": radar_model,
            "software_version": software_version,
        },
    }

    return body


def upload_data_block(source_directory, bucket_name):
    block_data = get_files(source_directory)

    for individual_block_data in block_data:
        if not individual_block_data.endswith(".block"):
            continue
        else:
            if not inquirer.confirm(
                "To your best of your knowledge, are these results acceptable?",
                default=False,
            ):
                print(
                    f"Delete {individual_block_data} and and restart the data uploading process"
                )
                break

            context_file_name = os.path.join(source_directory, "trail_details.yaml")
            yaml_body = create_yaml_body()
            with open(context_file_name, "w") as file:
                yaml.dump(yaml_body, file, default_flow_style=False)

            context_blob_name = f"{source_directory}/trail_details.yaml"
            upload_file(bucket_name, context_file_name, context_blob_name)
            source_file_name = os.path.join(source_directory, individual_block_data)
            destination_blob_name = f"{source_directory}/{individual_block_data}"
            upload_file(bucket_name, source_file_name, destination_blob_name)


def upload_metadata(source_directory, bucket_name):
    if not inquirer.confirm(
        "Did you take the pictures of the aerial view?", default=False
    ):
        print("Please take the pictures and restart the data uploading process")
        return

    if not inquirer.confirm("Drone software version is up to date?", default=False):
        print(
            "Please update the software version and restart the data uploading process"
        )
        return

    source_directory = os.path.join(source_directory, "meta_data")
    meta_data_list = get_files(source_directory)

    for individual_meta_data in meta_data_list:
        source_file_name = os.path.join(source_directory, individual_meta_data)
        destination_blob_name = f"{source_directory}/{individual_meta_data}"
        upload_file(bucket_name, source_file_name, destination_blob_name)


def upload_files(data_directory, bucket_name):
    chosen_block_directory = choose_directory(data_directory)["trial_name"]
    source_directory = os.path.join(data_directory, chosen_block_directory)
    upload_data_block(source_directory, bucket_name)
    upload_metadata(source_directory, bucket_name)


upload_files(data_directory, bucket_name)
