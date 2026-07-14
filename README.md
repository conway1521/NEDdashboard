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

County-level input data is not committed to this repository. The `src/` directory contains the data pipeline and aggregation logic. Data sources include the American Community Survey, BLS LAUS, FDIC, FCC, and several CDC and EPA datasets.

## Deployment

This project is configured for Render (`render.yaml` included). The live deployment is at [NED Dashboard](https://neddashboard.onrender.com). _N.b., it takes a bit to load upon the first time, about 1.5-2 minutes._
