# Changelog

All notable changes to the Grade Dashboard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-03-21

### Changed
- Redesigned the Quick Stats section and moved it above betting cards
  - Consolidated into a 3-column grid layout with Current Opportunities, Grade Distribution, and Time to Event
  - Removed the Sportsbook Distribution from the Quick Stats (available via Parlay Options)
  - Made Time to Event display match the Grade Distribution style
- Improved the Initial Details section at the bottom of bet cards:
  - Removed "Initial Details" label
  - Reordered items to: First seen, Initial Odds, Initial EV
  - Added icons to each item for better visual distinction
  - Improved spacing and layout
- Updated "Last Updated" timestamp format in the header to match the "First Seen" format for consistency

## [1.1.2] - 2025-03-20

### Changed
- Completely redesigned the bet card layout with a modern, compact format:
  - Arranged metrics in a 2x4 grid for better organization
  - Top row shows Odds, Current EV, Time Left, and Bet Size
  - Bottom row displays Sportsbook, Win Probability, Market Probability, and Parlay options
  - Made grade display more prominent with colored left border on bet cards
  - Added trend indicators using colored arrows (↑, ↓, -) to show changes from initial values
  - Streamlined Initial Details section into a single row format
- Revamped the explainer page with a fun, sarcastic tone aimed at sports bettors:
  - Added sidebar navigation with smooth scrolling between sections
  - Enhanced with gradient backgrounds and improved color coding
  - Added detailed sections explaining the trend indicator system and Initial Details feature
- Improved time distribution display:
  - Updated labels to be more user-friendly
  - Removed duplicate entries and standardized formatting
  - Fixed time threshold calculations for accurate color-coding
- Removed confusing elements:
  - Eliminated Bayesian Confidence from the dashboard UI
  - Removed bell curve grading distribution references from the UI
  - Fixed display of empty "None" IDs in bet card headers

### Fixed
- Corrected win and market probability percentage displays
- Standardized formatting across all UI components
- Fixed Time Left display threshold in bet cards
- Improved error handling for missing data points

## [1.1.1] - 2025-03-17

### Changed
- Updated time-to-event categories to be more granular:
  - Red: <1h (Immediate action needed)
  - Orange: 1-3h (Very urgent)
  - Yellow: 3-6h (Urgent)
  - Blue: 6-12h (Monitor)
  - Green: >12h (Plan ahead)
- Reordered time distribution summary from most urgent to least urgent

## [1.1.0] - 2025-03-17

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

## [1.0.3] - 2025-03-16

### Changed
- Renamed files to follow a more descriptive naming convention:
  - `app/models/betting.py` → `app/models/bet_models.py`
  - `app/services/betting.py` → `app/services/bet_service.py`
  - `app/api/routes.py` → `app/api/api_routes.py`
  - `app/main/routes.py` → `app/main/main_routes.py`
- Updated all relevant imports to reflect new file names
- Updated project documentation to reflect new file structure

## [1.0.2] - 2025-03-16

### Added
- Vercel deployment configuration
- Added `vercel.json` for serverless function configuration
- Created `api/index.py` as the Vercel entry point
- Added `.vercelignore` to exclude unnecessary files from deployment
- Updated requirements to use `>=` for better compatibility

## [1.0.1] - 2025-03-16

### Fixed
- Removed references to non-existent 'result' column in database queries
- Updated Bet model's get_by_sportsbook method to remove result filtering
- Added placeholder implementations for admin functions that previously relied on the result column
- Removed unused imports in admin routes

## [1.0.0] - 2025-03-16

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

## [0.9.0] - 2025-03-15

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

## [1.2.10] - 2024-03-29

### Fixed
- Removed dependency on unavailable custom SQL function
- Fixed error in grade retrieval by using standard database functions
- Improved error handling for database queries
- Reverted to using standard query method with time-based filtering
- Updated logging for better troubleshooting

## [1.2.9] - 2024-03-29

### Improved
- Dramatically optimized grade retrieval with direct SQL using Common Table Expressions (CTE)
- Added execute_custom_query function to support advanced SQL queries
- Replaced inefficient Python-based filtering with database-side SQL filtering
- Fixed major performance bottleneck that was taking 12-15 seconds during grade lookup
- SQL optimization now directly retrieves only the most recent grade for each bet ID

## [1.2.8] - 2024-03-29

### Improved
- Significantly optimized grade lookup performance (12+ seconds reduced to milliseconds)
- Fixed bottleneck in BetGrade object creation during grade attachment
- Improved handling of None values in sorting functions
- Enhanced attribute safety checks with hasattr() in sorting methods
- More efficient list creation in get_grades_by_bet_ids method

## [1.2.7] - 2024-03-29

### Improved
- Added detailed performance logging to identify slow operations
- Added timing metrics for all major service methods in bet_service.py
- Commented out verbose individual bet logging to reduce log clutter
- Each method now reports execution time for its key operations
- Each method now reports total execution time
- Enhanced error handling with timing metrics for failed operations

## [1.2.6] - 2024-03-29

### Improved
- Optimized grade retrieval to only fetch records from 5 minutes before the most recent betting data timestamp
- Significantly reduces database load and processing time when retrieving grades
- Maintains backward compatibility with fallback to full retrieval when needed

## [1.2.5] - 2024-03-29

### Added
- First-time user animation that points to the Explainer page
- Animation automatically disappears after 3 seconds
- Uses localStorage to track returning visitors

### Fixed
- Improved bet sorting to strictly prioritize letter grades (A to F) before considering score values 
- Added "Unusual Line" indicator for bets where the score is unusually high for the assigned grade
- Ensures bets with a C grade but high EV% are properly sorted after all A and B grade bets
- Clearly flags bets with score/grade mismatches to indicate deprioritized lines

## [1.2.4] - 2024-03-29

### Fixed
- Improved bet sorting logic to first sort by grade letter (A, B, C, D, F) and then by composite score within each grade
- This ensures bets with a C grade but high EV% (e.g., over 20%) won't appear before A or B grade bets

## [1.2.3] - 2024-03-29

### Changed
- Improved parlay value analysis section with clearer labels for odds comparison
- Updated terminology from "Calculated True Odds"/"Estimated Market Odds" to "This Sportsbook Pays"/"Market Average Pays"
- Enhanced tooltip descriptions to better explain the odds comparison

## [1.2.2] - 2024-03-29

### Fixed
- Improved bet sorting logic to first sort by grade letter (A, B, C, D, F) and then by composite score within each grade
- This ensures bets with a C grade but high EV% (e.g., over 20%) won't appear before A or B grade bets

## [1.2.1] - 2024-03-29

### Added
- New section in explainer document about getting limited by sportsbooks
- Added visual reference showing a betting slip with a small limit

### Changed
- Reduced color variety in the explainer page for better readability
- Updated section backgrounds to use more neutral color scheme
- Redesigned color code guide to use border-left pattern instead of colored backgrounds

## [1.2.0] - 2024-03-29

### Changed
- Completely redesigned the bet card layout with a modern, compact format:
  - Arranged metrics in a 2x4 grid for better organization
  - Top row shows Odds, Current EV, Time Left, and Bet Size
  - Bottom row displays Sportsbook, Win Probability, Market Probability, and Parlay options
  - Made grade display more prominent with colored left border on bet cards
  - Added trend indicators using colored arrows (↑, ↓, -) to show changes from initial values
  - Streamlined Initial Details section into a single row format