# Grade Dashboard

A Flask web application for tracking and analyzing betting opportunities with a focus on expected value (EV) and trend analysis.

## Features

- Dashboard for viewing active betting opportunities
- Comprehensive grading system (A-F) for betting opportunities
- Quick Stats section showing Current Opportunities, Grade Distribution, and Time to Event
- Initial bet details tracking for historical analysis and trend indicators
- Time-to-event color coding:
  - Red: 0-3 hours
  - Yellow: 3-6 hours
  - Purple: 6-12 hours
  - Blue: 12+ hours
- Trend indicators showing changes in odds and EV since first seen
- Explainer page with detailed information about the grading system
- Parlay calculator for multi-leg bets
- Mobile-responsive design optimized for all device sizes

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

## Mobile Experience

The dashboard is fully responsive with optimizations for mobile devices:
- Streamlined layout with vertical stacking of bet details
- Simplified metrics display that prioritizes the most important information
- Hidden secondary metrics (Win/Market Probability) to reduce clutter
- Optimized spacing and font sizes for mobile viewing
- Touch-friendly buttons and interactive elements

## API Endpoints

- `/api/sportsbook/<sportsbook>`: Get active bets for a specific sportsbook
- `/api/calculate_parlay`: Calculate parlay odds, probability, and EV for selected bets

## Grading System

Bets are graded on a scale from A (best) to F (worst):
- A: Exceptional
- B: Strong
- C: Fair
- D: Weak
- F: Poor

The grading system incorporates:
1. Current Expected Value (EV%)
2. Win Probability
3. Market Implied Probability
4. Time Until Event
5. Trend indicators (EV and odds changes)

The dashboard uses trend indicators to show how odds and EV have changed since the bet was first seen:
- Green arrows (↑, ↑↑, ↑↑↑) indicate improving conditions (more arrows = bigger improvement)
- Red arrows (↓, ↓↓, ↓↓↓) indicate worsening conditions (more arrows = bigger decline)

The Initial Details section of each bet card provides historical context by showing:
- First seen - when the betting opportunity was first identified
- Initial odds - the opening odds offered by the sportsbook
- Initial EV - the EV% when the bet was first discovered

See the Explainer page for more details on the grading methodology.
