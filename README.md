# Time to Help

A Streamlit prototype for coordinating potentially suitable emergency blood donors. Preloaded ranking candidates are fictional; self-entered donor details are held only in the active Streamlit session. This app does not confirm transfusion compatibility or medical eligibility.

## Files

- `app.py` - UI with a light/dark theme switch, request and input navigation, demo data, explainable score, response flow, screening handoff, and session audit log.
- `requirements.txt` - Streamlit dependency.
- `.streamlit/config.toml` - light blood-camp theme with dark theme palette.

## Run

Python 3.12 is recommended. From this folder:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If using Anaconda on Windows, create a Python 3.12 environment and use its Python executable to install and start Streamlit. For example, if the environment is named `timetohelp`:

```powershell
& "$env:USERPROFILE\.conda\envs\timetohelp\python.exe" -m pip install -r requirements.txt
& "$env:USERPROFILE\.conda\envs\timetohelp\python.exe" -m streamlit run app.py
```

## Ranking logic

The app screens out donor groups outside a simplified red-cell compatibility lookup and donors marked unavailable. Remaining candidates receive a weighted score normalized to 0-100. Exact group match scores 1.0 of its weight; compatible non-exact group scores 0.63. Confirmed availability scores 1.0; unconfirmed scores 0.47. Distance declines linearly to zero at 15 km. Response time declines to zero at an urgency-adjusted target based on the requested deadline: EMERGENCY uses 40%, Critical 60%, High 80%, Moderate 100%. Weights can be adjusted in the app; they are demo settings, not medical rules. The app displays a plain-language rationale and factor breakdown for every candidate.

The donor records, distances, and response estimates are fictional. "Simulate contact" only records a demo event; the app sends no messages. A real care team would contact verified candidates using an authorized channel and registry. Request verification must also happen outside the prototype. Progress is derived from current Accepted responses and capped at the requested units. Request IDs must be unique within a session. Session data resets when the Streamlit session ends.

The **Donor Screening** page lets donors enter their own name, age (18+), weight, gender, and optional hemoglobin value. These details stay in the active Streamlit session; they are not shown in ranked results or included in audit events. The prototype has no sign-in or identity verification, so self-entry is not proof of identity or eligibility. Each submission starts **Blood-bank review pending**. The demo review control only records a workflow step; it does not represent a real clinician's review. No health thresholds are applied. This boundary follows e-RaktKosh's note that its questionnaire is general guidance and donors should consult a doctor: [e-RaktKosh](https://eraktkosh.mohfw.gov.in/).

## Five manual checks

1. Pending request verification blocks matching; a verified demo request opens results. The default B+ request should show several candidates.
2. Exact and prototype-compatible groups appear; incompatible groups do not.
3. Unavailable candidates are excluded; unconfirmed availability scores lower.
4. Contact multiple candidates, accept more than the requested units, then change one response; progress should recalculate accurately.
5. Submit donor details with age under 18 and confirm the form rejects them; submit age 18+ and confirm details are absent from ranked results and audit events.
6. Confirm audit events appear and donor lists show anonymized IDs without personal details. Also try zeroing all weights; the app should explain that it is using defaults.
