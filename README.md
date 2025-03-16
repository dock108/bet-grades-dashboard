# Grade Dashboard

A Flask web application for tracking and analyzing betting opportunities with a focus on expected value (EV) and Bayesian confidence scoring.

## Features

- Dashboard for viewing active betting opportunities
- Statistical grading system using bell curve distribution
- Initial bet details tracking for EV change analysis
- Bayesian confidence scoring with time-aware adjustments
- Time-to-event color coding:
  - Red: <1h (Immediate action needed)
  - Orange: 1-3h (Very urgent)
  - Yellow: 3-6h (Urgent)
  - Blue: 6-12h (Monitor)
  - Green: >12h (Plan ahead)
- Sportsbook distribution tracking
- Rankings page for prioritized betting opportunities
- Explainer page with detailed information about the grading system
- Parlay calculator for multi-leg bets

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS (Tailwind), JavaScript

## Project Structure

```
grade-dashboard/
├── app/                    # Application package
│   ├── __init__.py         # Application factory
│   ├── admin/              # Admin functionality
│   ├── api/                # API endpoints
│   │   ├── __init__.py     # Blueprint initialization
│   │   └── api_routes.py   # API route handlers
│   ├── core/               # Core functionality
│   │   └── database.py     # Database utilities
│   ├── models/             # Data models
│   │   └── bet_models.py   # Betting models
│   ├── services/           # Business logic
│   │   ├── bet_service.py  # Betting services
│   │   └── parlay.py       # Parlay calculation services
│   ├── main/               # Main blueprint
│   │   ├── __init__.py     # Blueprint initialization
│   │   └── main_routes.py  # Main route handlers
│   ├── static/             # Static assets
│   └── templates/          # HTML templates
├── logs/                   # Application logs
├── .env.example            # Environment variables template
├── .env                    # Environment variables (not in version control)
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── README.md               # This file
```

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/grade-dashboard.git
   cd grade-dashboard
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file with your database credentials and configuration.

### Running the Application

```
python run.py
```

The application will be available at http://localhost:5000.

## Usage

1. **Home Dashboard**: View all active betting opportunities with grades and time-to-event indicators
2. **Rankings Page**: View betting opportunities sorted by priority
3. **Explainer Page**: Learn about the grading system and methodology

## API Endpoints

- `/api/sportsbook/<sportsbook>`: Get active bets for a specific sportsbook

## Grading System

Bets are graded on a bell curve distribution based on Bayesian confidence scores from the last 10,000 bets:
- A: Top 2.5% (Exceptional Value)
- B: Next 13.5% (Strong Value)
- C: Middle 68% (Fair Value)
- D: Next 13.5% (Weak Value)
- F: Bottom 2.5% (Poor Value)

The grading system incorporates:
1. Current Expected Value (55% weight)
2. EV Change from Initial Odds
3. Bayesian Confidence Score
4. Time Until Event

Bayesian confidence is calculated using:
- EV changes since the bet was first seen
- Time remaining until the event starts
- Asymmetric weighting for EV improvements vs declines

See the Explainer page for more details on the grading methodology.
