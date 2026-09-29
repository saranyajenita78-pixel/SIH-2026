# PolarOps AI — Antarctic Station Intelligence Platform

**Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations**

A decision-support platform for remotely monitoring India's Maitri and Bharati Antarctic
research stations: environmental conditions, equipment health, energy, inventory, logistics,
and operational risk — converted into explainable AI-driven alerts and recommendations.

> **This is a decision-support prototype.** It does **not** autonomously operate any
> Antarctic station, is **not** an official Government of India or NCPOR system, and is
> **not** connected to any real station hardware.

---

## 1. Problem & Solution

Indian Antarctic stations operate in one of the world's most challenging environments:
extreme cold, high winds, long isolation, limited resupply windows, and equipment that must
run reliably with minimal spare parts. Information about weather, equipment, energy,
inventory and logistics is normally scattered across separate systems. PolarOps AI unifies
this into a single intelligence pipeline:

```
OBSERVE → ANALYZE → PREDICT → PRIORITIZE → ALERT → RECOMMEND → DECIDE
```

## 2. Features

- **Command Center** — executive overview of both stations, overall risk, active alerts
- **Station Monitor** — Maitri vs Bharati comparison and history
- **Environment** — weather time series with an explainable weather-risk engine
- **Energy Intelligence** — consumption/production tracking + ML forecast vs baseline
- **Equipment Health** — predictive maintenance with per-signal explainability
- **Inventory & Logistics** — supply shortage prediction and resupply prioritization
- **Risk & Alerts** — transparent, weighted multi-domain operational risk score
- **AI Insights** — structured Q&A answered strictly from computed pipeline data
- **Data Explorer** — inspect every dataset with explicit REAL vs SIMULATED provenance
- **Model Performance** — methodology, metrics, and limitations for every model
- **Hackathon Demo Mode** — a scenario selector (sidebar) that walks a judge through
  NORMAL → EXTREME_WEATHER → EQUIPMENT_ANOMALY → RESOURCE_PRESSURE → COMPOUND_EMERGENCY,
  showing the whole OBSERVE→...→DECIDE chain react in real time.

## 3. Data Sources & Integrity Policy

See **DATA_SOURCES.md** for the full registry. The platform now separates source-backed
weather from demonstration telemetry:

| Category | Meaning | Used for |
|---|---|---|
| `REAL_OBSERVED` | Actual observations from a legitimate public source | NCPOR / NPDC weather |
| `REAL_FORECAST` | Official forecast product, kept separate from observations | IMD Polar WRF |
| `REAL_REFERENCE` | Real factual/reference info, not telemetry | Station metadata |
| `SIMULATED_DEMO` | Artificially generated, clearly labeled | Equipment, energy, inventory, logistics telemetry |
| `MODEL_PREDICTION` | Output of this project's own models | Anomaly scores, forecasts, risk scores |

The runtime command center is **REAL-first**: current dashboard weather uses verified NCPOR observations only. Demo scenarios affect the clearly labelled operational simulation modules; they do not turn synthetic weather into real weather. The main UI uses an official local NCPOR
CSV when supplied and otherwise attempts the latest published NCPOR/NPDC station observation.
It never silently substitutes simulated weather when real ingestion fails. DEMO mode retains the
deterministic simulator for offline hackathon demonstrations.

Official IMD Polar WRF exports can be supplied under `data/raw/imd/` and are tagged
`REAL_FORECAST`; the project does not invent or assume an undocumented IMD API endpoint.

## 4. Architecture

See **ARCHITECTURE.md** for the full diagram. Summary:

```
NCPOR / NPDC observations ─┐
IMD Polar WRF forecasts   ─┼─→ Ingestion → Validation → Cleaning → Digital Twin / AI
Demo simulator (optional) ─┘                                            │
                                                                          ▼
                                                          Analytics → ML Models → Risk Engine
                                                                          │
                                                          Alert Engine → Recommendation Engine
                                                                          │
                                                                   Streamlit Dashboard
```

## 5. Technology Stack

Python 3.11+, Pandas, NumPy, scikit-learn, Plotly, Streamlit, SQLite (stdlib `sqlite3`).
No Docker, no WSL, no cloud dependency — runs entirely locally on Windows.

## 6. Windows Installation (VS Code)

