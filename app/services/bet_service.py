"""
Betting service layer.
This module contains business logic for processing and managing bets.
"""
import logging
from app.core.database import execute_query
from app.models.bet_models import Bet, BetGrade
from datetime import datetime, timedelta
import pytz
import time

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
        start_time = time.time()
        bets = []
        est = pytz.timezone('America/New_York')
        
        try:
            # Get most recent timestamp first
            timestamp_query_start = time.time()
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            logger.info(f"get_active_bets: timestamp query - {time.time() - timestamp_query_start:.2f}s")
            
            if not timestamp_result:
                logger.warning("No timestamps found in betting_data")
                return []
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            logger.info(f"Latest timestamp: {latest_timestamp}")
            
            # Get bets from the latest timestamp
            bets_query_start = time.time()
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"timestamp": latest_timestamp},
                order={"timestamp": "desc"},
                limit=limit
            )
            logger.info(f"get_active_bets: bets query - {time.time() - bets_query_start:.2f}s")
            
            logger.info(f"Found {len(result)} bets from latest timestamp {latest_timestamp}")
            # if result:
            #    logger.info(f"Sample bet data: {result[0]}")
            
            bet_object_creation_start = time.time()
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
                        except (ValueError, TypeError):
                            # If parsing fails, leave it as is
                            pass
                    
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
                    logger.warning(f"Error creating bet from row: {str(e)}")
            logger.info(f"get_active_bets: bet object creation - {time.time() - bet_object_creation_start:.2f}s")
            
            logger.info(f"Created {len(bets)} bet objects")
            
            if include_grades and bets:
                # Get grades for these bets
                grades_query_start = time.time()
                bet_ids = [bet.bet_id for bet in bets]
                logger.info(f"Fetching grades for {len(bet_ids)} bets")
                
                # Get the latest timestamp and convert to datetime for comparison
                try:
                    latest_ts_dt = datetime.fromisoformat(latest_timestamp.replace('T', ' ').split('.')[0])
                    # Calculate cutoff time (5 minutes before latest timestamp)
                    cutoff_time = latest_ts_dt - timedelta(minutes=5)
                    cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"Using cutoff time for grades: {cutoff_time_str} (5 min before latest betting data)")
                    
                    # Since we can't use custom SQL, fall back to the regular query
                    # This may not be as optimized but should still work with the time filter
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={
                            "bet_id": {"operator": "in", "value": bet_ids},
                            "calculated_at": {"operator": ">=", "value": cutoff_time_str}
                        },
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades after time filter")
                    
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error parsing timestamp for optimization, falling back to regular query: {e}")
                    # Fallback to the regular query if timestamp parsing fails
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={"bet_id": {"operator": "in", "value": bet_ids}},
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades using fallback query")
                logger.info(f"get_active_bets: grades query - {time.time() - grades_query_start:.2f}s")
                
                # Create a lookup dictionary for grades - only keep the most recent grade for each bet_id
                grade_lookup_start = time.time()
                grade_lookup = {}
                for row in grades_result:
                    bet_id = row.get("bet_id")
                    if bet_id in bet_ids and bet_id not in grade_lookup:
                        # Store the raw row instead of creating a BetGrade object here
                        grade_lookup[bet_id] = row
                
                logger.info(f"Created grade lookup with {len(grade_lookup)} entries after filtering to most recent")
                
                # Attach grades to bets
                for bet in bets:
                    if bet.bet_id in grade_lookup:
                        # Only create BetGrade object when attaching to bet
                        bet.grade = BetGrade.from_dict(grade_lookup[bet.bet_id])
                    else:
                        bet.grade = None
                logger.info(f"get_active_bets: grade lookup and attachment - {time.time() - grade_lookup_start:.2f}s")
                
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
                bets.sort(key=lambda x: (
                    grade_order.get(x.grade.grade if hasattr(x, 'grade') and x.grade else None, 5),
                    -(x.grade.composite_score if hasattr(x, 'grade') and x.grade and hasattr(x.grade, 'composite_score') else 0)
                ))
            
            # Fetch initial bet details for all bets
            if bets:
                initial_details_start = time.time()
                bet_ids = [bet.bet_id for bet in bets]
                
                # Log the bet IDs we're looking for
                # logger.info(f"Looking for initial details for bet_ids: {bet_ids[:5]}...")
                
                # Initial bet details uses 'in' operator instead of exact match for arrays
                initial_details_result = execute_query(
                    table_name="initial_bet_details",
                    query_type="select",
                    filters={"bet_id": {"operator": "in", "value": bet_ids}}
                )
                
                # Create a lookup dictionary for initial details
                initial_details_lookup = {}
                for row in initial_details_result:
                    bet_id = row.get("bet_id")
                    if bet_id:
                        initial_details_lookup[bet_id] = row
                
                logger.info(f"Retrieved initial details for {len(initial_details_lookup)}/{len(bet_ids)} bets")
                
                # Attach initial details to bets
                for bet in bets:
                    initial_details = initial_details_lookup.get(bet.bet_id)
                    if initial_details:
                        bet.initial_odds = initial_details.get('initial_odds')
                        bet.initial_ev = initial_details.get('initial_ev')
                        bet.initial_line = initial_details.get('initial_line')
                        bet.first_seen = initial_details.get('first_seen')
                        
                        # Calculate EV change if current and initial EV are available
                        if bet.ev_percent is not None and bet.initial_ev is not None:
                            try:
                                bet.ev_change = float(bet.ev_percent) - float(bet.initial_ev)
                            except (ValueError, TypeError):
                                # logger.warning(f"Could not calculate EV change for bet {bet.bet_id}")
                                bet.ev_change = None
                logger.info(f"get_active_bets: initial details processing - {time.time() - initial_details_start:.2f}s")
            
            logger.info(f"get_active_bets: total execution time - {time.time() - start_time:.2f}s")
            return bets
        except Exception as e:
            logger.error(f"Error getting active bets: {str(e)}")
            logger.info(f"get_active_bets: failed execution time - {time.time() - start_time:.2f}s")
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
        start_time = time.time()
        try:
            logger.info(f"BetService: Getting bets for sportsbook: {sportsbook}")
            
            # Get most recent timestamp first
            timestamp_query_start = time.time()
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            logger.info(f"get_bets_by_sportsbook: timestamp query - {time.time() - timestamp_query_start:.2f}s")
            
            if not timestamp_result:
                logger.warning(f"BetService: No timestamps found in betting_data for {sportsbook}")
                return []
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            logger.info(f"BetService: Latest timestamp: {latest_timestamp}")
            
            # Use the Bet model's get_by_sportsbook method which already handles include_resolved
            bets_query_start = time.time()
            bets = Bet.get_by_sportsbook(sportsbook, include_resolved=include_resolved)
            logger.info(f"get_bets_by_sportsbook: bets query - {time.time() - bets_query_start:.2f}s")
            logger.info(f"BetService: Found {len(bets)} total bets for sportsbook {sportsbook}")
            
            # Filter to only include bets from the latest timestamp
            filtering_start = time.time()
            bets = [bet for bet in bets if bet.timestamp == latest_timestamp]
            logger.info(f"BetService: After filtering for latest timestamp, found {len(bets)} bets for sportsbook {sportsbook}")
            logger.info(f"get_bets_by_sportsbook: filtering bets - {time.time() - filtering_start:.2f}s")
            
            # Log sportsbooks in the database
            sportsbooks_query_start = time.time()
            all_sportsbooks = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={}
            )
            
            sportsbooks = set()
            for row in all_sportsbooks:
                if 'sportsbook' in row and row['sportsbook']:
                    sportsbooks.add(row['sportsbook'])
            
            logger.info(f"BetService: Available sportsbooks: {sorted(list(sportsbooks))}")
            logger.info(f"get_bets_by_sportsbook: sportsbooks query - {time.time() - sportsbooks_query_start:.2f}s")
            
            if include_grades and bets:
                # Get grades for these bets
                grades_query_start = time.time()
                bet_ids = [bet.bet_id for bet in bets]
                logger.info(f"Fetching grades for {len(bet_ids)} bets in get_bets_by_sportsbook")
                
                # Get the latest timestamp and convert to datetime for comparison
                try:
                    latest_ts_dt = datetime.fromisoformat(latest_timestamp.replace('T', ' ').split('.')[0])
                    # Calculate cutoff time (5 minutes before latest timestamp)
                    cutoff_time = latest_ts_dt - timedelta(minutes=5)
                    cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"Using cutoff time for grades: {cutoff_time_str} (5 min before latest betting data)")
                    
                    # Since we can't use custom SQL, fall back to the regular query
                    # This may not be as optimized but should still work with the time filter
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={
                            "bet_id": {"operator": "in", "value": bet_ids},
                            "calculated_at": {"operator": ">=", "value": cutoff_time_str}
                        },
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades after time filter")
                    
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error parsing timestamp for optimization, falling back to regular query: {e}")
                    # Fallback to the regular query if timestamp parsing fails
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={"bet_id": {"operator": "in", "value": bet_ids}},
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades using fallback query")
                logger.info(f"get_bets_by_sportsbook: grades query - {time.time() - grades_query_start:.2f}s")
                
                # Create a lookup dictionary for grades - only keep the most recent grade for each bet_id
                grade_attachment_start = time.time()
                grade_lookup = {}
                for row in grades_result:
                    bet_id = row.get("bet_id")
                    if bet_id in bet_ids and bet_id not in grade_lookup:
                        # Store the raw row instead of creating a BetGrade object here
                        grade_lookup[bet_id] = row
                
                logger.info(f"Created grade lookup with {len(grade_lookup)} entries after filtering to most recent")
                
                # Attach grades to bets
                for bet in bets:
                    if bet.bet_id in grade_lookup:
                        # Only create BetGrade object when attaching to bet
                        bet.grade = BetGrade.from_dict(grade_lookup[bet.bet_id])
                    else:
                        bet.grade = None
                
                # Count grades by type
                grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "None": 0}
                for bet in bets:
                    if bet.grade and bet.grade.grade:
                        grade_counts[bet.grade.grade] += 1
                    else:
                        grade_counts["None"] += 1
                
                logger.info(f"Grade distribution after attachment in get_bets_by_sportsbook: {grade_counts}")
                logger.info(f"get_bets_by_sportsbook: grade attachment - {time.time() - grade_attachment_start:.2f}s")
                
                # Sort bets by grade (A > B > C > D > F)
                sort_start = time.time()
                grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, None: 5}
                bets.sort(key=lambda x: (
                    grade_order.get(x.grade.grade if hasattr(x, 'grade') and x.grade else None, 5),
                    -(x.grade.composite_score if hasattr(x, 'grade') and x.grade and hasattr(x.grade, 'composite_score') else 0)
                ))
                logger.info(f"get_bets_by_sportsbook: sorting - {time.time() - sort_start:.2f}s")
            
            # Manually group bets by sportsbook
            grouping_start = time.time()
            grouped_bets = {}
            for bet in bets:
                if bet.sportsbook not in grouped_bets:
                    grouped_bets[bet.sportsbook] = []
                grouped_bets[bet.sportsbook].append(bet)
            
            # Log grouped bets
            for sportsbook, sb_bets in grouped_bets.items():
                logger.info(f"BetService: {len(sb_bets)} bets grouped under sportsbook {sportsbook}")
            logger.info(f"get_bets_by_sportsbook: grouping - {time.time() - grouping_start:.2f}s")
            
            # Return bets for the specified sportsbook
            logger.info(f"get_bets_by_sportsbook: total execution time - {time.time() - start_time:.2f}s")
            return grouped_bets.get(sportsbook, [])
        except Exception as e:
            logger.error(f"Error getting bets by sportsbook: {str(e)}")
            logger.info(f"get_bets_by_sportsbook: failed execution time - {time.time() - start_time:.2f}s")
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
        start_time = time.time()
        try:
            if not bet_ids:
                return []
            
            logger.info(f"Fetching grades for {len(bet_ids)} bet IDs in get_grades_by_bet_ids")
            
            # Get most recent timestamp first to calculate cutoff time
            timestamp_query_start = time.time()
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            logger.info(f"get_grades_by_bet_ids: timestamp query - {time.time() - timestamp_query_start:.2f}s")
            
            grades_query_start = time.time()
            if timestamp_result:
                latest_timestamp = timestamp_result[0].get('timestamp')
                # Convert to datetime for comparison
                try:
                    latest_ts_dt = datetime.fromisoformat(latest_timestamp.replace('T', ' ').split('.')[0])
                    # Calculate cutoff time (5 minutes before latest timestamp)
                    cutoff_time = latest_ts_dt - timedelta(minutes=5)
                    cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"Using cutoff time for grades: {cutoff_time_str} (5 min before latest betting data)")
                    
                    # Since we can't use custom SQL, fall back to the regular query
                    # This may not be as optimized but should still work with the time filter
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={
                            "bet_id": {"operator": "in", "value": bet_ids},
                            "calculated_at": {"operator": ">=", "value": cutoff_time_str}
                        },
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades after time filter")
                    
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error parsing timestamp for optimization, falling back to regular query: {e}")
                    # Fallback to the regular query if timestamp parsing fails
                    grades_result = execute_query(
                        table_name="bet_grades",
                        query_type="select",
                        filters={"bet_id": {"operator": "in", "value": bet_ids}},
                        order={"calculated_at": "desc"}
                    )
                    logger.info(f"Retrieved {len(grades_result)} grades using fallback query")
            else:
                # Fallback if no timestamp found
                logger.warning("No latest timestamp found, using all grades")
                grades_result = execute_query(
                    table_name="bet_grades",
                    query_type="select",
                    filters={"bet_id": {"operator": "in", "value": bet_ids}},
                    order={"calculated_at": "desc"}
                )
                logger.info(f"Retrieved {len(grades_result)} grades (no timestamp)")
            logger.info(f"get_grades_by_bet_ids: grades query - {time.time() - grades_query_start:.2f}s")
            
            # Create a lookup dictionary for grades - only keep the most recent grade for each bet_id
            processing_start = time.time()
            grade_lookup = {}
            for row in grades_result:
                bet_id = row.get("bet_id")
                if bet_id in bet_ids and bet_id not in grade_lookup:
                    grade_lookup[bet_id] = row
            
            logger.info(f"Created grade lookup with {len(grade_lookup)} entries after filtering to most recent")
            
            # Convert to list of BetGrade objects
            result = []
            for bet_id in bet_ids:
                if bet_id in grade_lookup:
                    result.append(BetGrade.from_dict(grade_lookup[bet_id]))
            
            logger.info(f"get_grades_by_bet_ids: processing - {time.time() - processing_start:.2f}s")
            logger.info(f"get_grades_by_bet_ids: total execution time - {time.time() - start_time:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"Error getting grades by bet IDs: {str(e)}")
            logger.info(f"get_grades_by_bet_ids: failed execution time - {time.time() - start_time:.2f}s")
            return []
    
    @staticmethod
    def calculate_summary_statistics(bets):
        """Calculate summary statistics for a list of bets."""
        start_time = time.time()
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
        
        try:
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
            
            logger.info(f"calculate_summary_statistics: execution time - {time.time() - start_time:.2f}s")
            return stats
        except Exception as e:
            logger.error(f"Error calculating summary statistics: {str(e)}")
            logger.info(f"calculate_summary_statistics: failed execution time - {time.time() - start_time:.2f}s")
            return stats
    
    @staticmethod
    def get_sportsbook_counts():
        """
        Get counts of bets by sportsbook from the latest timestamp.
        
        Returns:
            dict: Dictionary mapping sportsbook names to bet counts.
        """
        start_time = time.time()
        try:
            # Get most recent timestamp first
            timestamp_query_start = time.time()
            timestamp_result = execute_query(
                table_name="betting_data",
                query_type="select",
                order={"timestamp": "desc"},
                limit=1
            )
            logger.info(f"get_sportsbook_counts: timestamp query - {time.time() - timestamp_query_start:.2f}s")
            
            if not timestamp_result:
                return {}
                
            latest_timestamp = timestamp_result[0].get('timestamp')
            
            # Get bets from latest timestamp
            bets_query_start = time.time()
            active_bets = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"timestamp": latest_timestamp}
            )
            logger.info(f"get_sportsbook_counts: bets query - {time.time() - bets_query_start:.2f}s")
            
            # Count bets by sportsbook
            counting_start = time.time()
            sportsbook_counts = {}
            for bet in active_bets:
                if bet.get('sportsbook'):
                    sportsbook_counts[bet['sportsbook']] = sportsbook_counts.get(bet['sportsbook'], 0) + 1
            logger.info(f"get_sportsbook_counts: counting - {time.time() - counting_start:.2f}s")
            
            logger.info(f"get_sportsbook_counts: total execution time - {time.time() - start_time:.2f}s")
            return sportsbook_counts
        except Exception as e:
            logger.error(f"Error getting sportsbook counts: {str(e)}")
            logger.info(f"get_sportsbook_counts: failed execution time - {time.time() - start_time:.2f}s")
            return {} 