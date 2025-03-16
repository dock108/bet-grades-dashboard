"""
API routes for bet-related operations.
Handles bet grading, updates, and retrievals.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import pytz
from app.models.bet_models import BetGrade, Bet
from app.core.database import execute_query

# Create a Blueprint for bet routes
bet_routes = Blueprint('bet_routes', __name__)

@bet_routes.route('/bets/update', methods=['POST'])
def update_bets():
    """
    Run grading update: compute Bayesian confidence and grades for all bets.
    Updates bet_grades table with latest calculations.
    """
    try:
        # Get all bets that need grading
        bets = execute_query(
            table_name="betting_data",
            query_type="select",
            order={"timestamp": "desc"}
        )

        updated_count = 0
        errors = []

        for bet in bets:
            try:
                bet_id = bet.get('bet_id')
                if not bet_id:
                    continue

                # Create Bet instance for easier handling
                bet_instance = Bet.from_dict(bet)
                
                # Calculate grade
                grade = BetGrade(
                    bet_id=bet_id,
                    ev_score=bet_instance.ev_percent,
                    timing_score=80,  # Default timing score
                    historical_edge=75,  # Default historical edge
                )

                # This will trigger Bayesian calculations and grade assignment
                grade.save()
                updated_count += 1

            except Exception as e:
                errors.append({"bet_id": bet_id, "error": str(e)})

        # Force update of distribution stats after batch update
        BetGrade._get_distribution_stats(force_update=True)

        response = {
            "status": "success",
            "updated_count": updated_count,
        }

        if errors:
            response["errors"] = errors

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bet_routes.route('/bets/graded', methods=['GET'])
def get_graded_bets():
    """
    Retrieve bets with their latest Bayesian confidence and grades.
    Supports filtering and pagination.
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        grade_filter = request.args.get('grade')
        min_confidence = request.args.get('min_confidence')
        max_confidence = request.args.get('max_confidence')

        # Build filters
        filters = {}
        if grade_filter:
            filters['grade'] = grade_filter
        if min_confidence:
            filters['bayesian_confidence__gte'] = float(min_confidence)
        if max_confidence:
            filters['bayesian_confidence__lte'] = float(max_confidence)

        # Calculate offset
        offset = (page - 1) * per_page

        # Get graded bets with pagination
        graded_bets = execute_query(
            table_name="bet_grades",
            query_type="select",
            filters=filters,
            order={"calculated_at": "desc"},
            limit=per_page,
            offset=offset
        )

        # Get total count for pagination
        total_count = execute_query(
            table_name="bet_grades",
            query_type="count",
            filters=filters
        )

        # Enhance bet data with additional details
        enhanced_bets = []
        for grade in graded_bets:
            bet_id = grade.get('bet_id')
            if not bet_id:
                continue

            # Get bet details
            bet_details = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"bet_id": bet_id}
            )

            if bet_details and len(bet_details) > 0:
                bet_data = bet_details[0]
                enhanced_bets.append({
                    "bet_id": bet_id,
                    "grade": grade.get('grade'),
                    "bayesian_confidence": grade.get('bayesian_confidence'),
                    "ev_change": grade.get('ev_change'),
                    "composite_score": grade.get('composite_score'),
                    "calculated_at": grade.get('calculated_at'),
                    "description": bet_data.get('description'),
                    "current_ev": bet_data.get('ev_percent'),
                    "event_time": bet_data.get('event_time'),
                    "sportsbook": bet_data.get('sportsbook')
                })

        return jsonify({
            "status": "success",
            "data": enhanced_bets,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Additional helper route for testing
@bet_routes.route('/bets/test-grade/<bet_id>', methods=['GET'])
def test_grade_bet(bet_id):
    """
    Test endpoint to grade a single bet and view the results.
    Useful for debugging and verification.
    """
    try:
        # Get bet details
        bet_details = execute_query(
            table_name="betting_data",
            query_type="select",
            filters={"bet_id": bet_id}
        )

        if not bet_details or len(bet_details) == 0:
            return jsonify({
                "status": "error",
                "message": f"Bet {bet_id} not found"
            }), 404

        bet = bet_details[0]
        
        # Test grade calculation
        grade = BetGrade.test_bayesian_update(bet_id, bet.get('ev_percent'))
        
        if not grade:
            return jsonify({
                "status": "error",
                "message": "Failed to calculate grade"
            }), 500

        return jsonify({
            "status": "success",
            "data": {
                "bet_id": bet_id,
                "grade": grade.grade,
                "bayesian_confidence": grade.bayesian_confidence,
                "ev_change": grade.ev_change,
                "composite_score": grade.composite_score,
                "ev_score": grade.ev_score,
                "timing_score": grade.timing_score,
                "historical_edge": grade.historical_edge
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500 