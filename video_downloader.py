"""Helper code to download and assemble all the videos uploaded to blob storage.

Original code: https://github.com/jimbobbennett/pi-hat-cam

The blobs are downloaded, then concatenated together in the order they were created,
giving one final video with a name that defaults to downloaded_video.h264 unless a
new file name is given in the .env file.

This file requires a .env file with the following values:

BLOB_CONNECTION_STRING=<storage connection string>
CONTAINER_NAME=<blob container name>
DOWNLOADED_VIDEO_NAME=>file name for the downloaded video>

* BLOB_CONNECTION_STRING needs to be set to the connection string for your storage account.
* CONTAINER_NAME needs to be the name of an existing container containing the blobs.
* DOWNLOADED_VIDEO_NAME is optional and is the filename for the downloaded video. If this is
  not set if defaults to downloaded_video.h264
"""
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load the environment variables
load_dotenv()
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
DOWNLOADED_VIDEO_NAME = os.getenv("DOWNLOADED_VIDEO_NAME", "downloaded_video.h264")

# Connect to the Azure blob service
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)

# Get the container
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# get all the blob names
blob_names = []

blob_list = container_client.list_blobs()
for blob in blob_list:
    blob_names.append(blob.name)

# Sort the blob names alphabetically.
# Seeing as they are named based off the date/time of creation, this puts them all
# in the right order
blob_names.sort()

print(len(blob_names), "blobs to download")

# Open the file to write to
with open(DOWNLOADED_VIDEO_NAME, "wb") as output_file:

    # Loop throuh the blobs
    for blob_name in blob_names:
        print("Downloading", blob_name)
        # Get a blob client for each blob
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME,
                                                          blob=blob_name)

        # Download the blob to the end of the output file
        output_file.write(blob_client.download_blob().readall())

print("Finished!")
