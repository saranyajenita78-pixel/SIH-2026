# LIMITATIONS.md

This document states plainly what PolarOps AI currently cannot do, per the project's
credibility and data-integrity requirements.

## Data limitations

- **No real NCPOR/NPDC data was downloaded for this build.** The environment used to
  assemble this project has no outbound internet access. The NCPOR ingestion pipeline
  (`src/data/ncpor_loader.py`) is fully implemented and tested against synthetic CSVs, but a
  live connection to the NCPOR/NPDC portal has not been exercised. Weather data shown by
  default is `SIMULATED_DEMO`, clearly labeled as such everywhere it appears.
- **No real equipment, energy, inventory, or logistics telemetry exists for this project to
  use.** No public real-time feed of Antarctic station generator vibration, fuel tank levels,
  spare-part stock, or resupply schedules is known to exist. All such data is `SIMULATED_DEMO`
  by design, generated with plausible cause-and-effect relationships rather than pure random
  noise, but it is not, and does not claim to be, real operational data.
- **Station coordinates are approximate public-knowledge values** (`REAL_REFERENCE`), not
  independently surveyed GPS fixes.

## Machine learning limitations

- **No ground-truth failure labels exist** for the simulated equipment telemetry, so the
  anomaly detection model cannot be evaluated with precision/recall — it is evaluated only
  via unsupervised diagnostics (e.g., does its score correctly separate the demo's
  deliberately-injected anomaly scenario from the normal baseline).
- **The energy forecast model** is trained and evaluated only on the simulated demo history
  (up to `config.HISTORY_DAYS` days). Its metrics (MAE/RMSE/R²) describe how well it predicts
  *this simulated series*, not real station energy demand.
- **The risk engine is rule-based, not a trained classifier.** Thresholds and weights in
  `config.py` are illustrative defaults chosen for explainability and demo clarity, not
  calibrated against historical incident data (none was available).
- Models are retrained on every pipeline run (fast, since data volume is small) rather than
  persisted and versioned — acceptable for a demo/prototype, not for production use.

## Functional limitations

- **No real-time IoT connection.** The platform does not connect to any actual station
  hardware, sensor network, or satellite uplink. "Communication status" is simulated.
- **No offline-sync engine is actually implemented** beyond a conceptual status indicator —
  the app runs fully locally against SQLite and does not currently queue/replay data across a
  real intermittent connection.
- **Single-user, local application.** No multi-user authentication, role-based access
  control, or centralized headquarters server is implemented in this build, though the
  database schema includes a `users` concept for future extension.
- **No LLM-based free-text assistant is wired in by default** (see AI Insights page) — the
  platform is fully functional without any API key, per the project's requirement that the
  optional AI assistant never be a hard dependency.

## What this project does NOT claim

- This is **not** an official Government of India or NCPOR system.
- This project is **not** officially deployed, endorsed, or used by NCPOR or any Antarctic
  station.
- This platform does **not** autonomously operate any station or piece of equipment.
- Recommendations shown are **decision support only** and are never an official safety
  instruction.

## Future scope

See README.md §12 for planned extensions: real-time IoT integration, edge computing,
satellite communication, real equipment telemetry, advanced predictive maintenance, a
digital twin, satellite imagery / computer vision, advanced weather forecasting, and
multi-station logistics optimization.
