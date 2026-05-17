# Hand Cricket Match Management

A desktop-first Hand Cricket Match Management and Analytics System built with Python, PySide6, SQLite, SQLAlchemy, and pandas.

## Current status

The first implementation slice is in place.

Implemented now:
- Application bootstrap with JSON settings, runtime directory creation, and structured logging
- SQLite/SQLAlchemy schema for teams, players, tournaments, matches, innings, balls, and statistics
- Pure hand cricket match engine with innings handling, chase logic, winner detection, undo, reset, and super over support
- In-memory scoring service and Qt match controller
- Modern dark-mode desktop shell with dashboard, live match screen, analytics workspace, and player management screen
- Analytics transformation service for ball history, over summaries, innings summaries, and win probability heuristics
- Export service for JSON and CSV outputs
- Pytest coverage for scoring logic, database relationships, and analytics transforms

## Architecture

The codebase follows a layered desktop architecture:

- `ui/`: PySide6 views, widgets, theming, and navigation shell
- `controllers/`: UI orchestration and signal-driven workflows
- `services/`: pure scoring engine, analytics transforms, and export logic
- `database/`: SQLAlchemy models, engine bootstrap, and session management
- `utils/`: shared constants, validation, settings loading, helpers, and logging
- `config/`: JSON application settings
- `tests/`: focused pytest coverage for the core domain and persistence layers

## Project structure

```text
.
├── main.py
├── requirements.txt
├── config/
├── controllers/
├── database/
├── services/
├── ui/
├── utils/
├── assets/
└── tests/
```

## Setup

Use a local virtual environment on macOS because the system Python is externally managed.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the desktop app

```bash
source venv/bin/activate
python main.py
```

## Run tests

```bash
source venv/bin/activate
python -m pytest tests/test_scoring.py tests/test_database.py tests/test_analytics.py
```

## Implemented design decisions

- PySide6 is the desktop UI stack
- SQLite is the default local persistence layer
- Ball events are modeled as immutable records to support undo, analytics, and auditability
- Real-time scoring state is isolated in a pure rule engine so it can be tested independently of the UI
- Analytics are generated from event history instead of hardcoded aggregate counters

## Next implementation targets

1. Wire controllers to persistent SQLite-backed match workflows instead of demo-only in-memory setup.
2. Expand the analytics screen from summary tables into embedded charts and cached report generation.
3. Add full team and player CRUD forms, tournament workflows, and exportable scorecards.
4. Complete report export pipelines for PDF summaries and scorecard images.
5. Add background workers for heavier analytics and export operations.

## Screenshots

Screenshot placeholders:
- Dashboard view
- Live match desk
- Analytics workspace
- Player management

## Roadmap

- Tournament mode and leaderboards
- Commentary generation and richer live insights
- OBS overlay support
- REST API and multiplayer-ready service boundaries
- Advanced visual analytics and report templates