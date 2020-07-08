# Raspberry Pi Hat Cam

A hat/clothing camera app for the Raspberry Pi.

This app requires a Raspberry Pi connected to a Raspberry Pi Camera and WiFi. It continuously records short videos from the camera (by default 10 seconds in length), and uploads these to Azure blob storage.

This method allow resiliancy - if WiFi connection is lost the uploaded will keep retrying. If the device is damaged then everything already uploaded will be secure. Files are stored on the SD card and only deleted after successfully being uploaded, so if there is no internet connection, files can be grabbed off the SD card.

This also allows audit trails - each short video is named with the current timestamp, and Blob storage stores the time the file was uploaded.

This code also includes a utility to download all the blobs and concatenate them into a single video file.

## Set up the application

Before you can run the application, you need an Azure subscription and a storage account.

### Set up your Azure Subscription

* If you are a student aged 18 and up and have an email address from an academic institution, you can sign up for the free Azure for Students offer at [azure.microsoft.com/free/students](https://azure.microsoft.com/free/students/?WT.mc_id=agrohack-github-jabenn) without a credit card. At the time of writing this gives you $100 of credit to use over 12 months, as well as free tiers of a number of services for that 12 months. At the end of the 12 months, if you are still a student you can renew and get another $100 in credit and 12 months of free services.

* If you are not a student, you can sign up at [azure.microsoft.com/free](https://azure.microsoft.com/free/?WT.mc_id=agrohack-github-jabenn). You will need a credit card for verification purposes only, you will not be billed unless you decide to upgrade your account to a paid offering. At the time of writing the free account will give you US$200 of free credit to spend on what you like in the first 30 days, 12 months of free services, plus a load of services that have tiers that are always free.

### Set up the storage account

An Azure storage account is a general purpose account to store data as files, queues, tables or blobs. In this app, each short video is stored as a blob in the storage account.

To create a storagge account:

1. Head to [ms.portal.azure.com/#create/Microsoft.StorageAccount-ARM](https://aka.ms/AA8xjmk) to go straight to the create a new storage resource blade

1. Sign in with your Azure account if necessary

1. Select your Azure subscription

1. For the *Resource group*, select **Create new**. Name the resource group `hatcam` then select **OK**



## Deploy the code

### Deploy the Python code

### Configure the app

## Create the wearable

## Download the video
