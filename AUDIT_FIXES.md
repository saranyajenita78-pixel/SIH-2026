# Polar Twin Sentinel — Backend / AI Audit Fixes

## Fixed in this build

1. **Historical snowfall grounding**
   - Added `src/data/historical.py`.
   - Added `data/raw/ncpor/historical/` for authorised NCPOR/IMD CSV/JSON exports.
   - The Copilot can answer maximum-snowfall questions when an export contains a snowfall field.
   - No synthetic snowfall is created or presented as real.

2. **Real AI Copilot**
   - OpenAI Responses API remains the primary agent when `OPENAI_API_KEY` is configured.
   - Current pipeline, provenance, historical-data status, risk, equipment, energy, inventory and logistics context are supplied.
   - Web search is enabled for current/source/snowfall-style questions.

3. **Risk-engine temperature bug**
   - Corrected a non-monotonic temperature risk calculation where warmer temperatures could increase cold-stress risk.
   - Cold-stress contribution now increases as temperature becomes colder and is zero above the moderate cold threshold.

4. **Predictive-maintenance baseline**
   - Saved normal-operation equipment anomaly artifacts are now loaded when available.
   - Scenario telemetry is scored against the normal baseline instead of retraining on the anomaly itself.
   - This is both more defensible and faster.

5. **Energy forecast**
   - Added a genuine next-hour consumption prediction from the final model trained on the available history.
   - Evaluation metrics remain time-aware and are reported separately from the next-hour estimate.

6. **SQLite backend snapshot**
   - The pipeline now synchronizes its current Digital Twin state into `database/antarctic.db`.
   - Weather, equipment, energy, inventory, logistics, communication, predictions, alerts and recommendations are persisted as a current snapshot.

7. **Data freshness honesty**
   - The dashboard no longer blindly labels every NCPOR observation as `LIVE`.
   - Observation age is calculated from the source timestamp and shown as latest published / published N hours ago.

8. **Deterministic simulator**
   - Replaced Python's process-randomized `hash()` seed component with SHA-256-derived stable seeds.
   - Demo outputs are reproducible across Python processes.

9. **Documentation consistency**
   - Updated model-card tree counts (IsolationForest 80, RandomForest 100).
   - Updated data-source documentation and historical snowfall limitations.

## Remaining limitation that is intentional

The public NCPOR portal currently lists historical Maitri datasets (including SASE 2006–2015),
but the public graph interface does not expose a stable documented snowfall download API. The
project therefore does **not** invent a maximum snowfall date. To answer that exact question from
real data, place an authorised historical export in `data/raw/ncpor/historical/`.

The same principle applies to internal equipment, energy, inventory, logistics and communication
telemetry: these remain `SIMULATED_DEMO` until an authorised station feed is supplied.

## Verification

- **28/28 automated tests passed.**
- Python compile checks passed for modified application/backend modules.
- SQLite snapshot sync was exercised successfully.
