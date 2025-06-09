#!/usr/bin/env python3

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from config import TIMEZONE

def get_current_time():
    """Get current time in Bangkok timezone"""
    return datetime.now(TIMEZONE)

def calculate_month_navigation(current_date: date, target_date: date) -> dict:
    """
    Calculate navigation steps needed to go from current month to target month
    Returns dict with year and month navigation steps needed
    """
    # Calculate the difference in months
    current_year_month = current_date.year * 12 + current_date.month
    target_year_month = target_date.year * 12 + target_date.month
    
    month_diff = target_year_month - current_year_month
    
    # For year navigation: if target year is different, we need to navigate years first
    year_diff = target_date.year - current_date.year
    
    return {
        'year_diff': year_diff,
        'month_diff': month_diff,
        'total_months': month_diff,
        'navigation_direction': 'left' if month_diff < 0 else 'right',
        'steps_needed': abs(month_diff)
    }

def get_date_range_for_month(year: int, month: int) -> tuple:
    """Get the first and last day of a given month"""
    first_day = date(year, month, 1)
    
    # Get last day by going to first day of next month and subtracting 1 day
    if month == 12:
        last_day = date(year + 1, 1, 1) - relativedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - relativedelta(days=1)
    
    return first_day, last_day

def format_date_for_display(date_obj: date) -> dict:
    """Format date for Qashier POS interface display"""
    return {
        'day_text': date_obj.strftime('%A %d/%m/'),  # e.g., "Monday 09/06/"
        'month_text': date_obj.strftime('%B'),       # e.g., "March"
        'day': str(date_obj.day),                    # e.g., "9"
        'formatted_date': date_obj.strftime('%Y-%m-%d')
    }

def split_date_range_by_month(start_date: date, end_date: date) -> list:
    """
    Split a date range into monthly chunks for easier processing
    Returns list of (start_date, end_date) tuples for each month
    """
    chunks = []
    current = start_date
    
    while current <= end_date:
        # Get the last day of current month
        month_end = get_last_day_of_month(current.year, current.month)
        
        # Don't go beyond the end date
        chunk_end = min(month_end, end_date)
        
        chunks.append((current, chunk_end))
        
        # Move to first day of next month
        current = chunk_end + relativedelta(days=1)
    
    return chunks

def get_last_day_of_month(year: int, month: int) -> date:
    """Get the last day of a given month"""
    if month == 12:
        return date(year + 1, 1, 1) - relativedelta(days=1)
    else:
        return date(year, month + 1, 1) - relativedelta(days=1)

def validate_date_range(start_date: date, end_date: date) -> tuple:
    """
    Validate and adjust date range to ensure it's reasonable for scraping
    Returns (adjusted_start, adjusted_end, warnings)
    """
    warnings = []
    current_date = get_current_time().date()
    
    # Don't allow future dates
    if start_date > current_date:
        start_date = current_date
        warnings.append("Start date adjusted to today (cannot sync future dates)")
    
    if end_date > current_date:
        end_date = current_date
        warnings.append("End date adjusted to today (cannot sync future dates)")
    
    # Don't allow ranges that are too large (more than 12 months)
    max_months = 12
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if months_diff > max_months:
        end_date = start_date + relativedelta(months=max_months)
        warnings.append(f"Date range limited to {max_months} months to prevent timeout")
    
    # Don't allow dates before March 2024 (before system existed)
    earliest_allowed = date(2024, 3, 1)
    if start_date < earliest_allowed:
        start_date = earliest_allowed
        warnings.append("Start date adjusted to March 1, 2024 (earliest available data)")
    
    # Ensure start is before end
    if start_date > end_date:
        start_date, end_date = end_date, start_date
        warnings.append("Start and end dates were swapped")
    
    return start_date, end_date, warnings

def calculate_sync_estimates(start_date: date, end_date: date) -> dict:
    """
    Calculate estimates for syncing a date range
    """
    monthly_chunks = split_date_range_by_month(start_date, end_date)
    total_days = (end_date - start_date).days + 1
    
    return {
        'total_days': total_days,
        'monthly_chunks': len(monthly_chunks),
        'estimated_time_minutes': len(monthly_chunks) * 2,  # ~2 minutes per month
        'chunks': [
            {
                'start': str(chunk_start),
                'end': str(chunk_end),
                'days': (chunk_end - chunk_start).days + 1
            }
            for chunk_start, chunk_end in monthly_chunks
        ]
    } 