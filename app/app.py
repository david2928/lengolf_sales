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
from settings import *

# Define the Google Sheets ID
SPREADSHEET_ID = '1ECYWdaDaM7dFAuQVEBFnba93WGuNMA5mqczawIIMB98'

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
            
            # Add a column with the current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_data_cleaned['UpdateTime'] = current_time

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

        # get current month in format YYYY_MM
        current_month = datetime.now().strftime('%Y_%m')

        # set up gspread lib
        gc = gspread.service_account(filename=PATH_TO_GOOGLE_KEY)

        # open the Google Sheet
        sheet = gc.open_by_key("1ECYWdaDaM7dFAuQVEBFnba93WGuNMA5mqczawIIMB98")

        # check if the worksheet exists, if not create it
        try:
            worksheet = sheet.worksheet(current_month)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=current_month, rows="100", cols="20")

        # clear the worksheet before updating
        worksheet.clear()

        # update the worksheet with the dataframe
        worksheet.update([df_data.columns.values.tolist()] + df_data.values.tolist())
        print(f"Worksheet '{current_month}' updated successfully")

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

        browser = p.chromium.launch(headless=True)  # Set headless to False
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
        page.locator('button:has-text("Login")').click()
        print(f"Pressed LOGIN")

        page.wait_for_timeout(2000)
        page.wait_for_load_state()
        print(f"Login finished")

        # Go to transactions page
        transactions_url = "https://hq.qashier.com/#/transactions"
        print(f"Opening transactions page: {transactions_url}")
        page.goto(transactions_url)

        page.wait_for_timeout(2000)
        page.wait_for_load_state()

        screenshot(filename="TransactionsPage.png", page=page)
        print(f"Opened transactions page")

        # Get the current day and the previous day
        current_date = datetime.today()
        current_day_text = current_date.strftime('%A %d/%m/')
        current_month_text = current_date.strftime('%B')
        current_day = str(current_date.day)

        print(f"Current day: {current_day_text}")
        print(f"Current month: {current_month_text}")
        print(f"Current day: {current_day}")

        # Select the current day of the month
        print(f"Clicking current day: {current_day_text}")
        page.get_by_role("button", name=current_day_text).click()

        # Select the first day of the current month
        print(f"Clicking first day: 1")
        page.get_by_role("button", name="1", exact=True).click()

        # Select today's date
        print(f"Clicking current day: {current_day}")
        page.get_by_role("button", name=current_day, exact=True).click()

        screenshot(filename="DateRangeSelected.png", page=page)
        print("Date range selected")

        # Click OK to confirm the date range
        print("Clicking OK to confirm date range")
        page.get_by_role("button", name="OK").click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state()

        screenshot(filename="DateRangeConfirmed.png", page=page)
        print("Date range confirmed")

        # Click the correct EXPORT button
        print("Clicking EXPORT")
        page.get_by_role("button", name="Export", exact=True).click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state()

        screenshot(filename="ExportClicked.png", page=page)
        print("Export clicked")

        # Click transaction details and download the file
        print("Clicking transaction details")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="TRANSACTION DETAILS").click()
            print("Transaction details clicked")

        # Save the downloaded file
        download = download_info.value
        download_path = os.path.join(DOWNLOAD_FOLDER, download.suggested_filename)
        download.save_as(download_path)
        print(f"File downloaded to {download_path}")

        # Convert the downloaded XLSX file to CSV
        csv_path = os.path.splitext(download_path)[0] + ".csv"
        convert_xlsx_to_csv(download_path, csv_path)

        # Copy the CSV file to a permanent location
        permanent_location = "C:\\Users\\dgeiermann\\Documents"  # Change to your desired path
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

    print("APP END")

if __name__ == "__main__":
    main()
