import os 
import base64
from dotenv import load_dotenv
import tempfile

# Load environment variables from .env file
load_dotenv()

URL = os.getenv("URL", "https://hq.qashier.com/#/login")    
URL_CUST_MAGEMENT = os.getenv("URL_CUST_MAGEMENT", "https://hq.qashier.com/#/customer-management") 

# Create Windows-compatible paths
TEMP_DIR = tempfile.gettempdir()
DOWNLOAD_FOLDER = os.path.join(TEMP_DIR, "browserdownload2")
PATH_TO_GOOGLE_KEY = os.path.join(TEMP_DIR, "service_account.json")
SCREENSHOT_FOLDER = os.path.join(TEMP_DIR, "browserscreenshots")

# Create necessary directories if they don't exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

HEADLESS = True 

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1ECYWdaDaM7dFAuQVEBFnba93WGuNMA5mqczawIIMB98") 
FILE_NAME_PREFIX = os.getenv("FILE_NAME_PREFIX", "LENGOLF_SALES_POS")  

DEBUG = os.getenv("DEBUG", False)

try:
    # Get encoded values from .env file
    APP_LOGIN_ENCODED = os.getenv("APP_LOGIN")
    APP_PASSWORD_ENCODED = os.getenv("APP_PASSWORD")
    GOOGLE_KEY = os.getenv("GOOGLE_KEY")

    if not (APP_LOGIN_ENCODED and APP_PASSWORD_ENCODED and GOOGLE_KEY):
        print("APP_LOGIN, APP_PASSWORD, GOOGLE_KEY is not specified in .env file. Exit")
        exit(1)

    # Decode the values
    APP_LOGIN = base64.b64decode(APP_LOGIN_ENCODED).decode('utf-8')
    APP_PASSWORD = base64.b64decode(APP_PASSWORD_ENCODED).decode('utf-8')
    decoded = base64.b64decode(GOOGLE_KEY).decode('utf-8')

    with open(PATH_TO_GOOGLE_KEY, "wt") as f:
        f.write(decoded)
        print(f"Key decoded and placed in {PATH_TO_GOOGLE_KEY}")

except Exception as ex:
    print("ERROR during parsing ENV variables. Make sure APP_LOGIN, APP_PASSWORD, GOOGLE_KEY are specified in correct format in .env file")
    exit(1)
    raise ex
   
