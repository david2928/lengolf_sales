import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright
from googleapiclient import discovery
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import pandas as pd
import gspread
import openpyxl
import csv
import json
from .settings import *
import re
from zoneinfo import ZoneInfo

# Define the Google Sheets ID
SPREADSHEET_ID = '1ECYWdaDaM7dFAuQVEBFnba93WGuNMA5mqczawIIMB98'

# Set timezone to Bangkok
TIMEZONE = ZoneInfo("Asia/Bangkok")

def get_current_time():
    return datetime.now(TIMEZONE)

def screenshot(filename, page):
    filepath = os.path.join(SCREENSHOT_FOLDER, filename)
    print(f"Saving screenshot to: {filepath}")
    if DEBUG:
        page.screenshot(path=filepath)

def list_download_dir():
    print("List of downloaded csv files locally")
    files = []
    for child in [i for i in Path(DOWNLOAD_FOLDER).iterdir() if ".csv" in str(i)]:
        print(child)
        files.append(child)
    return files

def convert_xlsx_to_csv(xlsx_path, csv_path):
    print(f"Converting {xlsx_path} to {csv_path}")
    workbook = openpyxl.load_workbook(xlsx_path)
    sheet = workbook.active
    with open(csv_path, 'w', newline="", encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in sheet.iter_rows(values_only=True):
            writer.writerow(row)
    print("Conversion done")

def convert_file_to_sheets_data(file_path):
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            print(f"Trying to read file with encoding: {encoding}")
            df_data = pd.read_csv(file_path, encoding=encoding, skiprows=2)  # Skipping the first two rows
            print(f"Data read with shape: {df_data.shape}")
            print(f"Data columns before setting headers: {df_data.columns}")

            # Fill NaN values with empty string
            df_data_cleaned = df_data.fillna('')
            
            # Convert Date column to Bangkok timezone
            if 'Date' in df_data_cleaned.columns:
                print("Converting dates to Bangkok timezone")
                df_data_cleaned['Date'] = pd.to_datetime(df_data_cleaned['Date'])
                df_data_cleaned['Date'] = df_data_cleaned['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok').dt.strftime('%d/%m/%Y %H:%M:%S')
            
            # Add a column with the current timestamp
            current_time = get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            df_data_cleaned['UpdateTime'] = current_time

            # Log date range information
            if 'Date' in df_data_cleaned.columns:
                min_date = df_data_cleaned['Date'].min()
                max_date = df_data_cleaned['Date'].max()
                print(f"Data date range: from {min_date} to {max_date}")
                print(f"Number of unique dates: {df_data_cleaned['Date'].nunique()}")
                print(f"Total rows per date:\n{df_data_cleaned.groupby('Date').size()}")

            # Convert problematic values to strings to prevent JSON serialization issues
            def safe_conversion(x):
                if isinstance(x, (float, bool)):
                    if isinstance(x, float) and (pd.isna(x) or x == float('inf') or x == float('-inf') or abs(x) > 1.7976931348623157e+308):
                        print(f"Converting problematic float value: {x}")
                        return str(x)
                    else:
                        return str(x)
                return x

            for col in df_data_cleaned.columns:
                print(f"Processing column: {col}")
                df_data_cleaned[col] = df_data_cleaned[col].apply(safe_conversion)

            print("File read and cleaned successfully")
            return df_data_cleaned
        except UnicodeDecodeError:
            print(f"Failed to read file with encoding: {encoding}")
        except Exception as ex:
            print(f"An error occurred while reading the file: {ex}")
            raise ex

    raise UnicodeDecodeError(f"None of the specified encodings worked for the file: {file_path}")

def push_to_google_sheets(df_data):
    try:
        # set up credentials
        credentials = service_account.Credentials.from_service_account_file(PATH_TO_GOOGLE_KEY)

        # Use fixed month format YYYY_MM for January 2025
        sheet_name = "2025_01"

        # set up gspread lib
        gc = gspread.service_account(filename=PATH_TO_GOOGLE_KEY)

        # open the Google Sheet
        sheet = gc.open_by_key(SPREADSHEET_ID)

        # check if the worksheet exists, if not create it
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=sheet_name, rows="100", cols="20")

        # clear the worksheet before updating
        worksheet.clear()

        # update the worksheet with the dataframe
        worksheet.update([df_data.columns.values.tolist()] + df_data.values.tolist())
        print(f"Worksheet '{sheet_name}' updated successfully")

    except HttpError as error:
        print(f"An error occurred with the Google Sheets API: {error}")
    except ValueError as ve:
        print(f"Value error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_file():
    print("Getting files from CMS")
    with sync_playwright() as p:
        if DEBUG:
            print(f"HEADLESS = {HEADLESS}")
            print(f"APP_LOGIN = {APP_LOGIN}")
            print(f"APP_PASSWORD = {APP_PASSWORD}")
            print(f"URL = {URL}")
            print(f"URL_CUST_MAGEMENT = {URL_CUST_MAGEMENT}")
            print(f"SCREENSHOT_FOLDER = {SCREENSHOT_FOLDER}")

        # Launch browser in visible mode for debugging
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Opening main page: {URL}")
        page.goto(URL)
        page.wait_for_load_state()
        print(f"Opened main page {page.title()}")

        screenshot(filename="LoginPageBefore.png", page=page)

        page.get_by_label('Username').fill(APP_LOGIN)
        page.get_by_label('Password').fill(APP_PASSWORD)

        print(f"Input log/pass")
        print(f"Pressing LOGIN...")

        screenshot(filename="LoginPageAfter.png", page=page)
        page.get_by_role("button", name="Login").click()
        print(f"Pressed LOGIN")

        page.wait_for_timeout(3000)  # Increased timeout
        page.wait_for_load_state()
        print(f"Login finished")

        # Go to transactions page
        print(f"Opening transactions page")
        page.locator("a").filter(has_text=re.compile(r"^Transactions$")).click()
        page.wait_for_timeout(3000)  # Increased timeout
        page.wait_for_load_state()

        screenshot(filename="TransactionsPage.png", page=page)
        print(f"Opened transactions page")

        # Fixed date selection for 31/1/2025
        print("Clicking date range")
        page.get_by_role("button", name="Sunday 02/02/").click()
        page.wait_for_timeout(2000)

        # Navigate to January
        print("Clicking left chevron to go to January")
        page.locator("button").filter(has_text="chevron_left").nth(1).click()
        page.wait_for_timeout(2000)

        # Select date range
        print("Selecting date range")
        page.get_by_role("button", name="1", exact=True).click()
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="31").click()
        page.wait_for_timeout(1000)

        screenshot(filename="DateRangeSelected.png", page=page)
        print("Date range selected")

        # Click OK to confirm the date range
        print("Clicking OK to confirm date range")
        page.get_by_role("button", name="OK").click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state()

        screenshot(filename="DateRangeConfirmed.png", page=page)
        print("Date range confirmed")

        # Click the EXPORT dropdown button
        print("Clicking EXPORT dropdown")
        page.get_by_label('Expand "Export "').click()
        page.wait_for_timeout(2000)

        screenshot(filename="ExportDropdownClicked.png", page=page)
        print("Export dropdown clicked")

        # Click TRANSACTION DETAILS option
        print("Clicking TRANSACTION DETAILS")
        page.get_by_text("Transaction Details").click()
        page.wait_for_timeout(2000)

        screenshot(filename="TransactionDetailsClicked.png", page=page)
        print("Transaction details clicked")

        # Click CONFIRM in the confirmation dialog
        print("Clicking CONFIRM in dialog")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Confirm").click()
            print("Confirm clicked, waiting for download")
            download = download_info.value

        # Save the downloaded file
        date_folder = "2025_01"  # For January 2025
        download_path = os.path.join(DOWNLOAD_FOLDER, download.suggested_filename)
        download.save_as(download_path)
        print(f"File downloaded to {download_path}")

        # Convert the downloaded XLSX file to CSV
        csv_path = os.path.splitext(download_path)[0] + ".csv"
        convert_xlsx_to_csv(download_path, csv_path)

        # Copy the CSV file to a permanent location with date-based folder
        permanent_location = os.path.join(os.path.expanduser("~"), "Documents", date_folder)
        os.makedirs(permanent_location, exist_ok=True)
        shutil.copy(csv_path, permanent_location)
        print(f"File copied to {permanent_location}")

        browser.close()

def main():
    print("APP START")
    
    get_file()
    files = list_download_dir()
    for i in files:
        body = convert_file_to_sheets_data(i)
        push_to_google_sheets(body)
        
        # Clean up files after processing
        if os.path.exists(i):
            os.remove(i)
            print(f"Cleaned up file: {i}")

    print("APP END")

if __name__ == "__main__":
    main() 