1. Extract/clone this project folder.
2. Open the folder in VS Code.
3. Double-click **`setup.bat`** (creates a virtual environment, installs dependencies,
   initializes the database, and generates demo data). This can take a few minutes the
   first time.
4. Double-click **`run.bat`**. Your browser opens automatically to the dashboard
   (usually `http://localhost:8501`).

### Manual steps (equivalent, from a VS Code terminal)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\initialize_database.py
python scripts\ingest_ncpor_data.py
python scripts\ingest_imd_data.py
python scripts\build_model_artifacts.py
streamlit run app.py
```

## 7. Bringing in real NCPOR and IMD data

1. **NCPOR / NPDC live observation:** Run the app in **REAL** mode. If no local file is present,
   `src/data/ncpor_live.py` requests the public Maitri/Bharati NPDC station page and parses the
   latest published temperature, humidity, pressure and wind observation.
2. **NCPOR historical observation:** For longer time series and model training, place an official
   export at `data/raw/ncpor/maitri_aws.csv` or `data/raw/ncpor/bharati_aws.csv`.
3. **IMD Polar WRF:** Place an official forecast export at
   `data/raw/imd/maitri_polar_wrf.csv` or `data/raw/imd/bharati_polar_wrf.csv` (JSON is also accepted).
   These values appear as `REAL_FORECAST` and are not mixed with observations.
4. Equipment, energy, inventory, logistics and communication remain `SIMULATED_DEMO` unless an
   authorised real telemetry source is supplied.

For a deterministic offline presentation, switch the sidebar to **DEMO** mode.

## 8. Hackathon Demo Flow (5–10 minutes)

1. Open the **Command Center**. Scenario = `NORMAL`. Both stations show LOW/MEDIUM risk.
2. In the sidebar, switch Demo Mode to **`EXTREME_WEATHER`**. Watch temperature drop, wind
   rise, weather risk escalate to HIGH, and new alerts appear.
3. Switch to **`EQUIPMENT_ANOMALY`**. Visit **Equipment Health** — see a specific generator's
   health score fall, with an explicit "why" (which signal deviated, and by how much).
4. Switch to **`RESOURCE_PRESSURE`**. Visit **Inventory & Logistics** — see days-remaining
   shrink and a resupply priority list appear.
5. Switch to **`COMPOUND_EMERGENCY`**. Return to the Command Center — the **Operational
   Decision Support** card now shows a compound situation, primary/secondary risk, and a
   ranked review list.
6. Visit **AI Insights** to show the structured Q&A layer, and **Model Performance** to show
   the ML methodology and metrics behind every number.

## 9. Machine Learning Summary

| Model | Purpose | Method | Evaluation |
|---|---|---|---|
| Equipment anomaly detection | Predictive maintenance | Per-unit baseline z-score + IsolationForest confirmation | Unsupervised diagnostics only (no real failure labels exist) |
| Energy forecast | Short-horizon consumption forecasting | RandomForestRegressor vs. persistence baseline, time-aware split | MAE / RMSE / R² |
| Risk engine | Explainable multi-domain operational risk | Rule-based weighted scoring (not a trained classifier, by design) | Transparent by construction |

See **MODEL_CARD.md** for full detail, and **LIMITATIONS.md** for what this prototype cannot
currently do.

## 10. Project Structure

```
antarctic_station_platform/
├── app.py                     # Command Center (entry point)
├── config.py                  # Central configuration
├── requirements.txt
├── setup.bat / run.bat
├── README.md / DATA_SOURCES.md / LIMITATIONS.md / ARCHITECTURE.md / MODEL_CARD.md
├── data/                      # raw/ncpor, raw/imd, raw/external, processed, simulated
├── database/                  # antarctic.db (SQLite, created by setup)
├── src/
│   ├── data/                  # NCPOR live/local, IMD forecast, simulator, validation
│   ├── database/              # schema + repository
│   ├── ml/                    # anomaly detection, energy forecast
│   ├── risk/                  # risk engine
│   ├── alerts/                # alert engine
│   ├── recommendations/       # recommendation engine
│   ├── utils/                 # logging, UI helpers, state
│   └── pipeline.py            # orchestrates the full chain
├── pages/                     # Streamlit multipage dashboard (1_..9_)
├── scripts/                   # initialize_database.py, generate_demo_data.py
└── tests/                     # pytest suite
```

## 11. AI Operations Copilot

The AI Insights page and Command Center use the OpenAI Responses API when `OPENAI_API_KEY` is configured. The agent receives a compact snapshot of the current pipeline, historical-data status, and provenance policy, and can use web search for current/external questions. Without a key, the app explicitly labels the local grounded copilot; it does not claim that fallback is ChatGPT.

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL=gpt-5.6-luna` in the environment or a local `.env` file. Never commit the key.

