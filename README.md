# Student Housing Management System for Off-Campus Accommodation in UNN

This is an application to streamline the rental process of students in university environment. Below are the process for running the application.

## Features

- **Listing of available houses**: Students can view available house listings that are around the university campus
- **Virtual Tour**: Each of the houses are vividly described with the aid of images and vidoes
- **Payment Gateway**: Students can:
  - Make payments directly from the site
  - Request a refund in case there was a breach of agreement

## Technology Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript (React) with jQuery for dynamic content rendering
- **Data Storage**: Postgres for persistent notification and event storage

## Setup and Installation
It is assumed that you have already cloned the repo before continuing with the steps below.

**This is the setup for linx/MacOS**
1. To run the application you ensure that your terminal is in the main directory - 'powertron'. **Note: There is also a subdirectory with the name powertron**
2. create a virtual environment using this command - python3 -m venv venv
3. Activate the virtual environment using - source venv/bin/activate
4. Install all the requirements and dependencies using - pip install -r requirements.txt
2. The terminal uses uvicorn to run asynchronously as Django does not support asynchronous programming natively. Run this command to start up the server - **uvicorn Gethired.asgi:application --po
rt 8080 --env-file ../.env --reload --ssl-keyfile ./localhost+1-key.pem --ssl-certfile ./localhost+1.pem**
3. The flask application should be running, if the command does not try using plain 'python' without the 3

**For windows users**
1. step 1-2 remains the same except that the 3 added to the end of the python might not be neccessary, it all depends on the user installation
2. To activate the virtual environment in git bash you use this command - 'source bin/Scripts/activate. If you are using command prompt use this instead - 'venv/Scripts/activate.bat' (assuming your terminal is in the folder containing the venv folder and your virtual environment folder is called venv)