# Historical Antarctic Weather / Snow Exports

Place an authorised NCPOR or IMD historical CSV/JSON export here, for example:

- `maitri_historical.csv`
- `bharati_historical.csv`

Supported fields include `timestamp`, `snowfall_mm`, `snow_depth_m`, and
`precipitation_mm` plus common aliases.

The application does **not** fabricate historical snowfall. The NCPOR public
portal lists historical Maitri datasets (including SASE 2006-2015), but this
prototype does not claim an undocumented machine-readable download API.
