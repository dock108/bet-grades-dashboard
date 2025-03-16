"""
Betting service for the application.
This module provides services for retrieving and processing betting data.
"""
import logging
from app.core.database import execute_query
from app.models.betting import Bet, BetGrade
from datetime import datetime

logger = logging.getLogger(__name__)

class BettingService:
    """Service for retrieving and processing betting data."""
    
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
            
            bets = []
            for row in result:
                try:
                    bet = Bet.from_dict(row)
                    
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
            # Get most recent timestamp first
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            
            if not timestamp_result:
                return []
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            
            # Use the Bet model's get_by_sportsbook method which already handles include_resolved
            bets = Bet.get_by_sportsbook(sportsbook, include_resolved=include_resolved)
            
            # Filter to only include bets from the latest timestamp
            bets = [bet for bet in bets if bet.timestamp == latest_timestamp]
            
            logger.info(f"Found {len(bets)} bets for sportsbook {sportsbook} (include_resolved={include_resolved})")
            
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
            
            return bets
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
        """
        Calculate summary statistics for a list of bets.
        
        Args:
            bets (list): List of Bet objects.
            
        Returns:
            dict: Dictionary of summary statistics.
        """
        logger = logging.getLogger(__name__)
        
        # Initialize empty stats with all possible values
        empty_stats = {
            "total_bets": 0,
            "average_ev": 0,
            "average_edge": 0,
            "sportsbooks": [],
            "grade_distribution": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "F": 0
            },
            "sportsbook_distribution": {},
            "time_distribution": {
                "Early": 0,
                "Mid": 0,
                "Late": 0
            },
            "latest_timestamp": None
        }
        
        if not bets:
            # Get most recent timestamp from betting_data table
            try:
                timestamp_result = execute_query(
                    table_name="betting_data",
                    query_type="select",
                    order={"timestamp": "desc"},
                    limit=1
                )
                
                if timestamp_result and len(timestamp_result) > 0:
                    latest_timestamp = timestamp_result[0].get('timestamp')
                    empty_stats["latest_timestamp"] = latest_timestamp
                    logger.info(f"Got latest timestamp from database: {latest_timestamp}")
            except Exception as e:
                logger.error(f"Error getting latest timestamp: {str(e)}")
                
            return empty_stats
        
        total_bets = len(bets)
        total_ev = sum(float(bet.ev_percent or 0) for bet in bets)
        average_ev = total_ev / total_bets if total_bets > 0 else 0
        
        # Get latest timestamp from the first bet (since they're already sorted by timestamp desc)
        latest_timestamp = None
        if bets:
            latest_timestamp = bets[0].timestamp
            logger.info(f"Latest timestamp from first bet: {latest_timestamp}")
        else:
            # If no bets provided, get the latest timestamp from the database
            try:
                timestamp_result = execute_query(
                    table_name="betting_data",
                    query_type="select",
                    order={"timestamp": "desc"},
                    limit=1
                )
                
                if timestamp_result and len(timestamp_result) > 0:
                    latest_timestamp = timestamp_result[0].get('timestamp')
                    logger.info(f"Got latest timestamp from database: {latest_timestamp}")
            except Exception as e:
                logger.error(f"Error getting latest timestamp: {str(e)}")
        
        # Calculate edge (market implied probability - win probability)
        total_edge = 0
        valid_edge_bets = 0
        
        for bet in bets:
            if bet.odds and bet.win_probability:
                try:
                    odds = float(bet.odds)
                    win_prob = float(bet.win_probability)
                    
                    # Calculate market implied probability
                    if odds > 0:
                        market_prob = 100 / (odds + 100)
                    else:
                        market_prob = abs(odds) / (abs(odds) + 100)
                    
                    edge = win_prob - market_prob
                    total_edge += edge
                    valid_edge_bets += 1
                except (ValueError, ZeroDivisionError):
                    pass
        
        average_edge = total_edge / valid_edge_bets if valid_edge_bets > 0 else 0
        
        # Get unique sportsbooks
        sportsbooks = list(set(bet.sportsbook for bet in bets if bet.sportsbook))
        
        # Calculate grade distribution (starting with empty distribution)
        grade_distribution = empty_stats["grade_distribution"].copy()
        logger.info(f"Starting grade distribution calculation with {len(bets)} bets")

        for bet in bets:
            if hasattr(bet, 'grade') and bet.grade and hasattr(bet.grade, 'grade'):
                grade = bet.grade.grade
                if grade in grade_distribution:
                    grade_distribution[grade] += 1
                    logger.info(f"Counted grade {grade} for bet {bet.bet_id}")
            else:
                logger.info(f"Bet {bet.bet_id} has no grade or grade attribute")

        logger.info(f"Final grade distribution: {grade_distribution}")
        
        # Calculate sportsbook distribution
        sportsbook_distribution = {}
        for bet in bets:
            if bet.sportsbook:
                sportsbook_distribution[bet.sportsbook] = sportsbook_distribution.get(bet.sportsbook, 0) + 1
        
        # Calculate time distribution (starting with empty distribution)
        time_distribution = empty_stats["time_distribution"].copy()
        now = datetime.now()
        
        for bet in bets:
            if bet.event_time:
                try:
                    # Ensure event_time is a datetime
                    event_time = bet.event_time
                    if isinstance(event_time, str):
                        # Try different formats for parsing the string
                        try:
                            # Try the format with seconds
                            event_time = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S")
                        except ValueError:
                            try:
                                # Try the format without seconds
                                event_time = datetime.strptime(event_time, "%Y-%m-%d %H:%M")
                            except ValueError:
                                # If all parsing fails, log and continue
                                logger.warning(f"Could not parse event_time: {event_time} for bet {bet.bet_id}")
                                continue
                    
                    time_diff = event_time - now
                    hours_until_event = time_diff.total_seconds() / 3600
                    
                    if hours_until_event > 12:
                        time_distribution["Early"] += 1
                    elif hours_until_event > 6:
                        time_distribution["Mid"] += 1
                    else:
                        time_distribution["Late"] += 1
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error calculating time distribution for bet {bet.bet_id}: {str(e)}")
                    continue
        
        # Format latest timestamp for display
        formatted_timestamp = None
        if latest_timestamp:
            try:
                if isinstance(latest_timestamp, str):
                    # Try to parse the string to a datetime
                    try:
                        if 'T' in latest_timestamp:
                            # Handle ISO format with T separator
                            dt_str = latest_timestamp.replace('T', ' ')
                            if '.' in dt_str:
                                dt_str = dt_str.split('.')[0]  # Remove microseconds
                            formatted_timestamp = dt_str
                        else:
                            # Try to parse as datetime and format
                            dt = datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S")
                            formatted_timestamp = dt.strftime("%Y-%m-%d %I:%M %p")
                    except ValueError:
                        # If parsing fails, use the string as is
                        formatted_timestamp = latest_timestamp
                else:
                    # Convert to string format for display
                    formatted_timestamp = latest_timestamp.strftime("%Y-%m-%d %I:%M %p")
                logger.info(f"Formatted timestamp: {formatted_timestamp}")
            except Exception as e:
                logger.error(f"Error formatting timestamp: {str(e)}")
        
        return {
            "total_bets": total_bets,
            "average_ev": average_ev,
            "average_edge": average_edge,
            "sportsbooks": sportsbooks,
            "grade_distribution": grade_distribution,
            "sportsbook_distribution": sportsbook_distribution,
            "time_distribution": time_distribution,
            "latest_timestamp": formatted_timestamp
        }
    
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