# Changelog

All notable changes to the Grade Dashboard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2024-03-20

### Changed
- Completely revamped the explainer page with a fun, sarcastic tone aimed at sports bettors
- Added sidebar navigation to the explainer page with smooth scrolling between sections
- Enhanced the explainer page with gradient backgrounds and improved color coding
- Updated time distribution labels to be more user-friendly:
  - "Now-ish" (<1h)
  - "Soon" (1-3h)
  - "Later" (3-6h)
  - "Tonight" (6-12h)
  - "Tomorrow+" (>12h)
- Added a detailed section explaining parlay calculator functionality
- Added comprehensive explanation of Expected Value (EV) concept with real-world examples
- Improved documentation on "Initial Details" feature including first seen timestamp

## [1.0.3] - 2024-03-16

### Changed
- Renamed files to follow a more descriptive naming convention:
  - `app/models/betting.py` → `app/models/bet_models.py`
  - `app/services/betting.py` → `app/services/bet_service.py`
  - `app/api/routes.py` → `app/api/api_routes.py`
  - `app/main/routes.py` → `app/main/main_routes.py`
- Updated all relevant imports to reflect new file names
- Updated project documentation to reflect new file structure

## [1.0.2] - 2024-03-16

### Added
- Vercel deployment configuration
- Added `vercel.json` for serverless function configuration
- Created `api/index.py` as the Vercel entry point
- Added `.vercelignore` to exclude unnecessary files from deployment
- Updated requirements to use `>=` for better compatibility

## [1.0.1] - 2024-03-16

### Fixed
- Removed references to non-existent 'result' column in database queries
- Updated Bet model's get_by_sportsbook method to remove result filtering
- Added placeholder implementations for admin functions that previously relied on the result column
- Removed unused imports in admin routes

## [1.0.0] - 2024-03-16

### Added
- Initial release of the Grade Dashboard
- Home dashboard for viewing active betting opportunities
- Rankings page for prioritized betting opportunities
- Explainer page with detailed information about the grading system
- Grading system (A-F) based on composite scores
- Time-to-event color coding (green for >12h, yellow for 6-12h, red for <6h)
- Sportsbook distribution tracking
- Parlay calculator for multi-leg bets
- API endpoint for retrieving sportsbook-specific bets

### Changed
- Updated time categories from old system (>24h, 6-24h, <6h) to new system (>12h, 6-12h, <6h)
- Simplified timezone handling throughout the application
- Improved grade retrieval logic to fetch the most recent grades

### Fixed
- Resolved issues with timezone conversion in templates
- Fixed bug in `get_bets_by_sportsbook` method to properly handle the `include_resolved` parameter
- Improved error handling in betting service methods

## [1.1.0] - 2024-03-17

### Added
- Initial bet details tracking in new `initial_bet_details` table
- Bayesian confidence scoring system for bet evaluation
- Bell curve grading distribution (A: top 2.5%, B: next 13.5%, C: middle 68%, D: next 13.5%, F: bottom 2.5%)
- Time-aware Bayesian confidence adjustments
- EV change tracking from initial odds

### Changed
- Updated grading system to use statistical distribution instead of fixed thresholds
- Modified UI to show new metrics (EV change, Bayesian confidence)
- Improved time-based color coding thresholds
- Updated templates to reflect new grading system

## [1.1.1] - 2024-03-17

### Changed
- Updated time-to-event categories to be more granular:
  - Red: <1h (Immediate action needed)
  - Orange: 1-3h (Very urgent)
  - Yellow: 3-6h (Urgent)
  - Blue: 6-12h (Monitor)
  - Green: >12h (Plan ahead)
- Reordered time distribution summary from most urgent to least urgent

## [1.1.3] - 2024-03-25

### Changed
- Removed all bell curve grading distribution references from the UI and explainer
- Updated grade descriptions to be more intuitive:
  - A: Exceptional
  - B: Strong
  - C: Fair
  - D: Weak
  - F: Poor
- Modified grading system to use absolute criteria instead of distribution percentages
- Updated Distribution Statistics section in explainer document to remove bell curve references

## [1.1.4] - 2024-03-26

### Changed
- Removed Bayesian Confidence display from the dashboard UI as it was causing confusion
- Added intuitive trend indicators (↑, →, ↓) in the Initial Details section to show:
  - EV trends (significant improvement, slight improvement, stable, slight decline, significant decline)
  - Odds movement (better, stable, worse)
- Added detailed explanation of trend indicators in the explainer document
- Simplified the UI to focus on actionable data points

## [0.9.0] - 2024-03-15

### Added
- Initial development version
- Basic Flask application structure
- Database connection and models
- Core betting services
- HTML templates with Tailwind CSS

### Changed
- Migrated from old logic structure to new Flask application architecture
- Simplified database schema

### Removed
- Legacy code and outdated features from previous implementation 