#!/usr/bin/env python3

import base64
import logging
import tempfile
import os
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import config
from utils import (
    get_current_time, 
    calculate_month_navigation, 
    get_date_range_for_month, 
    format_date_for_display,
    split_date_range_by_month
)

logger = logging.getLogger(__name__)

class QashierPOSScraper:
    """Scraper for Qashier POS system using Playwright"""
    
    def __init__(self):
        # Decode base64 encoded credentials
        self.username = base64.b64decode(config.qashier_username).decode('utf-8')
        self.password = base64.b64decode(config.qashier_password).decode('utf-8')
        
        logger.info(f"Qashier credentials decoded successfully")
    
    def scrape_daily_data(self) -> pd.DataFrame:
        """Scrape today's sales data from Qashier POS"""
        today = get_current_time().strftime('%Y-%m-%d')
        
        logger.info(f"Starting to scrape data for date: {today}")
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Login to Qashier
                self._login_to_qashier(page)
                
                # Navigate to transactions page
                self._navigate_to_transactions(page)
                
                # Select today's date range (existing logic)
                self._select_current_day_range(page)
                
                # Export and download data
                sales_data = self._export_and_download_data(page, today)
                
                browser.close()
                logger.info(f"Successfully scraped {len(sales_data)} records")
                
                return pd.DataFrame(sales_data)
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                if 'browser' in locals():
                    browser.close()
                raise

    def scrape_historical_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Scrape historical sales data for a specific date range
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            DataFrame with historical sales data
        """
        logger.info(f"Starting to scrape historical data from {start_date} to {end_date}")
        
        # Split the date range by month for easier processing
        monthly_chunks = split_date_range_by_month(start_date, end_date)
        logger.info(f"Split date range into {len(monthly_chunks)} monthly chunks")
        
        all_sales_data = []
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Login to Qashier
                self._login_to_qashier(page)
                
                # Process each monthly chunk
                for chunk_start, chunk_end in monthly_chunks:
                    logger.info(f"Processing chunk: {chunk_start} to {chunk_end}")
                    
                    try:
                        # Navigate to transactions page (need fresh navigation for each chunk)
                        self._navigate_to_transactions(page)
                        
                        # Select the historical date range
                        self._select_historical_date_range(page, chunk_start, chunk_end)
                        
                        # Export and download data for this chunk
                        chunk_data = self._export_and_download_data(page, chunk_start.strftime('%Y-%m-%d'))
                        
                        all_sales_data.extend(chunk_data)
                        logger.info(f"Successfully scraped {len(chunk_data)} records for {chunk_start} to {chunk_end}")
                        
                        # Add small delay between chunks
                        page.wait_for_timeout(1000)
                        
                    except Exception as chunk_error:
                        logger.error(f"Error processing chunk {chunk_start} to {chunk_end}: {chunk_error}")
                        # Continue with next chunk instead of failing entirely
                        continue
                
                browser.close()
                logger.info(f"Successfully scraped {len(all_sales_data)} total historical records")
                
                return pd.DataFrame(all_sales_data)
                
            except Exception as e:
                logger.error(f"Error during historical scraping: {e}")
                if 'browser' in locals():
                    browser.close()
                raise

    def _login_to_qashier(self, page):
        """Login to Qashier POS system"""
        logger.info("Logging in to Qashier POS...")
        page.goto(config.qashier_base_url)
        page.wait_for_load_state()
        
        page.get_by_label('Username').fill(self.username)
        page.get_by_label('Password').fill(self.password)
        page.locator('button:has-text("Login")').click()
        
        page.wait_for_timeout(2000)
        page.wait_for_load_state()
        logger.info("Successfully logged in")

    def _navigate_to_transactions(self, page):
        """Navigate to the transactions page"""
        logger.info(f"Opening transactions page: {config.qashier_transactions_url}")
        page.goto(config.qashier_transactions_url)
        
        page.wait_for_timeout(2000)
        page.wait_for_load_state()
        logger.info("Opened transactions page")

    def _select_current_day_range(self, page):
        """Select current day date range (existing logic)"""
        # Get the current day in Bangkok time - USING WORKING ORIGINAL LOGIC
        current_date = get_current_time()
        current_day_text = current_date.strftime('%A %d/%m/')
        current_month_text = current_date.strftime('%B')
        current_day = str(current_date.day)

        logger.info(f"Current day: {current_day_text}")
        logger.info(f"Current month: {current_month_text}")
        logger.info(f"Current day: {current_day}")
        logger.info(f"Attempting to select date range: 1-{current_day} {current_month_text}")

        # Take screenshot before date selection
        try:
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path="screenshots/TransactionsPage.png")
            logger.info("Screenshot saved: TransactionsPage.png")
        except:
            pass

        # Select the current day of the month
        logger.info(f"Clicking current day: {current_day_text}")
        page.get_by_role("button", name=current_day_text).click()

        # Select the first day of the current month
        logger.info(f"Clicking first day: 1")
        page.get_by_role("button", name="1", exact=True).click()

        # Select today's date
        logger.info(f"Clicking current day: {current_day}")
        page.get_by_role("button", name=current_day, exact=True).click()

        # Take screenshot after date selection
        try:
            page.screenshot(path="screenshots/DateRangeSelected.png")
            logger.info("Screenshot saved: DateRangeSelected.png")
        except:
            pass

        logger.info("Date range selected")

        # Click OK to confirm the date range
        logger.info("Clicking OK to confirm date range")
        page.get_by_role("button", name="OK").click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state()

        # Take screenshot after date confirmation
        try:
            page.screenshot(path="screenshots/DateRangeConfirmed.png")
            logger.info("Screenshot saved: DateRangeConfirmed.png")
        except:
            pass

        logger.info("Date range confirmed")

    def _select_historical_date_range(self, page, start_date: date, end_date: date):
        """
        Select historical date range by navigating the calendar interface
        
        This handles the complex navigation logic for historical dates:
        1. Start from current date (today)
        2. Navigate to target year/month
        3. Select start and end dates
        """
        current_date = get_current_time().date()
        
        logger.info(f"Selecting historical date range: {start_date} to {end_date}")
        logger.info(f"Current date: {current_date}")
        
        # Calculate navigation needed to reach start_date month
        nav_info = calculate_month_navigation(current_date, start_date)
        logger.info(f"Navigation needed: {nav_info}")
        
        # Take screenshot before date selection
        try:
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path=f"screenshots/BeforeHistorical_{start_date}_{end_date}.png")
            logger.info(f"Screenshot saved: BeforeHistorical_{start_date}_{end_date}.png")
        except:
            pass

        # Click on date picker (assuming it starts with current date)
        current_display = format_date_for_display(current_date)
        logger.info(f"Clicking current date picker: {current_display['day_text']}")
        page.get_by_role("button", name=current_display['day_text']).click()
        
        # Navigate to target year first if needed
        if nav_info['year_diff'] != 0:
            logger.info(f"Navigating {abs(nav_info['year_diff'])} year(s) {'left' if nav_info['year_diff'] < 0 else 'right'}")
            for _ in range(abs(nav_info['year_diff'])):
                if nav_info['year_diff'] < 0:  # Going back in time
                    page.locator("button").filter(has_text="chevron_left").nth(1).click()
                else:  # Going forward in time
                    page.locator("button").filter(has_text="chevron_right").nth(1).click()
                page.wait_for_timeout(500)  # Small delay between clicks
        
        # Navigate to target month (after year navigation)
        # After year navigation, we need to calculate remaining month difference
        if nav_info['year_diff'] != 0:
            # After year navigation, calculate the remaining month difference
            remaining_months = start_date.month - current_date.month
        else:
            remaining_months = nav_info['month_diff']
        
        if remaining_months != 0:
            logger.info(f"Navigating {abs(remaining_months)} month(s) {'left' if remaining_months < 0 else 'right'}")
            for _ in range(abs(remaining_months)):
                if remaining_months < 0:  # Going back in time
                    page.locator("button").filter(has_text="chevron_left").first.click()
                else:  # Going forward in time  
                    page.locator("button").filter(has_text="chevron_right").first.click()
                page.wait_for_timeout(500)  # Small delay between clicks
        
        # Take screenshot after navigation
        try:
            page.screenshot(path=f"screenshots/AfterNavigation_{start_date}_{end_date}.png")
            logger.info(f"Screenshot saved: AfterNavigation_{start_date}_{end_date}.png")
        except:
            pass
        
        # Select start date
        logger.info(f"Selecting start date: {start_date.day}")
        page.get_by_role("button", name=str(start_date.day), exact=True).click()
        
        # If end date is in a different month, navigate to it
        if start_date.month != end_date.month or start_date.year != end_date.year:
            end_nav_info = calculate_month_navigation(start_date, end_date)
            logger.info(f"Navigation needed for end date: {end_nav_info}")
            
            for _ in range(abs(end_nav_info['total_months'])):
                if end_nav_info['total_months'] < 0:
                    page.locator("button").filter(has_text="chevron_left").first.click()
                else:
                    page.locator("button").filter(has_text="chevron_right").first.click()
                page.wait_for_timeout(500)
        
        # Select end date
        logger.info(f"Selecting end date: {end_date.day}")
        page.get_by_role("button", name=str(end_date.day), exact=True).click()
        
        # Take screenshot after date selection
        try:
            page.screenshot(path=f"screenshots/DateRangeSelected_{start_date}_{end_date}.png")
            logger.info(f"Screenshot saved: DateRangeSelected_{start_date}_{end_date}.png")
        except:
            pass

        logger.info(f"Historical date range selected: {start_date} to {end_date}")

        # Click OK to confirm the date range
        logger.info("Clicking OK to confirm historical date range")
        page.get_by_role("button", name="OK").click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state()

        # Take screenshot after date confirmation
        try:
            page.screenshot(path=f"screenshots/DateRangeConfirmed_{start_date}_{end_date}.png")
            logger.info(f"Screenshot saved: DateRangeConfirmed_{start_date}_{end_date}.png")
        except:
            pass

        logger.info("Historical date range confirmed")

    def _export_and_download_data(self, page, date_for_logging: str) -> List[Dict]:
        """Export and download transaction data"""
        # Click the EXPORT dropdown button
        logger.info("Clicking EXPORT dropdown")
        page.locator('button:has-text("Export") i.material-icons:has-text("cloud_download")').click()
        page.wait_for_timeout(2000)

        # Take screenshot after export dropdown
        try:
            page.screenshot(path=f"screenshots/ExportDropdownClicked_{date_for_logging}.png")
            logger.info(f"Screenshot saved: ExportDropdownClicked_{date_for_logging}.png")
        except:
            pass

        logger.info("Export dropdown clicked")

        # Click TRANSACTION DETAILS option
        logger.info("Clicking TRANSACTION DETAILS")
        page.locator('div.q-item__section:has-text("TRANSACTION DETAILS")').click()
        page.wait_for_timeout(2000)

        # Take screenshot after transaction details selection
        try:
            page.screenshot(path=f"screenshots/TransactionDetailsClicked_{date_for_logging}.png")
            logger.info(f"Screenshot saved: TransactionDetailsClicked_{date_for_logging}.png")
        except:
            pass

        logger.info("Transaction details clicked")
        
        # Download and process the file
        with page.expect_download() as download_info:
            page.get_by_role("button", name="CONFIRM").click()
            download = download_info.value
        
        # Process downloaded file
        sales_data = self._process_downloaded_file(download, date_for_logging)
        return sales_data

    def _process_downloaded_file(self, download, date: str) -> List[Dict]:
        """Process the downloaded Excel file and convert to sales data"""
        try:
            # Save the downloaded file to a temporary location
            temp_dir = tempfile.mkdtemp()
            download_path = os.path.join(temp_dir, download.suggested_filename)
            download.save_as(download_path)
            
            logger.info(f"Downloaded file to: {download_path}")
            
            # Convert Excel to CSV and read
            csv_path = os.path.splitext(download_path)[0] + ".csv"
            self._convert_xlsx_to_csv(download_path, csv_path)
            
            # Read CSV file into DataFrame (skip first 2 rows like in original app.py)
            df = pd.read_csv(csv_path, encoding='utf-8', skiprows=2)
            logger.info(f"Read {len(df)} rows from downloaded file")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Fill NaN values with empty string
            df = df.fillna('')
            
            # Convert DataFrame to list of dictionaries for consistency
            sales_data = []
            for _, row in df.iterrows():
                # Parse and convert date from DD/MM/YYYY format to ISO format
                raw_date = str(row.get('Date', date))
                formatted_date = self._convert_date_to_iso(raw_date)
                
                record = {
                    'date': formatted_date,
                    'receipt_number': str(row.get('Receipt No.', '')),
                    'order_number': str(row.get('Order Number', '')),
                    'invoice_no': str(row.get('Invoice No.', '')),
                    'payment_method': str(row.get('Transaction Payment Method', '')),
                    'payment_note': str(row.get('Payment Note', '')),
                    'transaction_note': str(row.get('Transaction Note', '')),
                    'order_type': str(row.get('Order Type', '')),
                    'staff_name': str(row.get('Staff Name', '')),
                    'customer_name': str(row.get('Customer Name', '')),
                    'customer_phone_number': str(row.get('Customer Phone Number', '')),
                    'voided': str(row.get('Voided', '')),
                    'void_reason': str(row.get('Void Reason', '')),
                    'combo_name': str(row.get('Combo Name', '')),
                    'product_name': str(row.get('Transaction Item', '')),
                    'sku_number': str(row.get('SKU Number', '')),
                    'quantity': str(row.get('Transaction Item Quantity', '1')),
                    'item_notes': str(row.get('Transaction Item Notes', '')),
                    'item_discount': str(row.get('Transaction Item Discount', '0')),
                    'amount_before_subsidy': str(row.get('Amount Before Subsidy ฿', '0')),
                    'total_subsidy': str(row.get('Total Subsidy ฿', '0')),
                    'transaction_final_amount': str(row.get('Transaction Item Final Amount (฿)', '0')),
                    'store_name': str(row.get('Store Name', '')),
                    'total_invoice_amount': str(row.get('Total Invoice amount', '0')),
                    'transaction_total_amount': str(row.get('Transaction Total Amount', '0')),
                    'transaction_percentage_discount': str(row.get('Transaction Level Percentage Discount', '0')),
                    'transaction_dollar_discount': str(row.get('Transaction Level Dollar Discount', '0')),
                    'transaction_vat': str(row.get('Transaction Total VAT', '0')),
                    'update_time': get_current_time().strftime('%Y-%m-%d %H:%M:%S')
                }
                sales_data.append(record)
            
            # Clean up temp files
            try:
                os.remove(download_path)
                os.remove(csv_path)
                os.rmdir(temp_dir)
            except:
                pass  # Ignore cleanup errors
            
            return sales_data
            
        except Exception as e:
            logger.error(f"Error processing downloaded file: {e}")
            return []
    
    def _convert_date_to_iso(self, date_str: str) -> str:
        """
        Convert date from DD/MM/YYYY HH:MM:SS format to ISO YYYY-MM-DD HH:MM:SS format
        
        Args:
            date_str: Date string in DD/MM/YYYY HH:MM:SS format
            
        Returns:
            Date string in YYYY-MM-DD HH:MM:SS format
        """
        try:
            if not date_str or date_str == 'nan' or date_str == '':
                return get_current_time().strftime('%Y-%m-%d %H:%M:%S')
                
            # Parse DD/MM/YYYY HH:MM:SS format
            if '/' in date_str:
                # Try to parse as DD/MM/YYYY HH:MM:SS
                try:
                    parsed_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
                    return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Try DD/MM/YYYY format without time
                    try:
                        parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
            
            # If already in ISO format, return as-is
            if '-' in date_str:
                try:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    return date_str
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
            
            # Fallback to current time
            logger.warning(f"Could not parse date '{date_str}', using current time")
            return get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error(f"Error converting date '{date_str}': {e}")
            return get_current_time().strftime('%Y-%m-%d %H:%M:%S')

    def _convert_xlsx_to_csv(self, xlsx_path: str, csv_path: str):
        """Convert XLSX file to CSV"""
        try:
            # Use openpyxl to read Excel file
            import openpyxl
            import csv
            
            workbook = openpyxl.load_workbook(xlsx_path)
            sheet = workbook.active
            
            with open(csv_path, 'w', newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in sheet.iter_rows(values_only=True):
                    writer.writerow(row)
            
            logger.info(f"Converted {xlsx_path} to {csv_path}")
        except Exception as e:
            logger.error(f"Error converting XLSX to CSV: {e}")
            raise 