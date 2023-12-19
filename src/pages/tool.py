#========================================PACKAGES

# *** JFC *** Notes 11-Dec-2023
# Changes include:
# - moved graph calculations into unique functions (choropleths, bar, sunflower, etc)
# - made sure only the graph needed now is calculated
# - memoized the graphs, so they are calculated once and re-used
# - added some timing that can be removed later

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template("lux")
import numpy as np
from urllib.request import urlopen
import json
import pathlib
from sklearn.preprocessing import MinMaxScaler
import functools  # ***JFC*** - for memoization with lru_cache, used on plot functions
import time  # ***JFC*** - for timing

# ***JFC*** - timing access to the URL
tic = time.perf_counter()
print("Opening URL for geojson-counties-fips...")
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
toc = time.perf_counter()
print(f"Time for urlopen() is {toc - tic:0.4f} secs")
#========================================


#========================================INPUTING AND CLEANING THE DATA
# Layers

location = pathlib.Path(__file__).parent.parent

# ***JFC*** - timing set up of the page
tic = time.perf_counter()

df_p = pd.read_csv(f'{location}/assets/placedata.csv', dtype={'fips':str})
df_hsc = pd.read_csv(f'{location}/assets/humansocialdata.csv', dtype={'fips':str})
df_e = pd.read_csv(f'{location}/assets/econdata.csv', dtype={'fips':str})

df_first2 = pd.merge(df_p, df_hsc, on='fips', how='inner')
df_tot = pd.merge(df_first2, df_e, on='fips', how='inner')
df_tot = df_tot.drop(columns=['county', 'county_y'])
df_tot.rename(columns={"county_x": "county"}, inplace=True)

# Other
df_indices = pd.read_csv(f'{location}/assets/indices.csv', dtype={'fips':str})
df_industry = pd.read_csv(f'{location}/assets/industrydata.csv', dtype={'fips':str})
df_pop_weight = pd.read_csv(f'{location}/assets/popweightdata.csv', dtype={'fips':str})
# ------------------------------------------------------------------------------------------------------------
# SETTING UP TOPIC DICTIONARY
def getColNames(allColNames: list, startName: str, endName: str) -> list:
    index1 = allColNames.index(startName)
    index2 = allColNames.index(endName)
    subset = [allColNames[i] for i in range(index1, index2 + 1)]

    return subset

# place
df_p_colnames = list(df_p.columns)
df_p_dict = {"envhealth": ('fips', 'county', *getColNames(df_p_colnames, "water_violation", "particulate_matter")),
             "foodhealth": ('fips', 'county', *getColNames(df_p_colnames, "uninsured", "food_insec")),
             "housing": ('fips', 'county', *getColNames(df_p_colnames, "severe_housing", "crime_rate")),
             "transport": ('fips', 'county', *getColNames(df_p_colnames, "vehicle_avail", "commute_long")),
             "access_bcb": (
                 'fips', 'county', *getColNames(df_p_colnames, "access_finance_insurance", "access_broadband")),
             "innovcreation": ('fips', 'county', *getColNames(df_p_colnames, "r1_univ", "rd_density")),
             "skillbuilding": ('fips', 'county', *getColNames(df_p_colnames, "cc_density", "csu")),
             }
df_p_subj_dict = {"basic_needs": ('county', "envhealth", "foodhealth", "housing", "transport"),
                  "access": ('county', "access_bcb", "innovcreation", "skillbuilding")}
df_pgraph_dict = {"envhealth":"iii. Environmental Health",
                  "foodhealth":"iii. Food and Physical Health Security",
                  "housing":"iii. Housing and Neighborhoods",
                  "transport":"iii. Transportation",
                  "access_bcb":"iii. Access to Finance Institutions, Childcare, and Broadband",
                  "innovcreation":"iii. Density of Innovative Creation Organizations",
                  "skillbuilding":"ii. Density of Skill-building Centers"
}
df_pgraph_subj_dict = {"basic_needs":"ii. Basic Needs",
                       "access":"ii. Access",
}

# human and social capital
df_hsc_colnames = list(df_hsc.columns)
df_hsc_dict = {"educattain": ('fips', 'county', *getColNames(df_hsc_colnames, "attain_nohs", "MYS")),
              "schooling": ('fips', 'county', *getColNames(df_hsc_colnames, "enrol_preschool", "juvenile_felony")),
              "oppyouth": ('fips', 'county', *getColNames(df_hsc_colnames, "highered_enroll", "discon_youth")),
              "socialnet": ('fips', 'county', *getColNames(df_hsc_colnames, "econ_con", "clustering")),
              "socialcohesion": ('fips', 'county', *getColNames(df_hsc_colnames, "support_ratio", "civic_orgs")),
              }
df_hsc_subj_dict = {"eductalent": ('county', "educattain", "schooling", "oppyouth"),
                   "socialcapital": ('county', "socialnet", "socialcohesion")}
df_hscgraph_dict = {"educattain":"iii. Educational Attainment, current adults",
                  "schooling":"iii. Schooling Outcomes, current students",
                  "oppyouth":"iii. Transitional and Opportunity Youth",
                  "socialnet":"iii. Social Networks",
                  "socialcohesion":"iii. Social Cohesion"
}
df_hscgraph_subj_dict = {"eductalent":"ii. Education and Talent",
                  "socialcapital":"ii. Social Capital",
}

# economic development
df_e_colnames = list(df_e.columns)
df_e_dict = {"size": ('fips', 'county', *getColNames(df_e_colnames, "rgdp_18", "rgdp_10yr")),
             "stdliving": ('fips', 'county', "rgdp_capita"),
             "prod": ('fips', 'county', *getColNames(df_e_colnames, "prod_jobs", "prod_worker")),
             "jobs": ('fips', 'county', *getColNames(df_e_colnames, "jobs", "jobs_young_prop")),
             "emp": ('fips', 'county', *getColNames(df_e_colnames, "emp_to_pop", "jobs_highskill")),
             "u": ('fips', 'county', *getColNames(df_e_colnames, "u", "u_youth_gap")),
             "lf": ('fips', 'county', *getColNames(df_e_colnames, "lfp", "lfp_youth_gap")),
             "earn": ('fips', 'county', *getColNames(df_e_colnames, "earn_med", "earn_med_gender_gap")),
             "hhinc": ('fips', 'county', *getColNames(df_e_colnames, "hh_inc_med", "hh_rentburden")),
             "poverty": ('fips', 'county', *getColNames(df_e_colnames, "poverty_prop", "poverty_under18")),
             "assistance": ('fips', 'county', *getColNames(df_e_colnames, "assist_food", "assist_cash")),
             "incineq": ('fips', 'county', *getColNames(df_e_colnames, "gini_inc", "inc_ratio")),
             "homeown": ('fips', 'county', *getColNames(df_e_colnames, "home_own", "home_own_edgap")),
             "bank": ('fips', 'county', *getColNames(df_e_colnames, "hh_underbank", "hh_unbank")),
             "finresil": ('fips', 'county', *getColNames(df_e_colnames, "asset_pov_rate", "l_asset_pov_rate")),
             "patents": ('fips', 'county', *getColNames(df_e_colnames, "patents_per1000", "patent_5yr")),
             "bus": ('fips', 'county', "num_establishments"),
             "smallbusloan": ('fips', 'county', *getColNames(df_e_colnames, "loan_smallbus_number", "loan_avg"))
             }
