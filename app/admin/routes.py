from flask import render_template, request, jsonify
from app.admin import bp
from app.core.database import execute_query
import logging

# Configure logging
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Admin Dashboard with Overview Stats."""
    logger.debug("Accessing admin dashboard index")
    try:
        # Get total bets count
        total_bets_result = execute_query(
            table_name="betting_data",
            query_type="select",
            filters={}
        )
        total_bets = len(total_bets_result) if total_bets_result else 0
        
        # Get active bets count (unresolved bets)
        # Since we don't have a 'result' column, we'll just use all bets for now
        # This can be refined later if we add a way to track resolved bets
        active_bets_result = execute_query(
            table_name="betting_data",
            query_type="select",
            filters={}
        )
        active_bets = len(active_bets_result) if active_bets_result else 0
        
        stats = {
            'total_bets': total_bets,
            'active_bets': active_bets,
            'win_rate': calculate_win_rate(),
            'total_profit': calculate_total_profit(),
            'roi': calculate_roi()
        }
        
        # Recent performance graph
        performance_data = generate_performance_graph()
        
        return render_template(
            'admin/index.html',
            stats=stats,
            performance_graph=performance_data
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard index: {str(e)}")
        raise

@bp.route('/data-explorer')
def data_explorer():
    """Interactive Data Explorer."""
    logger.debug("Accessing data explorer")
    try:
        # Get distinct sports
        sports_result = execute_query(
            table_name="betting_data",
            query_type="select"
        )
        sports = list(set(bet.get('sport', '') for bet in sports_result if bet.get('sport')))
        
        # Get distinct sportsbooks
        sportsbooks_result = execute_query(
            table_name="betting_data",
            query_type="select"
        )
        sportsbooks = list(set(bet.get('sportsbook', '') for bet in sportsbooks_result if bet.get('sportsbook')))
        
        return render_template(
            'admin/data_explorer.html',
            sports=sports,
            sportsbooks=sportsbooks
        )
    except Exception as e:
        logger.error(f"Error in data explorer: {str(e)}")
        raise

@bp.route('/api/data')
def get_data():
    """API endpoint for fetching filtered data."""
    sport = request.args.get('sport')
    sportsbook = request.args.get('sportsbook')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    filters = {}
    
    if sport:
        filters['sport'] = sport
    if sportsbook:
        filters['sportsbook'] = sportsbook
    if date_from:
        filters['timestamp'] = {"operator": "gte", "value": date_from}
    if date_to:
        if 'timestamp' in filters:
            # This is a simplification - Supabase doesn't easily support range queries
            # You might need to handle this differently based on your specific requirements
            pass
        else:
            filters['timestamp'] = {"operator": "lte", "value": date_to}
    
    try:
        bets = execute_query(
            table_name="betting_data",
            query_type="select",
            filters=filters
        )
        return jsonify(bets)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({"error": str(e)}), 500

def calculate_win_rate():
    """Calculate overall win rate."""
    try:
        # Since we don't have a 'result' column, we can't calculate win rate
        # This is a placeholder that returns 0
        # TODO: Implement win rate calculation when we have a way to track bet results
        return 0
    except Exception as e:
        logger.error(f"Error calculating win rate: {str(e)}")
        return 0

def calculate_total_profit():
    """Calculate total profit."""
    try:
        # Since we don't have a 'result' column, we can't calculate profit
        # This is a placeholder that returns 0
        # TODO: Implement profit calculation when we have a way to track bet results
        return 0
    except Exception as e:
        logger.error(f"Error calculating total profit: {str(e)}")
        return 0

def calculate_roi():
    """Calculate ROI."""
    try:
        # Since we don't have a 'result' column, we can't calculate ROI
        # This is a placeholder that returns 0
        # TODO: Implement ROI calculation when we have a way to track bet results
        return 0
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return 0

def generate_performance_graph():
    """Generate performance over time graph."""
    try:
        # Since we don't have a 'result' column, we can't generate a performance graph
        # This is a placeholder that returns None
        # TODO: Implement performance graph when we have a way to track bet results
        return None
    except Exception as e:
        logger.error(f"Error generating performance graph: {str(e)}")
        return None 