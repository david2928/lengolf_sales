#!/usr/bin/env python3

import logging
import traceback
from typing import Dict, Any, List, Tuple
from datetime import date, datetime
import pandas as pd
from supabase_client import SupabaseClient
from qashier_scraper import QashierPOSScraper
from utils import (
    split_date_range_by_month,
    validate_date_range,
    calculate_sync_estimates
)

logger = logging.getLogger(__name__)

class SalesService:
    """Service layer for sales data operations"""
    
    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.scraper = QashierPOSScraper()
    
    def sync_daily_data(self) -> Dict[str, Any]:
        """Sync daily sales data from Qashier POS"""
        try:
            # Create sync log entry
            batch_id = self.supabase_client.create_sync_log('daily_sync')
            logger.info("Starting daily sync process...")
            
            # Scrape data from Qashier
            logger.info("Scraping data from Qashier POS...")
            sales_df = self.scraper.scrape_daily_data()
            
            if sales_df.empty:
                logger.warning("No data scraped from Qashier")
                self.supabase_client.update_sync_log(
                    batch_id, 
                    'completed', 
                    0, 
                    {'message': 'No data available for today'}
                )
                return {
                    'success': True,
                    'message': 'No data available for today',
                    'batch_id': batch_id,
                    'records_scraped': 0,
                    'records_inserted': 0,
                    'records_processed': 0
                }
            
            # Load data into staging table
            logger.info(f"Loading {len(sales_df)} records into staging table...")
            records_inserted = self.supabase_client.insert_staging_data(sales_df, batch_id)
            
            # Process staging data to final table using database function
            logger.info("Processing staging data...")
            records_processed = self.supabase_client.process_staging_to_final(batch_id)
            
            # Clean up staging data
            self.supabase_client.cleanup_staging_data(batch_id)
            
            # Update sync log with success
            self.supabase_client.update_sync_log(
                batch_id, 
                'completed', 
                records_processed, 
                error_message=None,
                metadata={
                    'records_scraped': len(sales_df),
                    'records_inserted': records_inserted,
                    'records_processed': records_processed
                }
            )
            
            logger.info(f"Daily sync completed successfully. Processed {records_processed} records.")
            
            return {
                'success': True,
                'message': f'Successfully processed {records_processed} records',
                'batch_id': batch_id,
                'records_scraped': len(sales_df),
                'records_inserted': records_inserted,
                'records_processed': records_processed
            }
            
        except Exception as e:
            logger.error(f"Daily sync failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update sync log with error if batch_id exists
            if 'batch_id' in locals():
                self.supabase_client.update_sync_log(
                    batch_id, 
                    'failed', 
                    0, 
                    error_message=str(e),
                    metadata={'error_details': str(e)}
                )
            
            return {
                'success': False,
                'message': f'Daily sync failed: {str(e)}',
                'error': str(e)
            }
    
    def sync_historical_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Sync historical sales data for a specific date range, processing month by month
        
        Args:
            start_date: Start date for historical sync
            end_date: End date for historical sync
            
        Returns:
            Dictionary with sync results
        """
        # Validate date range
        validated_start, validated_end, warnings = validate_date_range(start_date, end_date)
        
        logger.info(f"Starting historical sync process for {validated_start} to {validated_end}...")
        if warnings:
            logger.warning(f"Date range validation warnings: {warnings}")
        
        # Get sync estimates
        estimates = calculate_sync_estimates(validated_start, validated_end)
        logger.info(f"Will process {estimates['monthly_chunks']} monthly chunks ({estimates['total_days']} days total)")
        logger.info(f"Estimated time: ~{estimates['estimated_time_minutes']} minutes")
        
        # Create sync log for historical sync with metadata
        metadata = {
            'start_date': str(validated_start),
            'end_date': str(validated_end),
            'total_days': estimates['total_days'],
            'monthly_chunks': estimates['monthly_chunks'],
            'estimated_time_minutes': estimates['estimated_time_minutes']
        }
        batch_id = self.supabase_client.create_sync_log('historical_sync', metadata)
        
        # Process month by month
        monthly_chunks = split_date_range_by_month(validated_start, validated_end)
        
        overall_results = {
            'success': True,
            'message': '',
            'batch_id': batch_id,
            'start_date': str(validated_start),
            'end_date': str(validated_end),
            'warnings': warnings,
            'total_chunks': len(monthly_chunks),
            'chunks_processed': 0,
            'total_records_processed': 0,
            'chunk_results': [],
            'errors': []
        }
        
        try:
            for i, (chunk_start, chunk_end) in enumerate(monthly_chunks):
                chunk_days = (chunk_end - chunk_start).days + 1
                logger.info(f"Processing chunk {i+1}/{len(monthly_chunks)}: {chunk_start} to {chunk_end} ({chunk_days} days)")
                
                try:
                    # Scrape historical data for this chunk
                    sales_df = self.scraper.scrape_historical_data(chunk_start, chunk_end)
                    
                    if sales_df.empty:
                        logger.warning(f"No data found for chunk {chunk_start} to {chunk_end}")
                        chunk_result = {
                            'chunk_index': i + 1,
                            'start_date': str(chunk_start),
                            'end_date': str(chunk_end),
                            'days': chunk_days,
                            'success': True,
                            'records_scraped': 0,
                            'records_processed': 0,
                            'message': 'No data found for this period'
                        }
                    else:
                        # Insert data into staging table
                        records_inserted = self.supabase_client.insert_staging_data(sales_df, batch_id)
                        
                        # Process staging data to final table
                        records_processed = self.supabase_client.process_staging_to_final(batch_id)
                        
                        overall_results['total_records_processed'] += records_processed
                        
                        chunk_result = {
                            'chunk_index': i + 1,
                            'start_date': str(chunk_start),
                            'end_date': str(chunk_end),
                            'days': chunk_days,
                            'success': True,
                            'records_scraped': len(sales_df),
                            'records_processed': records_processed,
                            'message': f'Successfully processed {records_processed} records'
                        }
                        
                        logger.info(f"Chunk {i+1} completed: {records_processed} records processed")
                    
                    overall_results['chunk_results'].append(chunk_result)
                    overall_results['chunks_processed'] += 1
                    
                except Exception as chunk_error:
                    error_msg = f"Failed to process chunk {chunk_start} to {chunk_end}: {str(chunk_error)}"
                    logger.error(error_msg)
                    
                    chunk_result = {
                        'chunk_index': i + 1,
                        'start_date': str(chunk_start),
                        'end_date': str(chunk_end),
                        'days': chunk_days,
                        'success': False,
                        'error': str(chunk_error),
                        'message': error_msg
                    }
                    
                    overall_results['chunk_results'].append(chunk_result)
                    overall_results['errors'].append(error_msg)
                    overall_results['success'] = False
            
            # Clean up staging data
            self.supabase_client.cleanup_staging_data(batch_id)
            
            # Create summary message
            if overall_results['success']:
                overall_results['message'] = f"Successfully processed {overall_results['chunks_processed']}/{overall_results['total_chunks']} monthly chunks with {overall_results['total_records_processed']} total records"
            else:
                overall_results['message'] = f"Completed with errors. Processed {overall_results['chunks_processed']}/{overall_results['total_chunks']} chunks successfully, {len(overall_results['errors'])} failed"
            
            # Update sync log with final results
            self.supabase_client.update_sync_log(
                batch_id, 
                'completed' if overall_results['success'] else 'partial',
                overall_results['total_records_processed'],
                error_message='; '.join(overall_results['errors']) if overall_results['errors'] else None,
                metadata={
                    'start_date': str(validated_start),
                    'end_date': str(validated_end),
                    'sync_type': 'historical_range',
                    'warnings': warnings,
                    'chunks_processed': overall_results['chunks_processed'],
                    'total_chunks': overall_results['total_chunks'],
                    'total_records': overall_results['total_records_processed']
                }
            )
            
            logger.info(f"Historical sync completed: {overall_results['message']}")
            
            return overall_results
            
        except Exception as e:
            error_msg = f"Error during historical sync process: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            self.supabase_client.update_sync_log(
                batch_id, 
                'failed', 
                overall_results['total_records_processed'],
                error_message=error_msg,
                metadata={
                    'start_date': str(validated_start),
                    'end_date': str(validated_end),
                    'sync_type': 'historical_range',
                    'warnings': warnings,
                    'chunks_processed': overall_results['chunks_processed'],
                    'total_chunks': overall_results['total_chunks']
                }
            )
            
            overall_results['success'] = False
            overall_results['message'] = error_msg
            overall_results['error'] = str(e)
            
            return overall_results

    def get_sync_estimates(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get estimates for syncing a date range without actually performing the sync
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with sync estimates
        """
        try:
            # Validate date range
            validated_start, validated_end, warnings = validate_date_range(start_date, end_date)
            
            # Calculate estimates
            estimates = calculate_sync_estimates(validated_start, validated_end)
            
            return {
                'success': True,
                'original_range': {
                    'start_date': str(start_date),
                    'end_date': str(end_date)
                },
                'validated_range': {
                    'start_date': str(validated_start),
                    'end_date': str(validated_end)
                },
                'warnings': warnings,
                'estimates': estimates,
                'recommendations': {
                    'proceed': estimates['monthly_chunks'] <= 6,  # Recommend if 6 months or less
                    'reason': 'Recommended range size' if estimates['monthly_chunks'] <= 6 else 'Consider smaller date range for faster processing'
                }
            }
            
        except Exception as e:
            error_msg = f"Error calculating sync estimates: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            } 