df_e_subj_dict = {"growthprosp": ('county', "size", "stdliving", "prod"),
                  "labormarket": ('county', "jobs", "emp", 'u', "lf", "earn"),
                  "income": ('county', "hhinc", "poverty", "assistance", "incineq"),
                  "wealth": ('county', "homeown", "bank", "finresil"),
                  "busenv": ('county', "patents", "bus", "smallbusloan")}
df_egraph_dict = {"size":"iii. Size of Local Economy",
                  "stdliving":"iii. Standard of Living",
                  "prod":"iii. Productivity",
                  "jobs":"iii. Jobs",
                  "emp": "iii. Employment",
                  "u": "iii. Unemployment",
                  "lf": "iii. Labor Force",
                  "earn": "iii. Earnings",
                  "hhinc": "iii. Household Income",
                  "poverty": "iii. Poverty",
                  "assistance": "iii. Budgetary Assistance",
                  "incineq": "iii. Income Inequality",
                  "homeown": "iii. Homeownership",
                  "bank": "iii. Access to Wealth",
                  "finresil": "iii. Financial Resilience",
                  "patents": "iii. Patents",
                  "bus": "iii. Business Establishments",
                  "smallbusloan": "iii. Loans to Small Businesses"
}
df_egraph_subj_dict = {"growthprosp":"ii. Growth and Prosperity",
                       "labormarket":"ii. Labor Market",
                       "income": "ii. Household Income",
                       "wealth": "ii. Household Wealth",
                       "busenv": "ii. Business Environment",
}

df_tot_dict = {**df_p_dict, **df_hsc_dict, **df_e_dict}
df_tot_subj_dict = {**df_p_subj_dict, **df_hsc_subj_dict, **df_e_subj_dict}
df_totgraph_dict = {**df_pgraph_dict, **df_hscgraph_dict, **df_egraph_dict}
df_totgraph_subj_dict = {**df_pgraph_subj_dict, **df_hscgraph_subj_dict, **df_egraph_subj_dict}

# NORMALISATION ROUTINE

# For normalisation of positive components (life expectancy, higher the better), use Min-max (x-min)/(max-min)
# Certain variables have bounds, so will scale non-linearly to account for quality increases (HIHD)
# For normalisation of negative components (unemployment, lower the better), do 1 minus Min Max (or logMinMax)

df_fipscounty = df_tot.iloc[:, 0:2]
df_county = df_tot.iloc[:, 1]

# place
df_p_toscale = df_p.iloc[:, 2:]
scaler = MinMaxScaler()
scaler.fit(df_p_toscale)
MinMaxScaler()
df_p_n = scaler.transform(df_p_toscale)
df_p_n = pd.DataFrame(df_p_n, columns=df_p_toscale.columns)
df_p_n = pd.concat([df_fipscounty, df_p_n], axis=1)
df_p_n["water_violation"] = (1 - df_p_n["water_violation"])
df_p_n["particulate_matter"] = (1 - df_p_n["particulate_matter"])
df_p_n["uninsured"] = (1 - df_p_n["uninsured"])
df_p_n["years_lost"] = (1 - df_p_n["years_lost"])
df_p_n["limited_healthyfood"] = (1 - df_p_n["limited_healthyfood"])
df_p_n["food_insec"] = (1 - df_p_n["food_insec"])
df_p_n["severe_housing"] = (1 - df_p_n["severe_housing"])
df_p_n["rent_costburden"] = (1 - df_p_n["rent_costburden"])
df_p_n["housing_afford"] = (1 - df_p_n["housing_afford"])
df_p_n["homelessness"] = (1 - df_p_n["homelessness"])
df_p_n["resid_vacancy"] = (1 - df_p_n["resid_vacancy"])
df_p_n["crime_rate"] = (1 - df_p_n["crime_rate"])
df_p_n["commute_time"] = (1 - df_p_n["commute_time"])
df_p_n["commute_long"] = (1 - df_p_n["commute_alone"])
df_p_n["access_broadband"] = (1-df_p_n["access_broadband"])

# human and social capital
df_hsc_toscale = df_hsc.iloc[:, 2:]
scaler = MinMaxScaler()
scaler.fit(df_hsc_toscale)
MinMaxScaler()
df_hsc_n = scaler.transform(df_hsc_toscale)
df_hsc_n = pd.DataFrame(df_hsc_n, columns=df_hsc_toscale.columns)
df_hsc_n = pd.concat([df_fipscounty, df_hsc_n], axis=1)
df_hsc_n["suspensions"] = (1 - df_hsc_n["suspensions"])
df_hsc_n["juvenile_felony"] = (1 - df_hsc_n["juvenile_felony"])
df_hsc_n["discon_youth"] = (1 - df_hsc_n["discon_youth"])

