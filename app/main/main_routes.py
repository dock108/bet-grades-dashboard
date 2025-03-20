"""
Main routes for the application.
This module contains the routes for the main blueprint.
"""
from flask import render_template, jsonify, redirect, url_for
from app.main import bp
from app.services.bet_service import BettingService
import logging
from pprint import pformat
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

@bp.route('/')
def index():
    """Render the home dashboard with current betting opportunities."""
    try:
        # Get active bets
        active_bets = BettingService.get_active_bets()
        
        # Sort bets by grade letter first (A > B > C > D > F) and then by composite score within each grade
        grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, None: 5}
        
        def get_sort_key(bet):
            # First sort by grade letter, then by composite score
            if hasattr(bet, 'grade') and bet.grade and hasattr(bet.grade, 'grade'):
                return (
                    grade_order.get(bet.grade.grade, 5),
                    -(bet.grade.composite_score if hasattr(bet.grade, 'composite_score') else 0)
                )
            return (5, 0)  # No grade is sorted last
        
        active_bets.sort(key=get_sort_key)
        
        # Get sportsbook counts
        sportsbook_counts = BettingService.get_sportsbook_counts()
        
        # Calculate summary statistics
        summary_stats = BettingService.calculate_summary_statistics(active_bets)
        
        # Debug logs
        logger.info(f"Found {len(active_bets)} active bets")
        logger.info(f"Sportsbooks: {list(sportsbook_counts.keys())}")
        logger.info(f"Grade distribution: {pformat(summary_stats.get('grade_distribution', {}))}")
        logger.info(f"Sportsbook distribution: {pformat(summary_stats.get('sportsbook_distribution', {}))}")
        logger.info(f"Time distribution: {pformat(summary_stats.get('time_distribution', {}))}")
        logger.info(f"Latest timestamp: {summary_stats.get('latest_timestamp')}")
        
        # Debug log for template variables
        logger.info("Template variables:")
        logger.info(f"current_bets length: {len(active_bets)}")
        logger.info(f"summary_stats keys: {list(summary_stats.keys())}")
        logger.info(f"sportsbook_counts keys: {list(sportsbook_counts.keys())}")
        
        # Get current time in EST for time difference calculations
        est = pytz.timezone('America/New_York')
        now = datetime.now(est)
        
        # Log the sorted bets
        logger.info("Sorted bets by grade and composite score:")
        for bet in active_bets:
            if hasattr(bet, 'grade') and bet.grade:
                logger.info(f"Bet {bet.participant}: Grade={bet.grade.grade}, Score={bet.grade.composite_score}")
        
        return render_template(
            'index.html',
            current_bets=active_bets,
            sportsbook_counts=sportsbook_counts,
            summary_stats=summary_stats,
            now=now
        )
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)  # Added exc_info for full traceback
        return render_template('error.html', error=str(e))

@bp.route('/rankings')
def rankings():
    """Redirect to the main dashboard page which already shows ranked betting opportunities."""
    return redirect(url_for('main.index'))

@bp.route('/explainer')
def explainer():
    """Render the explainer page."""
    return render_template('explainer.html')

@bp.route('/api/sportsbook/<sportsbook>')
def get_sportsbook_bets(sportsbook):
    """Get active bets for a specific sportsbook."""
    try:
        # Get bets for the sportsbook
        bets = BettingService.get_bets_by_sportsbook(sportsbook, include_grades=True, include_resolved=False)
        
        # Filter for grades A and B
        grade_a_bets = [bet for bet in bets if hasattr(bet, 'grade') and bet.grade and bet.grade.grade == 'A']
        grade_b_bets = [bet for bet in bets if hasattr(bet, 'grade') and bet.grade and bet.grade.grade == 'B']
        
        # Calculate metrics
        total_bets = len(bets)
        grade_a_count = len(grade_a_bets)
        grade_b_count = len(grade_b_bets)
        
        # Calculate average EV
        total_ev = sum(safe_float(bet.ev_percent) for bet in bets if bet.ev_percent is not None)
        avg_ev = total_ev / total_bets if total_bets > 0 else 0
        
        # Format bets for JSON response
        formatted_bets = []
        for bet in bets:
            formatted_bet = {
                'bet_id': bet.bet_id,
                'timestamp': bet.timestamp,
                'betid_timestamp': bet.betid_timestamp,
                'ev_percent': bet.ev_percent,
                'event_time': bet.event_time,
                'home_team': bet.home_team,
                'away_team': bet.away_team,
                'sport': bet.sport,
                'league': bet.league,
                'description': bet.description,
                'participant': bet.participant,
                'bet_line': bet.bet_line,
                'bet_type': bet.bet_type,
                'bet_category': bet.bet_category,
                'odds': bet.odds,
                'sportsbook': bet.sportsbook,
                'bet_size': bet.bet_size,
                'win_probability': bet.win_probability,
                'edge': bet.edge,
                'market_implied_prob': bet.market_implied_prob,
                'event_teams': bet.event_teams if hasattr(bet, 'event_teams') else None,
                'grade': bet.grade.grade if hasattr(bet, 'grade') and bet.grade else None,
                'composite_score': bet.grade.composite_score if hasattr(bet, 'grade') and bet.grade else None
            }
            formatted_bets.append(formatted_bet)
        
        return jsonify({
            'sportsbook': sportsbook,
            'total_bets': total_bets,
            'grade_a_count': grade_a_count,
            'grade_b_count': grade_b_count,
            'avg_ev': avg_ev,
            'bets': formatted_bets
        })
    except Exception as e:
        logger.error(f"Error in get_sportsbook_bets for {sportsbook}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 