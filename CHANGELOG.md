# Changelog

All notable changes to the Grade Dashboard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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