#econ dev
df_e_toscale = df_e.iloc[:, 2:]
scaler = MinMaxScaler()
scaler.fit(df_e_toscale)
MinMaxScaler()
df_e_n = scaler.transform(df_e_toscale)
df_e_n = pd.DataFrame(df_e_n, columns=df_e_toscale.columns)
df_e_n = pd.concat([df_fipscounty, df_e_n], axis=1)
df_e_n["jobs_unstable_prop"] = (1 - df_e_n["jobs_unstable_prop"])
df_e_n["u"] = (1 - df_e_n["u"])
df_e_n["u_ed_gap"] = (1 - df_e_n["u_ed_gap"])
df_e_n["u_youth_gap"] = (1 - df_e_n["u_youth_gap"])
df_e_n["below_15000"] = (1 - df_e_n["below_15000"])
df_e_n["below_25000"] = (1 - df_e_n["below_25000"])
df_e_n["hh_houseburden"] = (1 - df_e_n["hh_houseburden"])
df_e_n["hh_rentburden"] = (1 - df_e_n["hh_rentburden"])
df_e_n["poverty_prop"] = (1 - df_e_n["poverty_prop"])
df_e_n["poverty_under18"] = (1 - df_e_n["poverty_under18"])
df_e_n["assist_food"] = (1 - df_e_n["assist_food"])
df_e_n["assist_income"] = (1 - df_e_n["assist_income"])
df_e_n["assist_cash"] = (1 - df_e_n["assist_cash"])
df_e_n["gini_inc"] = (1 - df_e_n["gini_inc"])
df_e_n["inc_ratio"] = (1 - df_e_n["inc_ratio"])
df_e_n["hh_underbank"] = (1 - df_e_n["hh_underbank"])
df_e_n["hh_unbank"] = (1 - df_e_n["hh_unbank"])
df_e_n["asset_pov_rate"] = (1 - df_e_n["asset_pov_rate"])
df_e_n["hh_noNW"] = (1 - df_e_n["hh_noNW"])
df_e_n["l_asset_pov_rate"] = (1 - df_e_n["l_asset_pov_rate"])


# AGGREGATION BY DICT- topic
# for dict in layer, select columns of the normalized df, and then average across to get a new variable vector
# Multiply by 10 to get score out of 10. if best in all scores, then would get 1 overall, this just puts in a more legible scale

# place
df_p_aggs = pd.DataFrame()
for dictentry in df_p_dict:
    subset = df_p_n.loc[:, df_p_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_p_aggs[dictentry] = vector * 10
df_p_aggs.insert(0, "county", df_county)

# human and social capital
df_hsc_aggs = pd.DataFrame()
for dictentry in df_hsc_dict:
    subset = df_hsc_n.loc[:, df_hsc_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_hsc_aggs[dictentry] = vector * 10
df_hsc_aggs.insert(0, "county", df_county)

# econ
df_e_aggs = pd.DataFrame()
for dictentry in df_e_dict:
    subset = df_e_n.loc[:, df_e_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_e_aggs[dictentry] = vector * 10
df_e_aggs.insert(0, "county", df_county)

# total
df_first2_aggs = pd.merge(df_p_aggs, df_hsc_aggs, on='county', how='inner')
df_tot_aggs = pd.merge(df_first2_aggs, df_e_aggs, on='county', how='inner')


# AGGREGATION BY DICT- Subject
# for dict in layer, select columns of the aggregated topic df, and then average across to get a new variable vector

# place
df_p_subj_aggs = pd.DataFrame()
for dictentry in df_p_subj_dict:
    subset = df_p_aggs.loc[:, df_p_subj_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_p_subj_aggs[dictentry] = vector
df_p_subj_aggs.insert(0, "county", df_county)

df_p_pill_aggs = pd.DataFrame(df_p_subj_aggs.mean(axis=1, numeric_only=True), columns=["p"])
df_p_pill_aggs.insert(0, "county", df_county)

# human and social capital
df_hsc_subj_aggs = pd.DataFrame()
for dictentry in df_hsc_subj_dict:
    subset = df_hsc_aggs.loc[:, df_hsc_subj_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_hsc_subj_aggs[dictentry] = vector
df_hsc_subj_aggs.insert(0, "county", df_county)

df_hsc_pill_aggs = pd.DataFrame(df_hsc_subj_aggs.mean(axis=1, numeric_only=True), columns=["hsc"])
df_hsc_pill_aggs.insert(0, "county", df_county)

# econ
df_e_subj_aggs = pd.DataFrame()
for dictentry in df_e_subj_dict:
    subset = df_e_aggs.loc[:, df_e_subj_dict.get(str(dictentry))]
    vector = subset.mean(axis=1, numeric_only=True)
    df_e_subj_aggs[dictentry] = vector
df_e_subj_aggs.insert(0, "county", df_county)

df_e_pill_aggs = pd.DataFrame(df_e_subj_aggs.mean(axis=1, numeric_only=True), columns=["e"])
df_e_pill_aggs.insert(0, "county", df_county)

# total
df_first2_aggs = pd.merge(df_p_subj_aggs, df_hsc_subj_aggs, on='county', how='inner')
df_tot_subj_aggs = pd.merge(df_first2_aggs, df_e_subj_aggs, on='county', how='inner')

df_first2_pillars = pd.merge(df_p_pill_aggs, df_hsc_pill_aggs, on='county', how='inner')
df_pillars = pd.merge(df_first2_pillars, df_e_pill_aggs, on='county', how='inner')
df_pillars_fips = df_pillars.copy()
df_pillars_fips.insert(1, 'fips', df_fipscounty.iloc[:,0])

df_nedscore = pd.DataFrame(df_pillars.mean(axis=1, numeric_only=True), columns=["NED"])
df_nedscore.insert(0, "county", df_county)
df_nedscore_fips = df_nedscore.copy()
df_nedscore_fips.insert(1, 'fips', df_fipscounty.iloc[:,0])

df_nedpillars = pd.merge(df_nedscore, df_pillars, on='county', how='inner')
df_nedpillars_fips = pd.merge(df_nedscore_fips, df_pillars, on='county', how='inner')

# Rankings for topics

df_p_rank = df_p_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                    na_option='bottom').astype(int).reset_index()
df_hsc_rank = df_hsc_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                      na_option='bottom').astype(int).reset_index()
df_e_rank = df_e_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                    na_option='bottom').astype(int).reset_index()

# total
df_first2_rank = pd.merge(df_p_rank, df_hsc_rank, on='county', how='inner')
df_tot_rank = pd.merge(df_first2_rank, df_e_rank, on='county', how='inner')

df_p_subj_rank = df_p_subj_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                              na_option='bottom').astype(int).reset_index()
df_hsc_subj_rank = df_hsc_subj_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                                na_option='bottom').astype(int).reset_index()
df_e_subj_rank = df_e_subj_aggs.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                              na_option='bottom').astype(int).reset_index()

# total
# df_first2_rank = pd.merge(df_p_rank, df_hsc_rank, on='county', how='inner')
# df_tot_rank = pd.merge(df_first2_rank, df_e_rank, on='county', how='inner')

df_first2_subj_rank = pd.merge(df_p_subj_rank, df_hsc_subj_rank, on='county', how='inner')
df_tot_subj_rank = pd.merge(df_first2_subj_rank, df_e_subj_rank, on='county', how='inner')

