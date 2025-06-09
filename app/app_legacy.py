#!/usr/bin/env python3
"""
Legacy compatibility script for the original app_supabase.py functionality.
This script maintains the same CLI interface but uses the new modular structure.
"""

import logging
from services import SalesService

logger = logging.getLogger(__name__)

def main():
    """Main function to run the daily sync process (legacy compatibility)"""
    logger.info("Starting Lengolf Sales POS sync process (legacy mode)...")
    
    try:
        # Initialize service
        sales_service = SalesService()
        
        # Run daily sync
        result = sales_service.sync_daily_data()
        
        if result['success']:
            logger.info("Legacy sync completed successfully")
            logger.info(f"Result: {result}")
        else:
            logger.error("Legacy sync failed")
            logger.error(f"Error: {result}")
            raise Exception(result['message'])
            
    except Exception as e:
        logger.error(f"Fatal error in legacy sync process: {e}")
        raise

if __name__ == "__main__":
    main() 