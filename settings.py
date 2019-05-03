import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

HST = os.environ.get("HOST_NAME")
USN = os.environ.get("USER_NAME")
PWD = os.environ.get("PASSWORD")
DSN = os.environ.get("DB_NAME")

HOME_DIRECTORY = os.environ.get("HOME_DIRECTORY")
SERVER_HOME_DIRECTORY = os.environ.get("SERVER_HOME_DIRECTORY")

AR_HOME_URL = os.environ.get("AR_HOME_URL")
AP_HOME_URL = os.environ.get("AP_HOME_URL")
GD_HOME_URL = os.environ.get("GD_HOME_URL")
HU_HOME_URL = os.environ.get("HU_HOME_URL")

SAVE_IMAGE_PATH = os.environ.get("SAVE_IMAGE_PATH")
SAVE_IMAGE_PERMALINK_PATH = os.environ.get("SAVE_IMAGE_PERMALINK_PATH")