df_nedpillars_rank = df_nedpillars.set_index('county').transform(pd.Series.rank, 0, method='max', ascending=False,
                                                              na_option='bottom').astype(int).reset_index()

df_nedpillars_rank = df_nedpillars_rank.rename(columns={"NED": "NED_r", "p": "p_r", "hsc": "hsc_r", "e": "e_r"})
#-----------------------------------------------------------------------------------------------------------------------





#=======================================================================================================================
#=======================================================================================================================
#=======================================================================================================================

## DASH

#-----------------------------------------------------------------------------------------------------------------------
#Data of webpage
color_graphbg = '#fafbfb' #'rgba(247,247,249,255)' #grey of dropdown men, 'rgba(179, 205, 227, 0.15)' light blue
#dbc LUX colors
color_NED = "#d8534f"
color_p = "#4abf73"
color_hsc = "#f0ad4e"
color_e = "#209bcf"

color_red = "rgba(226,126,123,255)"

# Make a list of subject strings for each of the three pillars
pillar_subjects = [ ['Environmental Health', 'Food and Physical Health Security', 'Housing',
                    "Transportation", "Access to Banking, Childcare, and Broadband",
                    "Innovation and Creation Institutions", "Skill-building"],
                   ['Educational Attainment', 'Schooling Outcomes', 'Opportunity Youth',
                    'Social Networks', 'Social Cohesion'],
                   ['Size of Local Economy', 'Standard of Living', 'Productivity', 'Jobs',
                    'Employment', "Unemployment", "Labor Force Participation", "Earnings",
                    "Household Income", "Poverty", "Budgetary Assistance", "Income Inequality",
                    "Homeownership", "Banking", "Financial Resilience", "Patents", "Businesses",
                    "Small Business Loans"]
                 ]
# Join the strings for each pillar with <br> - this is for hover-text, one subject per line
pillar_subjects_formatted = ["<br>".join(subject) for subject in pillar_subjects]
# Make a dataframe with three columns - pillar string, value of zero to plot as circle, subjects string (formatted)
df_pillarsintro = pd.DataFrame({'pillar': ['Place-based Conditions', 'Human and Social Capital', "Economic Activity"],
                               'value': [0, 0, 0],
                               'subjects': pillar_subjects_formatted,
                               })

pillarcirclesfig = px.scatter(df_pillarsintro, x='pillar', y='value', color='pillar', #template = "lux",
                                 color_discrete_map={
                                     "Place-based Conditions": color_p,
                                     "Human and Social Capital": color_hsc,
                                     "Economic Activity": color_e
                                 },
                                 custom_data='subjects',          # This column is used as-is for hover text
                                 )
pillarcirclesfig.update_traces(marker=dict(size=60, line=dict(width=1.5, color='DarkSlateGrey')),
                              name="",                        # suppresses the extra text outside hover-text boxes
                              hovertemplate="%{customdata}",  # formatted text in the hover-text boxes
                              )
pillarcirclesfig.update_xaxes(showgrid=False)
pillarcirclesfig.update_yaxes(showgrid=False,
                             zeroline=False,
                             showticklabels=False,
                             )
pillarcirclesfig.layout.xaxis.fixedrange = True
pillarcirclesfig.layout.yaxis.fixedrange = True
pillarcirclesfig.update_layout(
   title=None,
   xaxis_title=None,
   yaxis_title=None,
   showlegend=False,
)
pillarcirclesfig.update_layout(height=320, plot_bgcolor='white', font=dict(size=17))



df_pillars = pd.merge(df_nedpillars_fips, df_nedpillars_rank, on='county', how='inner')
df_pillars = df_pillars.round(1)

df_subjects = df_tot_subj_aggs.copy()

df_topics = df_tot_aggs.copy()
df_topics.insert(1, 'fips', df_fipscounty.iloc[:,0])
df_topics = df_topics.round(1)

df_subjects_rank = df_tot_subj_rank.copy()

df_topics_rank = df_tot_rank.copy()


choromenu: list = [
                    {"label": "New Economic Development", "value": "NED"},
                    {"label": "i. Place-based Conditions", "value": "p"},
                    {"label": "i. Human and Social Capital", "value": "hsc"},
                    {"label": "i. Economic Activity", "value": "e"}
]

countymenu: list = []
for index, row_name in enumerate(df_county):
    countymenu.append({'label': row_name, 'value': row_name})

#-----------------------------------------------------------------------------------------------------------------------
#Build components

intro_text = '''Individuals' lived experience and local conditions are increasingly understood as key components of a community's economic development. But what constitutes inclusive, sustainable, and effective local economic development? How can policymakers, researchers, and social entrepreneurs understand this fuller regional development lens, identify areas of opportunity, and come up with successful strategies? Aside from few local examples, no such comprehensive, nationally scalable assessment exists.

The New Economic Development (NED) tool does just that.
'''

ned_text1 = '''
NED combines frontier interdisciplinary research with key field-derived learning to represent the drivers of inclusive economic development through three distinct Pillars.
'''

ned_text2place = '''
...refer to the physical foundation upon which people live. Health, 
environment, and access are factored along with other metrics of thriving communities.'''

ned_text2humancap = '''
...cover the enablers of development given by individual 
education to social affiliation. This includes training pipelines and the strength of networks.
'''

ned_text2econact = '''
...represents material and financial prosperity, potential, 
and resilience. This is the 'size of the local economic pie' and how its 'slices' are distributed.
'''

intro_text2 = '''
Crucially, the balance of indicator levels across these three Pillars is what determines a place's standing. *Delve deeper in the [About this tool](/about) page.*
'''
intro_text3 = '''
>From granular US census, business, workforce, and social networks data, evaluate and compare local economic development the NED way across California's 58 counties based on 30 essential topics for material living conditions and equitable quality of life. Select either the [California](#toCA) or the individual [County](#toCounty) views below.
'''
choro_text1 = '''
See how inclusive economic development is distributed across California. Each of the three Pillars (*i.*) are presented individually and as an averaged general NED score, which serves as a benchmark and a comparison to common single development metrics like Gross Regional Product or the Human Development Index.

*Select a dimension from the menu below, and use the buttons above it to toggle between the Map and Bar chart.*
'''

