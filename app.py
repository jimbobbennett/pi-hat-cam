"""A Raspberry Pi app to capture video and upload to Azure Blob storageg.

Original code: https://github.com/jimbobbennett/pi-hat-cam

This code is designed to be used in a wearable camera, such as a hat camera. It captures
short bursts of video and uploads them to blob storage, retrying if there are any
connection issues.

The idea is to have a Pi Zero W tethered to a phone continuously uploading, and if signal is lost,
it will keep retrying. The short bursts allow the videos to be upoaded quickly to avoid loss of
videos if the signal is interrupted or the device ggets damaged. Files are named based on the
timestamp of when the recording started.

To use this, you will need an Azure subscription, and a storage account set up.

If you don't have a subscription you can sign up for free:

* If you are a student aged 18 and up and have an email address from an academic institution, you
  can sign up for the free Azure for Students offer at https://aka.ms/FreeStudentAzure without a
  credit card. At the time of writing this gives you $100 of credit to use over 12 months, as
  well as free tiers of a number of services for that 12 months. At the end of the 12 months, if
  you are still a student you can renew and get another $100 in credit and 12 months of
  free services.

* If you are not a student, you can sign up at https://aka.ms/FreeAz. You will need a credit card
  for verification purposes only, you will not be billed unless you decide to upgrade your account
  to a paid offering. At the time of writing the free account will give you US$200 of free credit
  to spend on what you like in the first 30 days, 12 months of free services, plus a load of
  services that have tiers that are always free.

For instructions to set up the storage account, check out the README for this repo at
https://GitHub.com/jimbobbennett/pi-hat-cam

Once you have set up storage, create a .env file with the following values:

BLOB_CONNECTION_STRING=<storage connection string>
CONTAINER_NAME=<blob container name>
VIDEO_LENGTH=<length of the short videos in seconds>
QUALITY=<quality from 1-40>
RESOLUTION=<resolution of videos as w,h>

* BLOB_CONNECTION_STRING needs to be set to the connection string for your storage account.
* CONTAINER_NAME is optional and should be set to the name of the container. If you leave
  this out, the default of videos is used.
* VIDEO_LENGTH is the length in seconds of each short video. This is optional, and if left out
  defaults to 10s.
* QUALITY is the quality of the video, ranging from 1 (highest quality), to 40 (lowest quality).
  The default is 30 which gives reasonable videos at about 500KB per 10 seconds at 720p.
* RESOLUTION is the resolution of the videos to capture. This needs to be in a supported video
  resolution for the camera. You can see the different resolutions supported in the Raspberry
  Pi Camera docs - https://www.raspberrypi.org/documentation/hardware/camera/. This should be as
  w,h for example 1280,720 for 720p resolution. The default is 720p
"""

import asyncio
import os
import datetime
import logging
from typing import Awaitable, NoReturn
from picamera import PiCamera
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import psutil
from retry import retry

# Load the environment variables
load_dotenv()
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "videos")
VIDEO_LENGTH = int(os.getenv("VIDEO_LENGTH", "10"))
QUALITY = int(os.getenv("QUALITY", "30"))
RESOLUTION = os.getenv("RESOLUTION", "1280,720")

# Set up some contstants for saving files
VIDEO_FOLDER = "./videos"
FILE_FORMAT = ".h264"
GENERATOR_FILE_NAME = VIDEO_FOLDER + "/%d" + FILE_FORMAT

# Connect to the Azure blob service
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)

# Check if the container exists and create if it doesn't
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

try:
    print("Checking container", CONTAINER_NAME)
    container_properties = container_client.get_container_properties()
# pylint: disable=W0702
except:
    # Container does not exist, so create it.
    print("Creating container", CONTAINER_NAME, "...")
    container_client.create_container()
    print("Container", CONTAINER_NAME, "created!")

# Create the video ouput folder
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

# Connect to the camera
camera = PiCamera()

# Set the resolution
resolution_parts = RESOLUTION.split(",")
print("Setting camera resolution to", resolution_parts[0], ",", resolution_parts[1])
camera.resolution = (int(resolution_parts[0]), int(resolution_parts[1]))