## 12. Model Artifacts & Runtime

The `models/` directory contains inspectable prototype-trained artifacts and `manifest.json`. Equipment anomaly scoring uses the saved normal-operation artifact when available, then scores scenario telemetry against that baseline; this avoids retraining on the anomaly itself. Energy metrics remain scenario-specific and the final energy model produces a next-hour estimate. All operational training data is `SIMULATED_DEMO` because internal station equipment/energy telemetry is not public.

## 13. Running Tests

```bat
.venv\Scripts\activate
pytest tests/ -v
```

## 12. Limitations & Future Scope

See **LIMITATIONS.md** for current limitations and **section 12 of this README's origin
spec** for future scope (real-time IoT integration, satellite communication, digital twin,
computer vision, advanced multi-station logistics optimization, etc.) — all noted as future
work, not current capability.

## 13. Credibility & Ethical Development

This project never invents datasets, fabricates model accuracy, claims government deployment,
or claims NCPOR endorsement. Every dataset in the dashboard is labeled with its real
provenance (`REAL_OBSERVED` / `REAL_REFERENCE` / `SIMULATED_DEMO` / `MODEL_PREDICTION`), and
every AI-generated recommendation is presented as decision support — never as an official
safety instruction.

## Polar Twin Sentinel UI

The command center is designed as an Antarctic operations cockpit rather than a generic analytics dashboard. It includes:

- Maitri and Bharati station imagery with live condition overlays
- popover-based station telemetry and decision briefs
- NCPOR observation provenance and separate IMD Polar WRF forecast provenance
- AI Operations Copilot with grounded operational questions
- What-If Mission Lab for weather/equipment/energy/logistics stress testing
- Digital Twin control-loop visualization: observe → fuse → twin → AI/ML → what-if → alert/action
- explicit synthetic-data badges for non-public equipment/energy/inventory/logistics telemetry
- dark navy / ice-blue visual system designed for a mission-control presentation

## Real-source boundary

NCPOR/NPDC public station observations are fetched in REAL mode. IMD Polar WRF is supported through an official export adapter because this prototype does not claim an undocumented public API. Equipment, energy, inventory and logistics remain simulated until an authorised station telemetry feed is supplied.

## SIH 2026 demo flow

1. Run `setup.bat` once, then `run.bat`.
2. Open `http://localhost:8501`.
3. Keep **REAL** selected to demonstrate NCPOR observations.
4. Use **AI Operations Copilot** and press **ASK AI** after typing a question.
5. Use **What-If Mission Lab** to test temperature, wind, pressure, equipment, energy and logistics shocks.
6. Use **SIH Solution Overview** to walk judges through the proposed solution, technical approach, feasibility, challenges and impact.
7. Switch to **DEMO** only when you want deterministic extreme-weather/equipment/resource scenarios.

## Real AI Copilot setup

The AI Operations Copilot uses the OpenAI Responses API. The application checks `OPENAI_API_KEY` from the environment and from Streamlit Cloud Secrets. The key is intentionally not bundled in this project.

### Local Windows
1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY=your_api_key_here`.
3. Install dependencies with `pip install -r requirements.txt`.
4. Restart the app with `streamlit run app.py`.

### Streamlit Cloud
Open the deployed app's **Settings → Secrets** and add:
```toml
OPENAI_API_KEY = "your_api_key_here"
OPENAI_MODEL = "gpt-5.6-luna"
```
Save and reboot/redeploy the app. The AI page should then show **OPENAI AI AGENT** instead of **LOCAL GROUNDED FALLBACK**.

A ChatGPT subscription does not automatically provide an API key to a deployed application; the app needs an OpenAI API key configured in its own environment/secrets.


### Historical snowfall grounding

The project includes `data/raw/ncpor/historical/` for authorised NCPOR/IMD CSV/JSON exports.
If a file contains `timestamp` and `snowfall_mm` (or a supported alias), the AI Copilot can answer
maximum-snowfall questions from that real export. If no such export is present, it explicitly says
the exact historical snowfall value is unavailable rather than guessing.