county_text = '''
Analyze individual counties' performance the NED way through the three subsequent levels of depth to identify the particular situation they're in.

1. Start top left with the Pillars (i.) barometer, which shows the general balance forming inclusive, sustainable economic development.  
*Ex: large magnitudes (Los Angeles) and lack of balance (Butte) showcase the variety of county experiences.*

2. Dig deeper with the eight Subjects (ii.) on the right showing the major categories underlying each Pillar.  
*Ex: significant differences within Pillars (Lassen, Economic Activity and Place-based Conditions) or Santa Clara (Economic Activity) highlight how balance (or imbalance) can scale whatever a county's means are.*

3. Finally, examine the distribution of Topics (iii., below) rankings to see specifically where counties specialize, and where they are weaker.  
*Ex: Skewed higher spreads (San Francisco) evidence the need for targeted approaches to comparatively improve local NED, whereas more concentrated lower rankings (Imperial) or widespread scores (Amador) suggest a comprehensive economic development plan is required.*

*Start by selecting a county using the dropdown menu below, and hover over the figures for more information. For simplification, *Place-based Conditions*, *Human and Social Capital*, and *Economic Activity* will be respectively shortened to *PbC*, *HSC*, and *EA*.*
'''

modal = html.Div(
    [
        dbc.Button("The NED Approach", id="open", n_clicks=0, color="dark", outline=True, className="me-1"),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Inclusive, Sustainable, and Effective Economic Growth")),
                dbc.ModalBody([
                    dbc.Row(
                        [
                            dbc.Col(dcc.Markdown(ned_text1), width = {"size":"auto"})
                        ]

                    ),
                    dbc.Row(
                        [
                            dcc.Graph(figure=pillarcirclesfig,config={'displayModeBar': False})
                        ]
                    ),

                    dbc.Row(
                        [
                            dbc.Col(dcc.Markdown(ned_text2place), width={"size": 4}),
                            dbc.Col(dcc.Markdown(ned_text2humancap), width={"size": 4}),
                            dbc.Col(dcc.Markdown(ned_text2econact), width={"size": 4}),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Markdown('''The NED Pillars (notated with an *i.* for clarity) are made up of Subjects (*ii.*) covering their relevant categories, which are themselves composed of Topics (*iii.*), composites of measured data.'''))
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Markdown(intro_text2), width = {"size":"auto"})
                        ]
                    ),
                ]),
            ],
            id="modal",
            size="xl",
            is_open=False,
        ),
    ], className="d-grid gap-2 d-md-flex justify-content-md-center",
)


chorotitle = dcc.Markdown(children='')
choro_graph = dcc.Graph(figure={}, config={'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso2d']})
nedpillar_graph = dcc.Graph(figure={})
choro_dropdown = dcc.Dropdown(options= choromenu,
                              value='NED',
                              clearable=False)
chorotab_See = dcc.Markdown(children='', link_target="_blank")
chorotab_Mean = dcc.Markdown(children='', link_target="_blank")
chorotab_See_content = dbc.Card(
    dbc.CardBody(
        [
            chorotab_See,
        ]
    ), className="mt-3",
)
chorotab_Mean_content = dbc.Card(
    dbc.CardBody(
        [
            chorotab_Mean,
        ]
    ), className="mt-3",
)

choro_tabs = html.Div(
            [
                dbc.Tabs(
                    [
                        dbc.Tab(chorotab_See_content, label="WHAT THIS SHOWS:"),
                        dbc.Tab(chorotab_Mean_content, label="WHAT THIS MEANS:"),
                    ],
                ),
            ]
)

chorotabSee_NED = '''
NED development across the State is highly variable and distinctly concentrated around major cities (San Francisco Bay Area, Los Angeles, San Diego). 
The spread is also significant: the score in the lowest county, Tulare, is almost half of top-ranked Marin and Santa Clara's.
'''
chorotabMean_NED = '''
NED is reflecting in large part the outcomes of 'agglomeration economies' (the benefits from firms and people being located near each other in industrial clusters). 
Geographic proximity boosts economic activity and enables the formation of strong social networks, increasing the supply of workers and businesses as well as the demand for an ecosystem around it.
However, agglomeration economies can also produce marked inequalities from higher living costs, gentrification, and social exclusion. From the current vantage point view, this complexity is not perceptible, but the Pillars (*i.*) can start to uncover it.

Consistent with [recent research](https://www.centreforcities.org/reader/office-politics/the-impact-of-agglomeration-on-the-economy/#:~:text=Agglomeration%20occurs%20because%20of%20the,larger%20cities%20and%20industrial%20concentrations.), agglomeration economy spillovers (both positive and negative) are especially strong in the Financial and Business Service sectors and increase with scale, like in the world-class centers of the San Francisco Bay Area, Los Angeles, and San Diego– the regions with the highest NED scores.
'''
chorotabSee_p = '''
Place-based Conditions vary across the state and showcase a wide range: Tulare (lowest) scores less than half of San Francisco (highiest). Significant concentrations exist around industrial clusters on the coast, and unlike with the NED score, to a lesser extent in Northern California.
'''
chorotabMean_p = '''
This Pillar measures the ecosystems being built up around agglomeration, as well as geographic idiosyncracies at play. 
In addition to attracting Research and Development firms and universities, industrial cluster counties offer more in terms of basic needs and access to services. 
But, they trade off higher housing costs, longer commute times, and environmental health to name a few. 
Counties that are more isolated from high economic activity can still offer an empowering ecosystem for their residents (a merit for instance of widespread higher education systems), but this is decreasing with scale.

To note, the central counties forming a major ground transportation corridor for goods experience significantly worse environmental quality, which contributes to their worse Place-based Conditions.
'''
chorotabSee_hsc = '''
Human and Social Capital are still quite variable across California, but the spread is less extreme: San Luis Obispo (highest) scores less than double Alpine (lowest).
'''
chorotabMean_hsc = '''
Social and Human Capital will concentrate around economic activity, both due to demand (firms that can afford to pay for high skills will do so) and supply (highly skilled and connected individuals want to work in areas with lucrative returns).
This more even concentration around cities is due in part to the greater presence of Higher Education as well as greater social capital. However, quality education systems can help share this more evenly (recalling the intersection with the Place-based Conditions Pillar).

Social networks can facilitate new matches being made and professional advancement, creating a reinforcing loop.
As [Chetty *et al*, 2022](https://socialcapital.org) find, the strength of social networks is conducive to upward mobility, both for adults and for children in schools. 
'''
chorotabSee_e = '''
The Economic Activity Pillar showcases the most variation and spread. Santa Clara (highest score) scores more than triple what Imperial (lowest) reaches. Likewise, we see a much higher skew given by the highest scorers being so significantly high. 
'''
chorotabMean_e = '''
Given the sheer size and significance of California's economy, it is natural for Economic Acitivty to be concentrated around its main engines, the world-class industrial clusters. Agglomeration around them creates high demand for exogenous assets, which in turn create more prosperity and create a self-reinforcing loop. It follows that this decreases with scale.

Inequalities and wealth divides are especially apparent in counties with high exogenous economic growth (where people, firms, and assets move to due to demand, pricing out locals who are not able to tap into the high-earning workstreams), which is . The importance of the other Pillars is in keeping this in check.
'''

