# NED Dashboard

A quantitative assessment tool for researchers and local policymakers to measure inclusive economic development at the county level. This dashboard was built on the premise that aggregate metrics like GDP miss the structural conditions that make prosperity durable and broadly shared.

The framework organizes county-level data across three pillars: **Place-based Conditions** (health, environment, housing, transport), **Human and Social Capital** (education pipelines, social networks, opportunity youth), and **Economic Activity** (labor market outcomes, household wealth, business environment). Scores across pillars are treated as complements whereby a county with strong economic output but weak place-based conditions signals extraction, not development. Crucially, this lack of substitutability is a feature that has been shared by field-practitioners across California during my time working at Jobs For the Future (JFF).

The dashboard was built in Python using Pandas, Plotly, and Plotly Dash in 2022-2023.

## Background

The NED framework draws from two bodies of work:

1. Recent economic research on the roles of social networks, geography, credit access, and wealth accumulation in shaping local development trajectories
2. Field learning from community-based organizations, workforce boards, and community colleges on what conditions households actually need to access opportunity

Nine indicator categories follow from this: Basic Needs, Access, Education and Talent, Social Capital, Growth and Prosperity, Labor Market, Household Income, Household Wealth, and Business Environment.

## Data

The county-level input data is in `docs/data/`, and the aggregation logic is in `src/pages/tool.py` (mirrored in `docs/assets/ned-data.js`). Data sources include the American Community Survey, BLS LAUS, FDIC, FCC, and several CDC and EPA datasets.

## Deployment

The live dashboard is a static site served by GitHub Pages from the `docs/` folder: [NED Dashboard](https://conway1521.github.io/NEDdashboard/). It loads instantly, with no server or cold start.

- `docs/assets/ned-data.js` is a JavaScript port of the scoring pipeline in `src/pages/tool.py` (normalisation, Topic/Subject/Pillar aggregation, rankings and population-weighted averages). Its output matches the Python version exactly.
- `docs/assets/ned-app.js` draws the charts with Plotly.js.
- `docs/data/` holds the county input data and geometry. Both the static site and the Python app read from it, so there is one copy to update.

To preview locally, run `python3 -m http.server -d docs` and open http://localhost:8000.

The original Python/Dash app is kept in `src/` for reference and can be run locally with `pip install -r requirements.txt` and `python src/app.py` (Python 3.10, matching the pinned 2023 dependencies).
