"""
API routes for the application.
"""
from flask import Blueprint, jsonify, request
from app.services.bet_service import BettingService
from app.models.bet_models import Bet
from app.services.parlay import ParlayService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)

@bp.route('/calculate_parlay', methods=['POST'])
def calculate_parlay():
    """API endpoint to calculate parlay odds and metrics."""
    data = request.get_json()
    bet_ids = data.get('bet_ids', [])
    
    # Fetch bet data
    bets = []
    for bet_id in bet_ids:
        bet = Bet.get_by_id(bet_id)
        if bet:
            bets.append({
                'odds': bet.odds,
                'win_probability': bet.win_probability,
                'ev_percent': bet.ev_percent
            })
    
    if not bets:
        return jsonify({'error': 'No valid bets found'}), 400
    
    # Calculate parlay metrics
    try:
        parlay_result = ParlayService.compute_parlay_odds(bets)
        return jsonify({
            'decimal_odds': parlay_result.decimal_odds,
            'american_odds': parlay_result.american_odds,
            'implied_probability': parlay_result.implied_prob_from_odds,
            'true_probability': parlay_result.true_win_prob,
            'ev_percent': parlay_result.ev,
            'kelly_fraction': parlay_result.kelly_fraction,
            'total_edge': parlay_result.total_edge,
            'correlated_warning': parlay_result.correlated_warning
        })
    except Exception as e:
        logger.error("Error calculating parlay: %s", str(e))
        return jsonify({'error': 'An internal error has occurred!'}), 500

@bp.route('/sportsbook_bets/<sportsbook>')
def get_sportsbook_bets(sportsbook):
    """Get all active bets for a specific sportsbook."""
    try:
        logger.info(f"API: Fetching bets for sportsbook: {sportsbook}")
        bets = BettingService.get_bets_by_sportsbook(sportsbook, include_resolved=False, include_grades=True)
        logger.info(f"API: Found {len(bets)} bets for sportsbook {sportsbook}")
        
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
                'event_teams': bet.event_teams if hasattr(bet, 'event_teams') else None,
                'grade': bet.grade.grade if hasattr(bet, 'grade') and bet.grade else None,
                'composite_score': bet.grade.composite_score if hasattr(bet, 'grade') and bet.grade else None
            }
            formatted_bets.append(formatted_bet)
        
        logger.info(f"API: Returning {len(formatted_bets)} formatted bets for sportsbook {sportsbook}")
        return jsonify(formatted_bets)
    except Exception as e:
        logger.error(f"Error getting sportsbook bets for {sportsbook}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/summary_stats')
def get_summary_stats():
    """Get summary statistics for bets."""
    try:
        # Get active bets
        active_bets = BettingService.get_active_bets(include_grades=True)
        
        # Calculate summary statistics
        stats = BettingService.calculate_summary_statistics(active_bets)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting summary stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/performance')
def get_performance_stats():
    """Get performance statistics for bets."""
    try:
        # Get active bets
        active_bets = BettingService.get_active_bets(include_grades=True)
        
        # Calculate summary statistics
        stats = BettingService.calculate_summary_statistics(active_bets)
        
        return jsonify({
            'total_bets': stats.get('total_bets', 0),
            'average_ev': stats.get('average_ev', 0),
            'average_edge': stats.get('average_edge', 0)
        })
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return jsonify({'error': str(e)}), 500 