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
                 market_implied_prob=None, betid_timestamp=None, created_at=None, updated_at=None):
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
            'market_implied_prob', 'betid_timestamp', 'created_at', 'updated_at'
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
                "updated_at": self.updated_at
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
            else:
                # Insert new bet
                execute_query(
                    table_name="betting_data",
                    query_type="insert",
                    data=data
                )
            
            return self
        except Exception as e:
            print(f"Error saving bet: {str(e)}")
            raise

class BetGrade:
    """Model representing a grade for a bet."""
    
    def __init__(self, id=None, bet_id=None, grade=None, calculated_at=None, ev_score=None,
                 timing_score=None, historical_edge=None, kelly_score=None, composite_score=None,
                 created_at=None, updated_at=None):
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
        
        # Calculate composite score if not provided but component scores are available
        if self.composite_score is None and self.ev_score is not None and self.historical_edge is not None and self.timing_score is not None:
            # Updated weights: 55% EV, 30% edge, 15% time, 0% Kelly
            self.composite_score = 0.55 * self.ev_score + 0.30 * self.historical_edge + 0.15 * self.timing_score
            
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
    
    @classmethod
    def from_dict(cls, data):
        """Create a BetGrade instance from a dictionary."""
        # Remove any fields that aren't in our model
        valid_fields = {
            'id', 'bet_id', 'grade', 'calculated_at', 'ev_score', 'timing_score',
            'historical_edge', 'kelly_score', 'composite_score', 'created_at', 'updated_at'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
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
                return cls.from_dict(result[0])
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