closing_text = '''
*Continue onto the [About this tool](/about) page to read more about the NED approach and potential applications of this tool, and explore the [Methodology](/methodology) for the technical decisions that went into its development.*
'''

countytitle = dcc.Markdown(children='')
county_pillarsgraph = dcc.Graph(figure={}, config={'modeBarButtonsToRemove': ['select', 'lasso2d']})
county_flower = dcc.Graph(figure={}, config={'modeBarButtonsToRemove': ['zoom', 'select', 'lasso2d']})
county_dropdown = dcc.Dropdown(options= countymenu,
                              value='Alameda',
                              clearable=False)
county_top5bot5graph = dcc.Graph(figure={}, config={'modeBarButtonsToRemove': ['select', 'lasso2d']})

#------------------------------------------------------
# Radio items
radio_mapbar = dcc.RadioItems(
    id = 'radio_mapbar',
    options = [
        {'label': ' Map ', 'value': 'map'},
        {'label': ' Bar chart (rankings).', 'value': 'bar'}
    ],
    value = 'map',
    inline=True,
    className="mb-4"
)

radio_alpharank = dcc.RadioItems(
    id = 'radio_alpharank',
    options = [
        {'label': ' alphabetically ', 'value': 'alph'},
        {'label': ' by rank.', 'value': 'rank'}
    ],
    style={'margin-right': '50px'},
    value = 'alph',
    inline=True,
    className="mb-4"
)



#-----------------------------------------------------------------------------------------------------------------------
# Registering page
dash.register_page(
    __name__,
    path='/',
    title='New Economic Development',
    name='NED tool'
)
#-----------------------------------------------------------------------------------------------------------------------
# LAYOUT OF THE WEBPAGE
layout = dbc.Container([
    html.H1('The NED Interactive Tool', style={'fontsize': '48px', 'text-align': 'center', 'color': "#d8534f"}),
    html.Br(),
    dbc.Row([dcc.Markdown(intro_text)]),
    dbc.Row([modal]),
    html.Br(),
    dbc.Row([dcc.Markdown(intro_text3, id = "toCA")]),
    html.Br(),
#------------
    html.H3("California NED", style={'fontsize': '24px', 'text-align': 'left', 'color': 'rgb(52,60,68)'}, id="ca"),
    dcc.Markdown(children=choro_text1),
    dbc.Row(
        [
            dbc.Col([chorotitle], width='auto'),
            dbc.Col(dcc.Markdown("###### *Sources in Methodology*"), width='auto')
        ],
        justify='between'
    ),
    dbc.Row(
        [
            dbc.Col([choro_graph], width=12)
        ]
    ),
    dbc.Row(
        [
            dbc.Col([choro_dropdown], width=6)
        ],
        justify='center'
    ),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dcc.Markdown("Display:"), width="auto"),
            dbc.Col(radio_mapbar, width='auto'),
        ],
        justify='start',
    ),
    dbc.Row(
        [
            dbc.Col(dcc.Markdown("Display counties of Bar chart"), width = "auto"),
            dbc.Col(radio_alpharank, width='auto'),
        ],
        justify='start',
    ),
    html.Br(),
    dbc.Row([choro_tabs]),
    html.Br(),
    dbc.Row([dcc.Markdown('''*Unpack the variation of NED in California by looking through each of its counties' particular conditions.*''', id = "toCounty")]),
    html.Br(),
    html.Br(),
#------------
    html.H3('County NED', style={'fontsize': '24px', 'text-align': 'left', 'color': 'rgb(52,60,68)'}),
    dcc.Markdown(children=county_text),
    dbc.Row([
        dbc.Col([county_dropdown], width=3)
    ], justify='left'),
    html.Br(),
    dbc.Row([
        dbc.Col([county_pillarsgraph], width=6),
        dbc.Col([county_flower], width=6)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([county_top5bot5graph], width=12)
    ]),
    dbc.Row([
        dbc.Col([countytitle], width='auto')
    ], justify='center'),
    html.Br(),
#------------
    html.Br(),
    dcc.Markdown(children=closing_text),
    html.Br(),
#    footerbar
], fluid=False, className="dbc")

# ***JFC*** - timing set up of the page
toc = time.perf_counter()
print(f"Time for all other stuff is {toc - tic:0.4f} secs")

#-----------------------------------------------------------------------------------------------------------------------
#Allows components to interact

@functools.lru_cache(maxsize=8)   # This memorizes the choropleths, so they are calculated once and saved
def draw_choropleth(choro_selected):
    # Color
    if choro_selected == 'NED':
        chorocholor = 'temps_r'
    elif choro_selected == 'p':   # place-based conditions
        chorocholor = 'emrld'
    elif choro_selected == "hsc": # human and social capital
        chorocholor = 'oryel'
    else:                         # e: economic activity
        chorocholor = 'ice_r'
    # Plotly express
    fig_choro = px.choropleth(df_pillars, geojson=counties, locations='fips', scope="usa", color=choro_selected,
                        color_continuous_scale=chorocholor,
                        height = 600,
                        hover_name=('county'),
                        hover_data={'fips':False}, #would like to round this to 2 significant digits
                        )
    fig_choro.update_geos(fitbounds='locations', visible=False)
    fig_choro.update_layout(
        coloraxis_colorbar=dict(
            title="Score",
        ),
    )
    fig_choro.update_traces(hovertemplate='%{hovertext}: %{z:.1f}<extra></extra>')

    return fig_choro


