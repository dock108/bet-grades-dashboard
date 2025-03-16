"""
Main routes for the application.
This module contains the routes for the main blueprint.
"""
from flask import Blueprint, render_template, jsonify
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
        
        # Sort bets by composite score
        def get_sort_key(bet):
            # Get composite score if available
            if hasattr(bet, 'grade') and bet.grade and hasattr(bet.grade, 'composite_score'):
                score = bet.grade.composite_score
                return (-score, -(bet.ev_percent or 0))
            return (0, -(bet.ev_percent or 0))
        
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
        logger.info("Sorted bets by composite score:")
        for bet in active_bets:
            if hasattr(bet, 'grade') and bet.grade:
                logger.info(f"Bet {bet.participant}: Score={bet.grade.composite_score}, EV%={bet.ev_percent}")
        
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
    """Render the rankings page with ranked betting opportunities."""
    try:
        # Get active bets
        active_bets = BettingService.get_active_bets()
        
        # Get current time in EST for time difference calculations
        est = pytz.timezone('America/New_York')
        now = datetime.now(est)
        
        # Process bets for ranking
        ranked_bets = []
        for bet in active_bets:
            try:
                # Ensure event_teams is set
                if not hasattr(bet, 'event_teams') or not bet.event_teams:
                    # First try to use home_team and away_team
                    if bet.home_team and bet.away_team:
                        bet.event_teams = f"{bet.home_team} vs {bet.away_team}"
                    # If not available, try to extract from description
                    elif bet.description and ("vs" in bet.description or "vs." in bet.description):
                        parts = bet.description.replace("vs.", "vs").split("vs")
                        if len(parts) >= 2:
                            bet.event_teams = f"{parts[0].strip()} vs {parts[1].strip()}"
                    else:
                        # Use participant as fallback
                        bet.event_teams = bet.participant
                
                ranked_bets.append(bet)
            except Exception as e:
                logger.error(f"Error processing bet for ranking: {str(e)}")
                continue

        # Log initial state
        logger.info("Before sorting - Composite scores:")
        for bet in ranked_bets:
            if hasattr(bet, 'grade') and bet.grade:
                logger.info(f"Bet {bet.participant}: Score={bet.grade.composite_score}, EV%={bet.ev_percent}")

        # Sort by composite score (if available), then EV%
        def get_sort_key(bet):
            # Get composite score if available
            if hasattr(bet, 'grade') and bet.grade and hasattr(bet.grade, 'composite_score'):
                score = bet.grade.composite_score
                # Log the actual score being used for sorting
                logger.info(f"Sort key for {bet.participant}: Using score {score}")
                return (-score, -(bet.ev_percent or 0))
            return (0, -(bet.ev_percent or 0))
        
        ranked_bets.sort(key=get_sort_key)
        
        # Log sorted state
        logger.info("After sorting - Composite scores:")
        for bet in ranked_bets:
            if hasattr(bet, 'grade') and bet.grade:
                logger.info(f"Bet {bet.participant}: Score={bet.grade.composite_score}, EV%={bet.ev_percent}")
        
        logger.info(f"Ranked {len(ranked_bets)} bets")
        if ranked_bets:
            top_bet = ranked_bets[0]
            logger.info(f"Top ranked bet: {top_bet.bet_id}, EV: {top_bet.ev_percent}, Composite Score: {top_bet.grade.composite_score if hasattr(top_bet, 'grade') and top_bet.grade else 'N/A'}")
        
        return render_template('rankings.html', ranked_bets=ranked_bets, now=now)
    except Exception as e:
        logger.error(f"Error in rankings route: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

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