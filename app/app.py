#!/usr/bin/env python3

import logging
from datetime import datetime, date
from flask import Flask, jsonify, request
from services import SalesService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize services
sales_service = SalesService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'lengolf-sales-api'
    })

@app.route('/info', methods=['GET'])
def info():
    """Service information endpoint"""
    return jsonify({
        'service': 'Lengolf Sales Sync API',
        'version': '2.0.0',
        'description': 'Microservice for synchronizing sales data from Qashier POS to Supabase',
        'endpoints': {
            'health': 'GET /health - Health check',
            'sync_daily': 'POST /sync/daily - Trigger daily sync',
            'sync_historical': 'POST /sync/historical - Trigger historical sync for date range (month by month)',
            'sync_estimates': 'POST /sync/estimates - Get sync estimates for date range',
            'info': 'GET /info - Service information'
        },
        'features': {
            'historical_sync': 'Sync any date range from March 2024 onwards',
            'monthly_processing': 'Large date ranges are processed month by month',
            'validation': 'Automatic date range validation and adjustment',
            'estimates': 'Get time and chunk estimates before syncing'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/sync/daily', methods=['POST'])
def sync_daily():
    """Trigger daily sync from Qashier POS to Supabase"""
    try:
        logger.info("API: Daily sync requested")
        result = sales_service.sync_daily_data()
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API: Error in daily sync: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/sync/historical', methods=['POST'])
def sync_historical():
    """
    Trigger historical sync for a specific date range (processed month by month)
    
    Expected JSON body:
    {
        "start_date": "2024-03-01",  # YYYY-MM-DD format
        "end_date": "2024-06-30"     # YYYY-MM-DD format
    }
    
    The date range will be automatically split into monthly chunks and processed sequentially.
    Large ranges (>12 months) will be automatically limited for performance.
    """
    try:
        # Validate request body
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'start_date' not in data or 'end_date' not in data:
            return jsonify({
                'success': False,
                'message': 'start_date and end_date are required fields'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        logger.info(f"API: Historical sync requested for {start_date} to {end_date}")
        result = sales_service.sync_historical_data(start_date, end_date)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API: Error in historical sync: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/sync/estimates', methods=['POST'])
def get_sync_estimates():
    """
    Get estimates for syncing a date range without actually performing the sync
    
    Expected JSON body:
    {
        "start_date": "2024-03-01",  # YYYY-MM-DD format
        "end_date": "2024-06-30"     # YYYY-MM-DD format
    }
    
    Returns information about:
    - How many monthly chunks will be created
    - Total days to sync
    - Estimated time
    - Validation warnings
    - Recommendations
    """
    try:
        # Validate request body
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'start_date' not in data or 'end_date' not in data:
            return jsonify({
                'success': False,
                'message': 'start_date and end_date are required fields'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        logger.info(f"API: Sync estimates requested for {start_date} to {end_date}")
        result = sales_service.get_sync_estimates(start_date, end_date)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API: Error calculating sync estimates: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    from config import config
    
    logger.info(f"Starting Lengolf Sales API on {config.host}:{config.port}")
    logger.info(f"Debug mode: {config.debug}")
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    ) 