@functools.lru_cache(maxsize=8)    # This memorizes bar plots, so they are calculated once and saved
def draw_cabars(choro_selected, radioitem_alpharank):
    if choro_selected == 'NED':
        pillar_color = color_NED
    elif choro_selected == 'p':
        pillar_color = color_p
    elif choro_selected == "hsc":
        pillar_color = color_hsc
    else:
        pillar_color = color_e

    if radioitem_alpharank == 'rank':
        df_forpillars = df_pillars.sort_values(choro_selected)
    else:
        df_forpillars= df_pillars

    fig_cabars = px.bar(df_forpillars, x = 'county', y= choro_selected,
                        hover_name = "county",
                        hover_data = {'county': False},
                        text = "county",
    )
    fig_cabars.update_traces(marker_color=pillar_color, opacity=1, marker=dict(line=dict(width=0.33, color='#1a1a1a')))
    fig_cabars.update_xaxes(showgrid=False, showticklabels=False)
    fig_cabars.update_yaxes(showgrid=False, range=[0,6.65])
    fig_cabars.update_layout(
        title=None,
        xaxis_title="County",
        yaxis_title=None
    )
    fig_cabars.update_layout(plot_bgcolor=color_graphbg)
    fig_cabars.update_layout(clickmode="event+select")
    fig_cabars.layout.xaxis.fixedrange = True
    fig_cabars.layout.yaxis.fixedrange = True
    for figure in fig_cabars.data:
        figure.update(
            selected=dict(marker=dict(color=pillar_color)),
            unselected=dict(marker=dict(color=pillar_color, opacity=0.6)),
        )
    fig_cabars.update_traces(hovertemplate='%{x}: %{y:.1f}<extra></extra>')

    return fig_cabars



@callback(
    Output("modal", "is_open"),
    Input("open", "n_clicks"),
    State("modal", "is_open"),
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


@callback(     # number of outputs must equal number of returns below
    Output(choro_graph, 'figure'),
    Output(chorotitle, 'children'),
    Output(chorotab_See, 'children'),
    Output(chorotab_Mean, 'children'),
    Input(choro_dropdown, 'value'),
    Input(radio_mapbar, 'value'),
    Input(radio_alpharank, 'value'),
)
def update_ca(choro_selected, radioitem_mapbar, radioitem_alpharank):
# ***JFC*** - timing update_ca()
    tic = time.perf_counter()

    # Graph-title
    def find_label_from_value(the_list:list, the_value:str) -> str:
        the_label = [element["label"] for element in the_list if the_value in element.values()]
        return the_label[0]

    chorovalue = find_label_from_value(choromenu, choro_selected)

    if radioitem_mapbar == 'map':
        fig_ca = draw_choropleth(choro_selected)
    else:
        fig_ca = draw_cabars(choro_selected, radioitem_alpharank)

# Text for "What this shows" and "What this means"
    if choro_selected == 'NED':
        chorotab_s = chorotabSee_NED
        chorotab_m = chorotabMean_NED
    elif choro_selected == 'p':
        chorotab_s = chorotabSee_p
        chorotab_m = chorotabMean_p
    elif choro_selected == "hsc":
        chorotab_s = chorotabSee_hsc
        chorotab_m = chorotabMean_hsc
    else:
        chorotab_s = chorotabSee_e
        chorotab_m = chorotabMean_e

# ***JFC*** - timing update_ca()
    toc = time.perf_counter()
    print(f"Time for update_ca() is {toc - tic:0.4f} secs")

    return fig_ca, '#### '+chorovalue+' Score', chorotab_s, chorotab_m


@functools.lru_cache(maxsize=128)    # This memorizes plots, so they are calculated once and saved
def draw_countpillars(county_selected):
    sf_pillars_slice = df_pillars.set_index('county').loc[county_selected]
    df_pillars_slice1 = pd.DataFrame({'Pillar': sf_pillars_slice.index, 'Score': sf_pillars_slice.values})
    df_pillars_slice2 = pd.DataFrame(df_pillars_slice1.loc[df_pillars_slice1['Pillar'].isin(['p', 'hsc', 'e'])])

    NED_wavg = np.average(df_nedpillars["NED"], weights=df_pop_weight["pop_perc"])
    p_wavg = np.average(df_nedpillars["p"], weights=df_pop_weight["pop_perc"])
    hsc_wavg = np.average(df_nedpillars["hsc"], weights=df_pop_weight["pop_perc"])
    e_wavg = np.average(df_nedpillars["e"], weights=df_pop_weight["pop_perc"])

    df_pillars_slice2["Pillar"] = ["Place-based Conditions", "Human and Social Capital", "Economic Activity"]
    df_pillars_slice2["Average"] = [p_wavg, hsc_wavg, e_wavg]

    # Plotly express
    fig_countypillars = px.bar(
        df_pillars_slice2, x = 'Pillar', y = 'Score',
        hover_name='Pillar',
        hover_data={'Pillar': False,  # remove from hover data
                    'Score': True,  # add other column, customized formatting
                    },
    )

    fig_countypillars.add_hline(y = NED_wavg, line_width=2.5, line_dash="dash", line_color=color_red
                                , annotation_text = "NED Score CA avg."
                                , annotation_font = dict({"color":"rgba(226,126,123,1)"})
                                , annotation_bgcolor = "rgba(250, 251, 251, 0.35)")   #, annotation_position = "top left")
    fig_countypillars.update_traces(marker=dict(line=dict(width=1,color='#1a1a1a')), marker_color=[color_p, color_hsc, color_e])
    fig_countypillars.update_yaxes(range=[0, np.max(df_pillars['hsc'] + .1)], showgrid=False, fixedrange=True)
    fig_countypillars.update_xaxes(tickmode = 'array', tickvals = df_pillars_slice2['Pillar'], ticktext = ["PbC", "HSC", "EA"], fixedrange=True)
    fig_countypillars.update_layout(title="i. Pillar Scores", title_x=0.5, xaxis_title="Pillar", yaxis_title="Score", plot_bgcolor=color_graphbg)

    return fig_countypillars


@functools.lru_cache(maxsize=128)    # This memorizes plots, so they are calculated once and saved
def draw_subjflower(county_selected):

    subject_slice = df_subjects.set_index('county').loc[county_selected].round(1)
    theta9 = [0, 40, 80, 120, 160, 200, 240, 280, 320]
    NED_wavg = np.average(df_nedpillars["NED"], weights=df_pop_weight["pop_perc"])

    fig_subjflower = go.Figure(go.Barpolar(
        r=subject_slice,
        theta=theta9,
        width=[20, 20, 20, 20, 20, 20, 20, 20, 20],
        marker_color=[color_p, color_p, color_hsc, color_hsc, color_e, color_e, color_e, color_e, color_e],
        marker_line_color="rgba(26,26,26,255)",
        marker_line_width=1,
        opacity=0.8,
        hoverinfo = 'all',
        hovertemplate='%{custom_name}: %{r}<extra></extra>',
        #customdata=[df_totgraph_subj_dict[i] for i in range(len(theta9))],  # Pass custom data for custom_name
    ))
    fig_subjflower.add_trace(go.Scatterpolar(
        r= [NED_wavg.round(1), NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),NED_wavg.round(1),],
        theta=[0, 40, 80, 120, 160, 200, 240, 280, 320, 360],
        mode='lines',
        name='NED avg.',
        line_color=color_red,
        line_dash='dot',
        line_width = 2,
        line_shape = 'spline',
        line_smoothing = 1.3,
        hoverinfo='text',  # Set hoverinfo to 'none' for this trace
        hovertext=['NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.', 'NED Score CA avg.'],
    ))

    fig_subjflower.update_layout(
        grid=None,
        showlegend = True,
        template=None,
        polar=dict(
            radialaxis=dict(range=[0, 8.5], showticklabels=False, ticks=''),
            angularaxis=dict(showticklabels=False, ticks='')
        ),
        title = 'ii. Subject Scores'
    )

    fig_subjflower.layout.xaxis.fixedrange = True
    fig_subjflower.layout.yaxis.fixedrange = True
    fig_subjflower.update_polars(radialaxis=dict(visible=False), bgcolor=color_graphbg, angularaxis_showgrid = False, angularaxis_showline = False)

    return fig_subjflower


