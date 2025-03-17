"""
Betting service layer.
This module contains business logic for processing and managing bets.
"""
import logging
from app.core.database import execute_query
from app.models.bet_models import Bet, BetGrade
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class BettingService:
    """Service class for managing betting operations."""
    
    @staticmethod
    def get_active_bets(limit=None, include_grades=True):
        """
        Get most recent bets sorted by grade.
        
        Args:
            limit (int, optional): Maximum number of bets to return.
            include_grades (bool, optional): Whether to include grades.
            
        Returns:
            list: List of bets sorted by grade.
        """
        bets = []
        est = pytz.timezone('America/New_York')
        
        try:
            # Get most recent timestamp first
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            
            if not timestamp_result:
                logger.warning("No timestamps found in betting_data")
                return []
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            logger.info(f"Latest timestamp: {latest_timestamp}")
            
            # Get bets from the latest timestamp
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"timestamp": latest_timestamp},
                order={"timestamp": "desc"},
                limit=limit
            )
            
            logger.info(f"Found {len(result)} bets from latest timestamp {latest_timestamp}")
            if result:
                logger.info(f"Sample bet data: {result[0]}")
            
            for row in result:
                try:
                    bet = Bet.from_dict(row)
                    
                    # Format event_time if it exists
                    if bet.event_time and isinstance(bet.event_time, str):
                        try:
                            # Try different formats for parsing the string
                            try:
                                # Try the format with seconds
                                naive_dt = datetime.strptime(bet.event_time, "%Y-%m-%dT%H:%M:%S")
                                bet.event_time = est.localize(naive_dt)
                            except ValueError:
                                try:
                                    # Try the format without seconds
                                    naive_dt = datetime.strptime(bet.event_time, "%Y-%m-%d %H:%M")
                                    bet.event_time = est.localize(naive_dt)
                                except ValueError:
                                    # If all parsing fails, leave as string
                                    logger.warning(f"Could not parse event_time: {bet.event_time} for bet {bet.bet_id}")
                        except (ValueError, TypeError) as e:
                            # If parsing fails, leave it as is
                            logger.warning(f"Error parsing event_time: {str(e)}")
                    
                    # Handle bet_line - ensure it's not "None" as a string
                    if bet.bet_line == "None":
                        bet.bet_line = None
                    
                    # Set event_teams based on home_team and away_team if available
                    if bet.home_team and bet.away_team:
                        bet.event_teams = f"{bet.home_team} vs {bet.away_team}"
                    # If not available, try to extract from description
                    elif not hasattr(bet, 'event_teams') or not bet.event_teams:
                        if bet.description and ("vs" in bet.description or "vs." in bet.description):
                            parts = bet.description.replace("vs.", "vs").split("vs")
                            if len(parts) >= 2:
                                bet.event_teams = f"{parts[0].strip()} vs {parts[1].strip()}"
                    
                    # Calculate market implied probability if we have odds
                    if bet.odds:
                        try:
                            odds = float(bet.odds)
                            if odds > 0:
                                bet.market_implied_prob = 100 / (odds + 100) * 100
                            else:
                                bet.market_implied_prob = abs(odds) / (abs(odds) + 100) * 100
                        except (ValueError, ZeroDivisionError):
                            bet.market_implied_prob = None
                    
                    # Calculate edge if we have win_probability and market_implied_prob
                    if bet.win_probability and bet.market_implied_prob:
                        bet.edge = bet.win_probability - bet.market_implied_prob
                    
                    bets.append(bet)
                except Exception as e:
                    logger.error(f"Error processing bet: {str(e)}")
                    continue
            
            if include_grades and bets:
                # Get grades for these bets
                bet_ids = [bet.bet_id for bet in bets]
                logger.info(f"Fetching grades for {len(bet_ids)} bets")
                
                # Get all grades ordered by calculated_at in descending order
                grades_result = execute_query(
                    table_name="bet_grades",
                    query_type="select",
                    order={"calculated_at": "desc"}
                )
                
                logger.info(f"Retrieved {len(grades_result)} grades from database")
                
                # Create a lookup dictionary for grades
                # Only keep the most recent grade for each bet_id
                grade_lookup = {}
                for row in grades_result:
                    bet_id = row.get("bet_id")
                    if bet_id in bet_ids and bet_id not in grade_lookup:
                        grade_lookup[bet_id] = BetGrade.from_dict(row)
                
                logger.info(f"Created grade lookup with {len(grade_lookup)} entries")
                logger.info(f"Found grades for {len(grade_lookup)}/{len(bet_ids)} bets")
                
                # Attach grades to bets
                for bet in bets:
                    bet.grade = grade_lookup.get(bet.bet_id)
                    if bet.grade:
                        logger.info(f"Attached grade {bet.grade.grade} with score {bet.grade.composite_score} to bet {bet.bet_id}")
                
                # Count grades by type
                grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "None": 0}
                for bet in bets:
                    if bet.grade and bet.grade.grade:
                        grade_counts[bet.grade.grade] += 1
                    else:
                        grade_counts["None"] += 1
                
                logger.info(f"Grade distribution after attachment: {grade_counts}")
                
                # Sort bets by grade (A > B > C > D > F)
                grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, None: 5}
                bets.sort(key=lambda x: (grade_order.get(x.grade.grade if x.grade else None, 5)))
            
            return bets
        except Exception as e:
            logger.error(f"Error getting active bets: {str(e)}")
            return []
    
    @staticmethod
    def get_bets_by_sportsbook(sportsbook, include_grades=True, include_resolved=False):
        """
        Get bets for a specific sportsbook from the latest timestamp.
        
        Args:
            sportsbook (str): The sportsbook to get bets for.
            include_grades (bool, optional): Whether to include grades.
            include_resolved (bool, optional): Whether to include resolved bets.
            
        Returns:
            list: List of bets for the sportsbook.
        """
        try:
            logger.info(f"BetService: Getting bets for sportsbook: {sportsbook}")
            
            # Get most recent timestamp first
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            
            if not timestamp_result:
                logger.warning(f"BetService: No timestamps found in betting_data for {sportsbook}")
                return []
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            logger.info(f"BetService: Latest timestamp: {latest_timestamp}")
            
            # Use the Bet model's get_by_sportsbook method which already handles include_resolved
            bets = Bet.get_by_sportsbook(sportsbook, include_resolved=include_resolved)
            logger.info(f"BetService: Found {len(bets)} total bets for sportsbook {sportsbook}")
            
            # Filter to only include bets from the latest timestamp
            bets = [bet for bet in bets if bet.timestamp == latest_timestamp]
            logger.info(f"BetService: After filtering for latest timestamp, found {len(bets)} bets for sportsbook {sportsbook}")
            
            # Log sportsbooks in the database
            all_sportsbooks = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={}
            )
            logger.info(f"BetService: All sportsbooks in database: {[sb.get('sportsbook') for sb in all_sportsbooks if sb.get('sportsbook')]}")
            
            # Log the first few bets for debugging
            if bets:
                logger.info(f"BetService: First bet for {sportsbook}: {bets[0].bet_id}, {bets[0].participant}, {bets[0].odds}")
            else:
                # Check if there are any bets for this sportsbook at all
                all_sportsbook_bets = execute_query(
                    table_name="betting_data",
                    query_type="select",
                    filters={"sportsbook": sportsbook}
                )
                logger.info(f"BetService: Found {len(all_sportsbook_bets)} total bets for {sportsbook} across all timestamps")
                
                if all_sportsbook_bets:
                    # Log the timestamps for this sportsbook
                    timestamps = set(row.get('timestamp') for row in all_sportsbook_bets)
                    logger.info(f"BetService: Timestamps for {sportsbook}: {timestamps}")
                    logger.info(f"BetService: Latest timestamp: {latest_timestamp}")
                    logger.info(f"BetService: Latest timestamp in set: {latest_timestamp in timestamps}")
            
            # Format event_time for each bet and handle bet_line
            for bet in bets:
                # Format event_time if it exists
                if bet.event_time and isinstance(bet.event_time, str):
                    try:
                        # Try different formats for parsing the string
                        try:
                            # Try the format with seconds
                            bet.event_time = datetime.strptime(bet.event_time, "%Y-%m-%dT%H:%M:%S")
                        except ValueError:
                            try:
                                # Try the format without seconds
                                bet.event_time = datetime.strptime(bet.event_time, "%Y-%m-%d %H:%M")
                            except ValueError:
                                # If all parsing fails, leave as string
                                logger.warning(f"Could not parse event_time: {bet.event_time} for bet {bet.bet_id}")
                    except (ValueError, TypeError) as e:
                        # If parsing fails, leave it as is
                        logger.warning(f"Error parsing event_time: {str(e)}")
                
                # Handle bet_line - ensure it's not "None" as a string
                if bet.bet_line == "None":
                    bet.bet_line = None
                
                # Set event_teams based on home_team and away_team if available
                if bet.home_team and bet.away_team:
                    bet.event_teams = f"{bet.home_team} vs {bet.away_team}"
                # If not available, try to extract from description
                elif not hasattr(bet, 'event_teams') or not bet.event_teams:
                    if bet.description and ("vs" in bet.description or "vs." in bet.description):
                        parts = bet.description.replace("vs.", "vs").split("vs")
                        if len(parts) >= 2:
                            bet.event_teams = f"{parts[0].strip()} vs {parts[1].strip()}"
                
                # Calculate market implied probability if we have odds
                if bet.odds:
                    try:
                        odds = float(bet.odds)
                        if odds > 0:
                            bet.market_implied_prob = 100 / (odds + 100) * 100
                        else:
                            bet.market_implied_prob = abs(odds) / (abs(odds) + 100) * 100
                    except (ValueError, ZeroDivisionError):
                        bet.market_implied_prob = None
                
                # Calculate edge if we have win_probability and market_implied_prob
                if bet.win_probability and bet.market_implied_prob:
                    bet.edge = bet.win_probability - bet.market_implied_prob
            
            if include_grades and bets:
                # Get grades for these bets
                bet_ids = [bet.bet_id for bet in bets]
                logger.info(f"Fetching grades for {len(bet_ids)} bets in get_bets_by_sportsbook")
                
                # Get all grades ordered by calculated_at in descending order
                grades_result = execute_query(
                    table_name="bet_grades",
                    query_type="select",
                    order={"calculated_at": "desc"}
                )
                
                logger.info(f"Retrieved {len(grades_result)} grades from database in get_bets_by_sportsbook")
                
                # Create a lookup dictionary for grades
                # Only keep the most recent grade for each bet_id
                grade_lookup = {}
                for row in grades_result:
                    bet_id = row.get("bet_id")
                    if bet_id in bet_ids and bet_id not in grade_lookup:
                        grade_lookup[bet_id] = BetGrade.from_dict(row)
                
                logger.info(f"Created grade lookup with {len(grade_lookup)} entries in get_bets_by_sportsbook")
                logger.info(f"Found grades for {len(grade_lookup)}/{len(bet_ids)} bets in get_bets_by_sportsbook")
                
                # Attach grades to bets
                for bet in bets:
                    bet.grade = grade_lookup.get(bet.bet_id)
                    if bet.grade:
                        logger.info(f"Attached grade {bet.grade.grade} with score {bet.grade.composite_score} to bet {bet.bet_id} in get_bets_by_sportsbook")
                
                # Count grades by type
                grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "None": 0}
                for bet in bets:
                    if bet.grade and bet.grade.grade:
                        grade_counts[bet.grade.grade] += 1
                    else:
                        grade_counts["None"] += 1
                
                logger.info(f"Grade distribution after attachment in get_bets_by_sportsbook: {grade_counts}")
                
                # Sort bets by grade (A > B > C > D > F)
                grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, None: 5}
                bets.sort(key=lambda x: (grade_order.get(x.grade.grade if x.grade else None, 5)))
            
            # Manually group bets by sportsbook
            grouped_bets = {}
            for bet in bets:
                if bet.sportsbook not in grouped_bets:
                    grouped_bets[bet.sportsbook] = []
                grouped_bets[bet.sportsbook].append(bet)
            
            # Log grouped bets
            for sportsbook, bets in grouped_bets.items():
                logger.info(f"BetService: {len(bets)} bets grouped under sportsbook {sportsbook}")
            
            # Return bets for the specified sportsbook
            return grouped_bets.get(sportsbook, [])
        except Exception as e:
            logger.error(f"Error getting bets by sportsbook: {str(e)}")
            return []
    
    @staticmethod
    def get_grades_by_bet_ids(bet_ids):
        """
        Get grades for a list of bet IDs.
        
        Args:
            bet_ids (list): List of bet IDs.
            
        Returns:
            list: List of grades for the bet IDs.
        """
        try:
            if not bet_ids:
                return []
            
            logger.info(f"Fetching grades for {len(bet_ids)} bet IDs in get_grades_by_bet_ids")
            
            # Get all grades ordered by calculated_at in descending order
            result = execute_query(
                table_name="bet_grades",
                query_type="select",
                order={"calculated_at": "desc"}
            )
            
            logger.info(f"Retrieved {len(result)} grades from database in get_grades_by_bet_ids")
            
            # Create a lookup dictionary to keep only the most recent grade for each bet_id
            grade_lookup = {}
            for row in result:
                bet_id = row.get("bet_id")
                if bet_id in bet_ids and bet_id not in grade_lookup:
                    grade_lookup[bet_id] = row
            
            logger.info(f"Found grades for {len(grade_lookup)}/{len(bet_ids)} bets in get_grades_by_bet_ids")
            
            # Convert to list of BetGrade objects
            return [BetGrade.from_dict(grade_lookup[bet_id]) for bet_id in bet_ids if bet_id in grade_lookup]
        except Exception as e:
            logger.error(f"Error getting grades by bet IDs: {str(e)}")
            return []
    
    @staticmethod
    def calculate_summary_statistics(bets):
        """Calculate summary statistics for a list of bets."""
        now = datetime.now(pytz.UTC)
        
        # Initialize statistics
        stats = {
            'total_bets': len(bets),
            'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
            'sportsbook_distribution': {},
            'time_distribution': {
                'Immediate': 0,  # <1h
                'VeryUrgent': 0,  # 1-3h
                'Urgent': 0,      # 3-6h
                'Monitor': 0,     # 6-12h
                'Plan': 0         # >12h
            },
            'latest_timestamp': None
        }
        
        # Process each bet
        for bet in bets:
            # Grade distribution
            if hasattr(bet, 'grade') and bet.grade and bet.grade.grade:
                stats['grade_distribution'][bet.grade.grade] = stats['grade_distribution'].get(bet.grade.grade, 0) + 1
            
            # Sportsbook distribution
            if bet.sportsbook:
                stats['sportsbook_distribution'][bet.sportsbook] = stats['sportsbook_distribution'].get(bet.sportsbook, 0) + 1
            
            # Time distribution
            if bet.event_time and isinstance(bet.event_time, datetime):
                time_diff = (bet.event_time - now).total_seconds() / 3600  # Convert to hours
                if time_diff <= 0:
                    continue  # Skip expired events
                elif time_diff <= 1:
                    stats['time_distribution']['Immediate'] += 1
                elif time_diff <= 3:
                    stats['time_distribution']['VeryUrgent'] += 1
                elif time_diff <= 6:
                    stats['time_distribution']['Urgent'] += 1
                elif time_diff <= 12:
                    stats['time_distribution']['Monitor'] += 1
                else:
                    stats['time_distribution']['Plan'] += 1
            
            # Track latest timestamp
            if bet.timestamp:
                if not stats['latest_timestamp'] or bet.timestamp > stats['latest_timestamp']:
                    stats['latest_timestamp'] = bet.timestamp
        
        return stats
    
    @staticmethod
    def get_sportsbook_counts():
        """
        Get counts of bets by sportsbook from the latest timestamp.
        
        Returns:
            dict: Dictionary mapping sportsbook names to bet counts.
        """
        try:
            # Get most recent timestamp first
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            
            if not timestamp_result:
                return {}
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            
            # Get bets from latest timestamp
            active_bets = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"timestamp": latest_timestamp}
            )
            
            # Count bets by sportsbook
            sportsbook_counts = {}
            for bet in active_bets:
                if bet.get('sportsbook'):
                    sportsbook_counts[bet['sportsbook']] = sportsbook_counts.get(bet['sportsbook'], 0) + 1
            
            return sportsbook_counts
        except Exception as e:
            logger.error(f"Error getting sportsbook counts: {str(e)}")
            return {} 