# Rotate the camera - the cable for the PiCam comes in the bottom, so to mount on
# a hat the cable needs to be at the top, meaning the camera is upside down
camera.rotation = 180

@retry(delay=1, backoff=2, max_delay=64)
def upload_file(filename: str) -> None:
    """Uploads a file with the given name to Azure Blob Storage

    This is set to retry if it fails, such as if internet access is lost. The retry
    happens after 1 second, with a doubling backoff maxing at 64 seconds.
    This means the retries happen after 1 second, 2, 4, 8, 16, 32, 64, 64, 64 etc.

    :param str filename: The name of the file on disk to upload
    """
    # Build the blob upload filename by removing the source folder
    blob_filename = filename.split("/")[-1]

    # Create a blob in the storage account
    print("Uploading", filename, "to", blob_filename)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME,
                                                      blob=blob_filename)

    # Read the file off disk and write it to the blob
    with open(filename, "rb") as data:
        blob_client.upload_blob(data)

    # Delete the file from disk
    print("Deleting", filename)
    os.remove(filename)

async def queue_worker(queue: asyncio.Queue) -> Awaitable[NoReturn]:
    """Uploads files from a queue of file names.

    Each filename is pulled from the queue, the file is uploaded to blob storage, then
    the file is deleted.

    :param asyncio.Queue queue: The queue to pull file names from
    """
    # Process items off the queue
    print("Starting queue worker")
    while True:
        try:
            # Get the next item of the queue, waiting till items are there if the
            # queue is empty
            filename = await queue.get()

            # Upload the file
            upload_file(filename)

        # pylint: disable=W0703
        except Exception as error:
            print(error)

async def wait_recording() -> Awaitable[None]:
    """Runs the camera.wait_recording function asynchronously
    """
    # Wait for the camera to record the short video
    await asyncio.get_event_loop().run_in_executor(None, camera.wait_recording, VIDEO_LENGTH)

def datetime_generator():
    """Generator returning a filename using the current date time.
    This is used to name the videos based off the current time stamp
    """
    while True:
        # Yield a file name using the current date and time
        yield datetime.datetime.now().strftime(VIDEO_FOLDER + "/%Y-%m-%d %H:%M:%S" + FILE_FORMAT)

async def video_capture(queue: asyncio.Queue) -> Awaitable[None]:
    """Continuously captures short videos from the Pi camera.
    These videos are created with a date/time based file names. Once recorded, the filenane
    is added to the queue to upload.

    After each file upload, the remaining disk space is checked, and if there isn't enough
    left, the function ends.

    :param asyncio.Queue queue: The queue to pull file names from
    """
    # Start the recoreding sequence using datetime-based file names
    for filename in camera.record_sequence(datetime_generator(),
                                           quality=QUALITY):

        # Wait for the short video to record
        print("Recording", filename)
        await wait_recording()

        # Get the file size and free space on disk
        file_size = os.path.getsize(filename)
        free_space = psutil.disk_usage(".").free

        # Queue the file for upload
        print("Queuing", filename)
        await queue.put(filename)

        # Verify we have enough disk space left, breaking out if we don't
        if free_space - (file_size * 2) < 0:
            print("No free space")
            break

async def main_loop() -> Awaitable[NoReturn]:
    """Main loop - sleeps in a loop to keep the event loop running
    """
    while True:
        # Sleep 😴
        await asyncio.sleep(1)

async def main() -> Awaitable[None]:
    """The main function.

    This creates the upload queue, adding any existing files from a previous run. It then
    starts the video capture and queue uploader functions
    """
    # Create the queue
    queue = asyncio.Queue()

    # Check for existing files, adding them to the queue if any are found
    filelist = [file for file in os.listdir(VIDEO_FOLDER) if file.endswith(FILE_FORMAT)]
    for file in filelist:
        await queue.put(VIDEO_FOLDER + "/" + file)

    # Start the video capture and queue uploader functions
    listeners = asyncio.gather(queue_worker(queue), video_capture(queue))

    # Start the main loop
    await main_loop()

    # Cancel everything when done
    listeners.cancel()

# Create a logger - the retry annotation logs errors
logging.basicConfig()

# Run the main function
asyncio.run(main())