@functools.lru_cache(maxsize=128)    # This memorizes plots, so they are calculated once and saved
def draw_fig_county5(county_selected):
    countyslice = df_topics_rank.set_index('county').loc[county_selected]
    bottom5 = countyslice.nlargest(n=15, keep='first')
    top5 = countyslice.nsmallest(n=15, keep='first')

    top5bottom5rank = pd.concat([top5, bottom5])  # Series of top5 and bottom 5, for the rank #
    top5bottom5neg = top5bottom5rank * (-1)  # Series of negative (for graphing)

    top5bottom5rank = top5bottom5rank.reset_index()  # prep for data frame
    top5bottom5neg = top5bottom5neg.reset_index()  # prep for data frame

    df_top5bottom5 = pd.merge(top5bottom5rank, top5bottom5neg, on='index')  # making data frame
    df_top5bottom5.columns = ['index', 'rank', 'rank_neg']  # rename

    df_top5bottom5['pillars'] = pd.Series()
    df_top5bottom5['zeros'] = 0.075

    for index, row in df_top5bottom5.iterrows():
        current_rank = df_top5bottom5.iloc[index]['rank']

        to_add = 0.2

        if index >= 0 and index <= 14:
            if index == 0:
                df_top5bottom5.loc[index, 'zeros'] = df_top5bottom5.loc[index, 'zeros']
            if index <= 14 and index >= 1:
                prev_rank = df_top5bottom5.iloc[index + -1]['rank']
                if current_rank == prev_rank:
                    df_top5bottom5.loc[index, 'zeros'] = df_top5bottom5.loc[index - 1, 'zeros'] + to_add
        else:
            if index == 15:
                df_top5bottom5.loc[index, 'zeros'] = df_top5bottom5.loc[index, 'zeros']
            if index <= 29 and index >= 16:
                prev_rank = df_top5bottom5.iloc[index + -1]['rank']
                if current_rank == prev_rank:
                    df_top5bottom5.loc[index, 'zeros'] = df_top5bottom5.loc[index - 1, 'zeros'] + to_add

    for index in df_top5bottom5['index']:
        if index in df_e_dict:
            df_top5bottom5.loc[df_top5bottom5['index'] == index, 'pillars'] = 'EA'
        elif index in df_hsc_dict:
            df_top5bottom5.loc[df_top5bottom5['index'] == index, 'pillars'] = 'HSC'
        else:
            df_top5bottom5.loc[df_top5bottom5['index'] == index, 'pillars'] = 'PbC'

    fig_county5 = px.scatter(df_top5bottom5, x='rank_neg', y='zeros', color='pillars',
                             color_discrete_map={
                                 "PbC": color_p,
                                 "HSC": color_hsc,
                                 "EA": color_e
                             },
                             category_orders={"pillars": ["PbC", "HSC", "EA"]},
                             # opacity=0.85,
                             hover_name='index',
                             hover_data={'rank_neg': False,  # remove from hover data
                                         'zeros': False,
                                         'pillars': False,  # add other column, default formatting
                                         'rank': True,  # add other column, customized formatting
                                         },
                             )
    fig_county5.update_traces(marker=dict(size=15,
                                          line=dict(width=1,
                                                    color='#1a1a1a')),
                              )
    fig_county5.update_xaxes(showgrid=False,
                             range=[-59, 0],
                             nticks=3,
                             # tick0=-58, dtick=29,
                             tickvals=[-58, -29, -1],
                             ticktext=['58', '29', '1'],
                             )

    fig_county5.update_yaxes(showgrid=False,
                             range=[-0.15, np.max(df_top5bottom5['zeros'] + .5)],
                             zeroline=True, zerolinecolor='black', zerolinewidth=3,
                             showticklabels=False,
                             )
    fig_county5.update_layout(
        title="iii. Topics Distribution by Score ranking",
        title_x=0.5,
        xaxis_title="Rank",
        yaxis_title="Frequency",
        legend_title="Pillar",
        #         legend = dict(
        #             orientation = "h",
        # #            yanchor = "bottom",
        # #            xanchor = "center",
        # #            xref = 'container'
        #         )
    )
    fig_county5.update_layout(height=400, plot_bgcolor=color_graphbg)
    fig_county5.layout.xaxis.fixedrange = True
    fig_county5.layout.yaxis.fixedrange = True

    return fig_county5



@callback(     # number of outputs must equal number of returns below
    Output(county_pillarsgraph, 'figure'),
    Output(county_flower, 'figure'),
    Output(county_top5bot5graph, 'figure'),
    Input(county_dropdown, 'value'),
)
def update_counties(county_selected):
# ***JFC*** - timing update_counties()
    tic = time.perf_counter()

    fig_countypillars = draw_countpillars(county_selected)
    fig_subjflower = draw_subjflower(county_selected)
    fig_county5 = draw_fig_county5(county_selected)

    toc = time.perf_counter()
    print(f"Time for update_counties() is {toc - tic:0.4f} secs")

    return fig_countypillars, fig_subjflower, fig_county5