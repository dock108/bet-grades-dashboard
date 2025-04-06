"""
Data models for betting entities.
This module contains the core data structures for bets and grades.
"""
from datetime import datetime
import pytz
from app.core.database import execute_query

class Bet:
    """Model representing a betting opportunity."""
    
    def __init__(self, id=None, bet_id=None, timestamp=None, ev_percent=None, event_time=None,
                 home_team=None, away_team=None, sport=None, league=None, description=None, participant=None,
                 bet_line=None, bet_type=None, bet_category=None, odds=None, 
                 sportsbook=None, bet_size=None, win_probability=None, edge=None,
                 market_implied_prob=None, betid_timestamp=None, created_at=None, updated_at=None,
                 initial_odds=None, initial_ev=None, initial_line=None, first_seen=None, ev_change=None):
        self.id = id
        self.bet_id = bet_id
        self.timestamp = timestamp  # Keep timestamp as is - already in correct timezone
        self.ev_percent = float(ev_percent) if ev_percent is not None else None
        
        # Handle event_time with timezone
        est = pytz.timezone('America/New_York')
        if event_time:
            if isinstance(event_time, str):
                try:
                    # Try different formats for parsing the string
                    try:
                        # Try the format with seconds
                        naive_dt = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S")
                        self.event_time = est.localize(naive_dt)
                    except ValueError:
                        try:
                            # Try the format without seconds
                            naive_dt = datetime.strptime(event_time, "%Y-%m-%d %H:%M")
                            self.event_time = est.localize(naive_dt)
                        except ValueError:
                            # If all parsing fails, keep as string
                            self.event_time = event_time
                except (ValueError, TypeError):
                    # If parsing fails, keep as string
                    self.event_time = event_time
            elif isinstance(event_time, datetime):
                if event_time.tzinfo is None:
                    # If it's a naive datetime, localize it
                    self.event_time = est.localize(event_time)
                else:
                    # If it already has timezone info, keep it as is
                    self.event_time = event_time
            else:
                self.event_time = event_time
        else:
            self.event_time = None
        
        self.home_team = home_team
        self.away_team = away_team
        self.sport = sport
        self.league = league
        self.description = description
        self.participant = participant
        # Handle bet_line properly - convert string "None" to None
        self.bet_line = None if bet_line == "None" else bet_line
        self.bet_type = bet_type
        self.bet_category = bet_category
        self.odds = float(odds) if odds is not None else None
        self.sportsbook = sportsbook
        self.bet_size = float(bet_size) if bet_size is not None else None
        self.win_probability = float(win_probability) if win_probability is not None else None
        self.edge = float(edge) if edge is not None else None
        self.market_implied_prob = float(market_implied_prob) if market_implied_prob is not None else None
        self.betid_timestamp = betid_timestamp or f"{bet_id}:{timestamp}" if bet_id and timestamp else None
        self.created_at = created_at
        self.updated_at = updated_at
        self.grade = None  # Will be set later if needed
        
        # Initial bet details
        self.initial_odds = initial_odds
        self.initial_ev = float(initial_ev) if initial_ev is not None else None
        self.initial_line = initial_line
        self.first_seen = first_seen
        self.ev_change = float(ev_change) if ev_change is not None else None
        
        # Set event_teams based on home_team and away_team if available
        if self.home_team and self.away_team:
            self.event_teams = f"{self.home_team} vs {self.away_team}"
        else:
            self.event_teams = None
            # Try to extract event teams from description
            if self.description and ("vs" in self.description or "vs." in self.description):
                parts = self.description.replace("vs.", "vs").split("vs")
                if len(parts) >= 2:
                    self.event_teams = f"{parts[0].strip()} vs {parts[1].strip()}"
    
    @classmethod
    def from_dict(cls, data):
        """Create a Bet instance from a dictionary."""
        # Remove any fields that aren't in our model
        valid_fields = {
            'id', 'bet_id', 'timestamp', 'ev_percent', 'event_time', 'home_team', 'away_team',
            'sport', 'league', 'description', 'participant', 'bet_line', 'bet_type', 
            'bet_category', 'odds', 'sportsbook', 'bet_size', 'win_probability', 'edge', 
            'market_implied_prob', 'betid_timestamp', 'created_at', 'updated_at',
            'initial_odds', 'initial_ev', 'initial_line', 'first_seen', 'ev_change'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Handle bet_line specifically to convert "None" string to None
        if 'bet_line' in filtered_data and filtered_data['bet_line'] == "None":
            filtered_data['bet_line'] = None
            
        return cls(**filtered_data)
    
    @classmethod
    def from_db_row(cls, row):
        """Create a Bet instance from a database row."""
        if row is None:
            return None
        return cls.from_dict(dict(row))
    
    @classmethod
    def get_by_id(cls, bet_id):
        """Get a bet by its ID."""
        try:
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"bet_id": bet_id}
            )
            
            if result and len(result) > 0:
                return cls.from_dict(result[0])
            return None
        except Exception as e:
            print(f"Error getting bet by ID: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, limit=None, order_by=None):
        """Get all bets, optionally limited and ordered."""
        try:
            order = None
            if order_by:
                # Parse order_by string (e.g., "timestamp DESC")
                parts = order_by.split()
                if len(parts) >= 2:
                    field, direction = parts[0], parts[1].lower()
                    order = {field: direction}
                else:
                    order = {parts[0]: "asc"}
            
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                order=order,
                limit=limit
            )
            
            return [cls.from_dict(row) for row in result]
        except Exception as e:
            print(f"Error getting all bets: {str(e)}")
            return []
    
    @classmethod
    def get_by_sportsbook(cls, sportsbook, include_resolved=False):
        """Get all bets for a specific sportsbook."""
        try:
            filters = {"sportsbook": sportsbook}
            
            # Remove the result filter since the column doesn't exist
            # We'll handle resolved/unresolved bets in a different way if needed
            
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                filters=filters,
                order={"timestamp": "desc"}
            )
            
            return [cls.from_dict(row) for row in result]
        except Exception as e:
            print(f"Error getting bets by sportsbook: {str(e)}")
            return []
    
    def save(self):
        """Save the bet to the database."""
        try:
            # Ensure betid_timestamp is set
            if not self.betid_timestamp and self.bet_id and self.timestamp:
                self.betid_timestamp = f"{self.bet_id}:{self.timestamp}"
                
            data = {
                "id": self.id,
                "bet_id": self.bet_id,
                "timestamp": self.timestamp,
                "ev_percent": self.ev_percent,
                "event_time": self.event_time,
                "home_team": self.home_team,
                "away_team": self.away_team,
                "sport": self.sport,
                "league": self.league,
                "description": self.description,
                "participant": self.participant,
                "bet_line": self.bet_line,
                "bet_type": self.bet_type,
                "bet_category": self.bet_category,
                "odds": self.odds,
                "sportsbook": self.sportsbook,
                "bet_size": self.bet_size,
                "win_probability": self.win_probability,
                "edge": self.edge,
                "market_implied_prob": self.market_implied_prob,
                "betid_timestamp": self.betid_timestamp,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "initial_odds": self.initial_odds,
                "initial_ev": self.initial_ev,
                "initial_line": self.initial_line,
                "first_seen": self.first_seen,
                "ev_change": self.ev_change
            }
            
            # Handle bet_line specifically to avoid saving "None" string
            if data.get("bet_line") == "None":
                data["bet_line"] = None
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            if self.bet_id:
                # Update existing bet
                execute_query(
                    table_name="betting_data",
                    query_type="update",
                    filters={"bet_id": self.bet_id},
                    data=data
                )
                
                # Save initial bet details (will only insert if bet_id doesn't exist due to ON CONFLICT DO NOTHING)
                if self.ev_percent is not None or self.bet_line is not None or self.odds is not None:
                    initial_data = {
                        "bet_id": self.bet_id,
                        "initial_ev": float(self.ev_percent.replace('%', '')) if isinstance(self.ev_percent, str) else self.ev_percent,
                        "initial_line": self.bet_line,
                        "first_seen": self.timestamp,
                        "initial_odds": str(self.odds) if self.odds is not None else None
                    }
                    execute_query(
                        table_name="initial_bet_details",
                        query_type="insert",
                        data=initial_data
                    )
            else:
                # Insert new bet
                execute_query(
                    table_name="betting_data",
                    query_type="insert",
                    data=data
                )
                
                # Save initial bet details for new bet
                if self.ev_percent is not None or self.bet_line is not None or self.odds is not None:
                    initial_data = {
                        "bet_id": data["bet_id"],
                        "initial_ev": float(self.ev_percent.replace('%', '')) if isinstance(self.ev_percent, str) else self.ev_percent,
                        "initial_line": self.bet_line,
                        "first_seen": self.timestamp,
                        "initial_odds": str(self.odds) if self.odds is not None else None
                    }
                    execute_query(
                        table_name="initial_bet_details",
                        query_type="insert",
                        data=initial_data
                    )
            
            return self
        except Exception as e:
            print(f"Error saving bet: {str(e)}")
            raise

