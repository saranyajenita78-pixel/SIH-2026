# ARCHITECTURE.md

## System overview

```
                    ┌───────────────────────┐
                    │ NCPOR / NPDC DATA     │   (used if a real CSV export is
                    │ Real Antarctic Data   │    placed in data/raw/ncpor/)
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ DATA INGESTION LAYER  │  src/data/ncpor_loader.py
                    └───────────┬───────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       ┌────────────────┐              ┌────────────────┐
       │ REAL DATA      │              │ SIMULATED DATA │
       │ (if supplied)  │              │ src/data/       │
       │                │              │ simulator.py    │
       └───────┬────────┘              └───────┬────────┘
               │                               │
               └──────────────┬────────────────┘
                              ▼
                    ┌───────────────────────┐
                    │ VALIDATION + CLEANING │  src/data/data_validator.py,
                    │                       │  src/data/preprocessing.py
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ SQLITE DATABASE       │  src/database/
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ ML ENGINE             │  src/ml/
                    │ (anomaly, forecast)   │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ RISK ENGINE           │  src/risk/risk_engine.py
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ ALERT ENGINE          │  src/alerts/alert_engine.py
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ RECOMMENDATION ENGINE │  src/recommendations/
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ STREAMLIT DASHBOARD   │  app.py + pages/
                    └───────────────────────┘
```

All of the above is orchestrated by a single function, `src.pipeline.run_full_pipeline()`,
so the dashboard, the scripts, and the test suite all exercise identical logic — there is no
separate "demo path" and "real path".

## Simulation design (why it's not random noise)

`src/data/simulator.py` builds every operational dataset off the **same weather series** for
a given station/scenario, so causal chains are visible and reproducible:

```
Extreme weather (colder + windier)
      ↓
Higher heating/energy demand
      ↓
Higher generator load
      ↓
Higher equipment temperature & vibration
      ↓
Higher anomaly probability (predictive maintenance)

Higher consumption
      ↓
Faster inventory depletion
      ↓
Lower resupply buffer
      ↓
Higher supply shortage risk
```

Each (station, scenario) pair uses a dedicated deterministic RNG seed
(`config.SIM_RANDOM_SEED` + a hash of station/scenario), so the Hackathon Demo Mode is fully
reproducible run-to-run.

## Risk engine design

Each domain (`weather`, `equipment`, `energy`, `inventory`, `logistics`, `communication`)
produces a 0–100 sub-score **and** a plain-language explanation of which specific factor
drove it (see `src/risk/risk_engine.py`). The overall score is a configurable weighted sum
(`config.RISK_WEIGHTS`), so every contribution is visible on the Risk & Alerts page rather
than hidden inside a single opaque number.

## Alert & recommendation design

- **Alerts** (`src/alerts/alert_engine.py`) only fire when a domain's risk level is MEDIUM or
  above, to avoid notification spam, and are sorted by severity.
- **Recommendations** (`src/recommendations/recommendation_engine.py`) turn the current alert
  list into a ranked "review this first" list and a single "Operational Decision Support"
  card — explicitly labeled as decision support, never an official safety instruction.

## Offline-first principle

The application depends on SQLite and local files only. No network call is required to run
the dashboard once `setup.bat` has installed dependencies. The only optional network-touching
component is manually placing a real NCPOR export file — no code in this project makes an
outbound network request.

## Technology choices and why

- **SQLite over a client-server DB:** zero-configuration, works identically on any Windows
  machine, matches the "runs locally, no Docker" requirement.
- **Streamlit multipage app over a custom web framework:** fast to build, professional-enough
  styling achievable via `src/utils/ui_helpers.py`, and trivially run via `streamlit run app.py`.
- **IsolationForest + statistical baseline over deep learning:** the per-unit dataset is small
  (hundreds of hourly points); a transparent, explainable method is both sufficient and far
  easier to justify to a judge or reviewer than an unexplainable neural network.
- **RandomForestRegressor + baseline comparison for forecasting:** simple, fast to train,
  and directly comparable against a naive persistence baseline to demonstrate genuine
  predictive value (or lack thereof) — per the project's "always compare against a baseline"
  methodology requirement.