class BetGrade:
    """Model representing a grade for a bet."""
    
    # Cache for distribution stats to avoid recalculating frequently
    _dist_stats = {
        'mean': None,
        'std': None,
        'trimmed_min': None,
        'trimmed_max': None,
        'last_update': None,
        'update_interval': 3600  # Update stats every hour
    }
    
    def __init__(self, id=None, bet_id=None, grade=None, calculated_at=None, ev_score=None,
                 timing_score=None, historical_edge=None, kelly_score=None, composite_score=None,
                 created_at=None, updated_at=None, initial_ev=None, initial_line=None,
                 ev_change=None, bayesian_confidence=None):
        self.id = id
        self.bet_id = bet_id
        self.grade = grade
        self.calculated_at = calculated_at or datetime.now()
        self.ev_score = float(ev_score) if ev_score is not None else None
        self.timing_score = float(timing_score) if timing_score is not None else None
        self.historical_edge = float(historical_edge) if historical_edge is not None else None
        self.kelly_score = float(kelly_score) if kelly_score is not None else None
        self.composite_score = float(composite_score) if composite_score is not None else None
        self.created_at = created_at
        self.updated_at = updated_at
        self.initial_ev = float(initial_ev) if initial_ev is not None else None
        self.initial_line = initial_line
        self.ev_change = float(ev_change) if ev_change is not None else None
        self.bayesian_confidence = float(bayesian_confidence) if bayesian_confidence is not None else None
        
        # Verify bet exists before proceeding with calculations
        if self.bet_id and not self._verify_bet_exists():
            raise ValueError(f"Bet with ID {self.bet_id} does not exist in betting_data table")
        
        # Calculate composite score if not provided but component scores are available
        if self.composite_score is None and self.ev_score is not None and self.historical_edge is not None and self.timing_score is not None:
            # Get initial bet details if not provided
            if self.initial_ev is None and self.bet_id:
                initial_details = self._get_initial_details()
                if initial_details:
                    self.initial_ev = float(initial_details.get('initial_ev')) if initial_details.get('initial_ev') is not None else None
                    self.initial_line = initial_details.get('initial_line')
            
            # Calculate EV trend score and Bayesian updates
            ev_trend_score = self._calculate_ev_trend_score()
            self._calculate_bayesian_updates()
            
            # Updated weights: 35% EV, 20% edge, 15% time, 15% EV trend, 15% Bayesian confidence
            self.composite_score = (
                0.35 * self.ev_score + 
                0.20 * self.historical_edge + 
                0.15 * self.timing_score +
                0.15 * (ev_trend_score if ev_trend_score is not None else self.ev_score) +
                0.15 * (self.bayesian_confidence if self.bayesian_confidence is not None else self.ev_score)
            )
            
            # Determine grade based on composite score
            if self.composite_score >= 90:
                self.grade = 'A'
            elif self.composite_score >= 80:
                self.grade = 'B'
            elif self.composite_score >= 70:
                self.grade = 'C'
            elif self.composite_score >= 65:
                self.grade = 'D'
            else:
                self.grade = 'F'
            
            # Calculate final grade using bell curve
            self.grade = self._assign_bell_curve_grade()
    
    def _verify_bet_exists(self):
        """Verify that the bet exists in the betting_data table."""
        try:
            result = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"bet_id": self.bet_id}
            )
            return result and len(result) > 0
        except Exception as e:
            print(f"Error verifying bet existence: {str(e)}")
            return False
    
    def _calculate_bayesian_updates(self):
        """Calculate Bayesian confidence and EV change metrics."""
        if self.initial_ev is not None and self.ev_score is not None:
            # Calculate EV change as percentage change from initial
            if self.initial_ev != 0:
                self.ev_change = ((self.ev_score - self.initial_ev) / abs(self.initial_ev)) * 100
            else:
                self.ev_change = self.ev_score * 100
            
            # Get event time and first seen time
            event_time = None
            first_seen = None
            
            # Get the bet details to get event_time
            bet_details = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"bet_id": self.bet_id}
            )
            if bet_details and len(bet_details) > 0:
                event_time = bet_details[0].get('event_time')
            
            # Get first seen time from initial_bet_details
            initial_details = self._get_initial_details()
            if initial_details:
                first_seen = initial_details.get('first_seen')
            
            # Calculate Bayesian confidence using the new method
            self.bayesian_confidence = self._compute_bayesian_confidence(
                initial_ev=self.initial_ev,
                current_ev=self.ev_score,
                first_seen_time=first_seen,
                game_time=event_time
            )
    
    def _compute_bayesian_confidence(self, initial_ev, current_ev, first_seen_time, game_time):
        """
        Calculate Bayesian confidence (0-100%) using EV change and time factors.
        
        Args:
            initial_ev: Initial EV percentage
            current_ev: Current EV percentage
            first_seen_time: When the bet was first recorded
            game_time: When the game/event starts
        """
        # Start with initial EV% as prior (normalized to 0-1 range)
        prior_conf = 0.5 + (initial_ev / 100.0)
        
        # Calculate EV change
        ev_change = current_ev - initial_ev
        
        # Apply adjustments based on EV movement
        if ev_change > 0:
            prior_conf += (ev_change / 100.0) * 0.5  # Small boost if EV increased
        elif ev_change < 0:
            prior_conf += (ev_change / 100.0) * 1.0  # Larger penalty if EV dropped
        
        # Time-based modifications
        now = datetime.now(pytz.UTC)
        
        # Convert times to UTC if they aren't already
        if game_time and isinstance(game_time, str):
            try:
                game_time = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                game_time = None
        
        if first_seen_time and isinstance(first_seen_time, str):
            try:
                first_seen_time = datetime.fromisoformat(first_seen_time.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                first_seen_time = None
        
        # Calculate hours left until game if we have valid game time
        hours_left = None
        if game_time and isinstance(game_time, datetime):
            if not game_time.tzinfo:
                game_time = pytz.UTC.localize(game_time)
            hours_left = (game_time - now).total_seconds() / 3600.0
        
        # Time-based confidence adjustments
        if hours_left is not None:
            if hours_left > 20 and ev_change > 0:
                prior_conf *= 1.05  # Boost confidence if bet improved early
            if hours_left < 3:
                if ev_change >= 0:
                    prior_conf *= 1.10  # Boost if bet held value close to game
                else:
                    prior_conf *= 0.50  # Heavy penalty if EV dropped late
        
        # Additional factors
        if first_seen_time:
            hours_since_first_seen = (now - first_seen_time).total_seconds() / 3600.0
            if hours_since_first_seen > 12 and abs(ev_change) < 10:
                prior_conf *= 1.05  # Boost confidence for stable long-term bets
        
        # Clamp between 0-100%
        return max(0, min(1, prior_conf)) * 100
    
    def _get_initial_details(self):
        """Get initial bet details from the initial_bet_details table."""
        try:
            # First verify bet exists in main table
            if not self._verify_bet_exists():
                print(f"Warning: Bet {self.bet_id} not found in betting_data table")
                return None
            
            result = execute_query(
                table_name="initial_bet_details",
                query_type="select",
                filters={"bet_id": self.bet_id}
            )
            return result[0] if result and len(result) > 0 else None
        except Exception as e:
            print(f"Error getting initial bet details: {str(e)}")
            return None
    
    def _calculate_ev_trend_score(self):
        """Calculate a score based on how the EV has changed since initial recording."""
        if self.initial_ev is None or self.ev_score is None:
            return None
            
        # Calculate the EV trend score
        if self.initial_ev > 0:  # If initial EV was positive
            # If current EV is higher than initial, that's good
            if self.ev_score >= self.initial_ev:
                return 100
            # If current EV is still positive but lower, score based on retention
            elif self.ev_score > 0:
                return 70 + (30 * (self.ev_score / self.initial_ev))
            # If current EV turned negative, that's bad
            else:
                return 50
        elif self.initial_ev < 0:  # If initial EV was negative
            # If current EV is now positive, that's great
            if self.ev_score > 0:
                return 100
            # If current EV is still negative but better, that's good
            elif self.ev_score > self.initial_ev:
                return 80
            # If current EV is more negative, that's bad
            else:
                return 60
        else:  # If initial EV was 0
            return self.ev_score if self.ev_score > 0 else 60
    
    @classmethod
    def from_dict(cls, data, skip_validation=False):
        """Create a BetGrade instance from a dictionary."""
        # Remove any fields that aren't in our model
        valid_fields = {
            'id', 'bet_id', 'grade', 'calculated_at', 'ev_score', 'timing_score',
            'historical_edge', 'kelly_score', 'composite_score', 'created_at', 'updated_at',
            'initial_ev', 'initial_line', 'ev_change', 'bayesian_confidence'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Create instance but bypass expensive calculations for batch processing
        instance = cls.__new__(cls)
        
        # Manually set attributes to avoid __init__ logic
        for key, value in filtered_data.items():
            if key in ['ev_score', 'timing_score', 'historical_edge', 'kelly_score', 
                       'composite_score', 'initial_ev', 'ev_change', 'bayesian_confidence']:
                setattr(instance, key, float(value) if value is not None else None)
            else:
                setattr(instance, key, value)
        
        # Set default values for any missing attributes
        if not hasattr(instance, 'calculated_at') or instance.calculated_at is None:
            instance.calculated_at = datetime.now()
        if not hasattr(instance, 'created_at'):
            instance.created_at = None
        if not hasattr(instance, 'updated_at'):
            instance.updated_at = None
        
        # Only run the expensive checks if not skipping validation (default is to skip for performance)
        if not skip_validation:
            # Run the full initialization with validation and calculations
            return cls(**filtered_data)
            
        return instance
    
    @classmethod
    def from_db_row(cls, row):
        """Create a BetGrade instance from a database row."""
        if row is None:
            return None
        return cls.from_dict(dict(row))
    
    @classmethod
    def get_by_bet_id(cls, bet_id):
        """Get a bet grade by bet ID."""
        try:
            result = execute_query(
                table_name="bet_grades",
                query_type="select",
                filters={"bet_id": bet_id}
            )
            
            if result and len(result) > 0:
                grade_instance = cls.from_dict(result[0])
                
                # Get initial details
                initial_details = execute_query(
                    table_name="initial_bet_details",
                    query_type="select",
                    filters={"bet_id": bet_id}
                )
                
                if initial_details and len(initial_details) > 0:
                    grade_instance.initial_ev = float(initial_details[0].get('initial_ev')) if initial_details[0].get('initial_ev') is not None else None
                    grade_instance.initial_line = initial_details[0].get('initial_line')
                
                return grade_instance
            return None
        except Exception as e:
            print(f"Error getting bet grade by ID: {str(e)}")
            return None
    
    def save(self):
        """Save the bet grade to the database."""
        try:
            data = {
                "id": self.id,
                "bet_id": self.bet_id,
                "grade": self.grade,
                "calculated_at": self.calculated_at,
                "ev_score": self.ev_score,
                "timing_score": self.timing_score,
                "historical_edge": self.historical_edge,
                "kelly_score": self.kelly_score,
                "composite_score": self.composite_score,
                "ev_change": self.ev_change,
                "bayesian_confidence": self.bayesian_confidence,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert (insert or update)
            execute_query(
                table_name="bet_grades",
                query_type="upsert",
                data=data
            )
            
            return self
        except Exception as e:
            print(f"Error saving bet grade: {str(e)}")
            raise
    
    @classmethod
    def test_bayesian_update(cls, bet_id, current_ev):
        """
        Test method to verify Bayesian update functionality for a specific bet.
        Returns the calculated grade details for inspection.
        """
        try:
            # Get initial details
            initial_details = execute_query(
                table_name="initial_bet_details",
                query_type="select",
                filters={"bet_id": bet_id}
            )
            
            if not initial_details or len(initial_details) == 0:
                print(f"No initial details found for bet_id: {bet_id}")
                return None
            
            # Get bet details for event time
            bet_details = execute_query(
                table_name="betting_data",
                query_type="select",
                filters={"bet_id": bet_id}
            )
            
            if not bet_details or len(bet_details) == 0:
                print(f"No bet details found for bet_id: {bet_id}")
                return None
                
            # Create a test grade instance
            grade = cls(
                bet_id=bet_id,
                ev_score=current_ev,
                timing_score=80,  # Example timing score
                historical_edge=75,  # Example historical edge
                initial_ev=float(initial_details[0].get('initial_ev')),
                initial_line=initial_details[0].get('initial_line')
            )
            
            # This will trigger the Bayesian calculations
            grade._calculate_bayesian_updates()
            
            # Print detailed results
            print("\nBayesian Update Test Results:")
            print(f"Initial EV: {grade.initial_ev}")
            print(f"Current EV: {grade.ev_score}")
            print(f"EV Change: {grade.ev_change:.2f}%")
            print(f"Event Time: {bet_details[0].get('event_time')}")
            print(f"First Seen: {initial_details[0].get('first_seen')}")
            print(f"Bayesian Confidence: {grade.bayesian_confidence:.2f}%")
            
            # Calculate final grade
            ev_trend_score = grade._calculate_ev_trend_score()
            grade.composite_score = (
                0.35 * grade.ev_score + 
                0.20 * grade.historical_edge + 
                0.15 * grade.timing_score +
                0.15 * (ev_trend_score if ev_trend_score is not None else grade.ev_score) +
                0.15 * (grade.bayesian_confidence if grade.bayesian_confidence is not None else grade.ev_score)
            )
            
            # Set grade based on composite score
            if grade.composite_score >= 90:
                grade.grade = 'A'
            elif grade.composite_score >= 80:
                grade.grade = 'B'
            elif grade.composite_score >= 70:
                grade.grade = 'C'
            elif grade.composite_score >= 65:
                grade.grade = 'D'
            else:
                grade.grade = 'F'
            
            print(f"EV Trend Score: {ev_trend_score}")
            print(f"Composite Score: {grade.composite_score:.2f}")
            print(f"Final Grade: {grade.grade}")
            
            # Save the test results
            grade.save()
            
            return grade
            
        except Exception as e:
            print(f"Error in test_bayesian_update: {str(e)}")
            return None
    
    @classmethod
    def verify_grade_update(cls, bet_id):
        """
        Verify that a bet's grade was properly updated in the database.
        Returns both the stored grade and current calculation for comparison.
        """
        try:
            # Get stored grade
            stored_grade = cls.get_by_bet_id(bet_id)
            
            if not stored_grade:
                print(f"No stored grade found for bet_id: {bet_id}")
                return None
            
            print("\nStored Grade Details:")
            print(f"Grade: {stored_grade.grade}")
            print(f"Composite Score: {stored_grade.composite_score}")
            print(f"EV Change: {stored_grade.ev_change}%")
            print(f"Bayesian Confidence: {stored_grade.bayesian_confidence}")
            
            return stored_grade
            
        except Exception as e:
            print(f"Error in verify_grade_update: {str(e)}")
            return None
    
    @classmethod
    def _get_distribution_stats(cls, force_update=False):
        """
        Get or compute the distribution statistics for grading.
        Updates cache if needed or forced.
        """
        now = datetime.now(pytz.UTC)
        
        # Check if we need to update stats
        should_return_cached = (
            not force_update and 
            cls._dist_stats['mean'] is not None and
            cls._dist_stats['last_update'] is not None and
            (now - cls._dist_stats['last_update']).total_seconds() < cls._dist_stats['update_interval']
        )
        
        if should_return_cached:
            return cls._dist_stats
        
        try:
            # Fetch last 10,000 bets with confidence scores
            result = execute_query(
                table_name="bet_grades",
                query_type="select",
                order={"calculated_at": "desc"},
                limit=10000
            )
            
            if not result:
                return cls._dist_stats
            
            # Extract confidence scores
            confidence_scores = [
                float(row.get('bayesian_confidence'))
                for row in result
                if row.get('bayesian_confidence') is not None
            ]
            
            if not confidence_scores:
                return cls._dist_stats
            
            # Sort scores for percentile calculations
            confidence_scores.sort()
            
            # Calculate trimmed range (2.5% from each end)
            trim_index = int(len(confidence_scores) * 0.025)
            trimmed_scores = confidence_scores[trim_index:-trim_index]
            
            # Calculate statistics
            mean = sum(trimmed_scores) / len(trimmed_scores)
            variance = sum((x - mean) ** 2 for x in trimmed_scores) / len(trimmed_scores)
            std = variance ** 0.5
            
            # Update cache
            cls._dist_stats.update({
                'mean': mean,
                'std': std,
                'trimmed_min': min(trimmed_scores),
                'trimmed_max': max(trimmed_scores),
                'last_update': now
            })
            
            return cls._dist_stats
            
        except Exception as e:
            print(f"Error computing distribution stats: {str(e)}")
            return cls._dist_stats
    
    def _assign_bell_curve_grade(self):
        """
        Assign A/B/C/D/F grade based on confidence score distribution and EV overrides.
        Uses bell curve distribution and applies EV-based overrides.
        """
        if self.bayesian_confidence is None or self.ev_score is None:
            return 'F'
        
        # Get distribution statistics
        stats = self._get_distribution_stats()
        
        if stats['mean'] is None or stats['std'] is None:
            # Fall back to absolute grading if no distribution data
            return self._assign_absolute_grade()
        
        # Clamp confidence to trimmed range
        clamped_confidence = max(min(self.bayesian_confidence, stats['trimmed_max']), stats['trimmed_min'])
        
        # Assign initial grade based on bell curve
        if stats['std'] == 0:
            initial_grade = 'C'  # Default to C if no variation
        else:
            z_score = (clamped_confidence - stats['mean']) / stats['std']
            
            if z_score >= 2.0:  # Top 2.5%
                initial_grade = 'A'
            elif z_score >= 1.0:  # Next 13.5%
                initial_grade = 'B'
            elif z_score > -1.0:  # Middle 68%
                initial_grade = 'C'
            elif z_score > -2.0:  # Next 13.5%
                initial_grade = 'D'
            else:  # Bottom 2.5%
                initial_grade = 'F'
        
        # Apply EV-based overrides
        if self.ev_score >= 20:
            return 'C'  # Cap suspicious high EV bets at C
        elif self.ev_score >= 10:
            return max(initial_grade, 'A', key=lambda x: 'FDCBA'.index(x))  # Ensure at least A
        elif self.ev_score >= 5:
            return max(initial_grade, 'B', key=lambda x: 'FDCBA'.index(x))  # Ensure at least B
        
        return initial_grade
    
    def _assign_absolute_grade(self):
        """Fallback method for absolute grading when distribution data is unavailable."""
        if self.composite_score >= 90:
            return 'A'
        elif self.composite_score >= 80:
            return 'B'
        elif self.composite_score >= 70:
            return 'C'
        elif self.composite_score >= 65:
            return 'D'
        else:
            return 'F'
    
    @classmethod
    def test_distribution_grading(cls):
        """
        Test method to verify bell curve grading distribution.
        Prints statistics and grade distribution of recent bets.
        """
        try:
            # Force update of distribution stats
            stats = cls._get_distribution_stats(force_update=True)
            
            print("\nBell Curve Grading Statistics:")
            print(f"Mean Confidence: {stats['mean']:.2f}")
            print(f"Standard Deviation: {stats['std']:.2f}")
            print(f"Trimmed Range: {stats['trimmed_min']:.2f} - {stats['trimmed_max']:.2f}")
            
            # Get recent grades distribution
            result = execute_query(
                table_name="bet_grades",
                query_type="select",
                order={"calculated_at": "desc"},
                limit=1000
            )
            
            if result:
                grades = [row.get('grade') for row in result if row.get('grade')]
                total = len(grades)
                
                if total > 0:
                    print("\nGrade Distribution (last 1000 bets):")
                    for grade in 'ABCDF':
                        count = grades.count(grade)
                        percentage = (count / total) * 100
                        print(f"Grade {grade}: {count} ({percentage:.1f}%)")
            
            return stats
            
        except Exception as e:
            print(f"Error in test_distribution_grading: {str(e)}")
            return None