#========================================PACKAGES

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template("lux")
import pathlib
#========================================


location = pathlib.Path(__file__).parent.parent

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

# data
df_treemap = pd.read_csv(f'{location}/assets/df_treemap.csv')
df_treemap = df_treemap.drop('Unnamed: 0', axis=1)
colorscale_phsce = [color_e,color_p,color_hsc]

#  text
ned_text1 = '''
The NED approach is informed by two main sources:

1. Recent research shows the determinant role of social networks, geography, education, and wealth (among others) for 
enabling local economic development.

2. Community-based organizations, workforce boards, and community colleges elevate the complementary and equally 
fundamental role of access, basic needs, and community engagement, particularly for inclusion.

By combining frontier interdisciplinary research with key field-derived learning, three distinct Pillars emerged as 
comprising the drivers of inclusive local economic development. *Hover over the Pillars below to see what each 
entails.*
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

ned_text3 = '''
In NED, the three Pillars are not mutually exclusive.
High Economic Activity scores do not make up for low Place-based Conditions and/or Human and Social Capital scores (which might imply exogenous economic growth and lacking endogenous assets and ecosystem, and thus inequal opportunity).
As such, NED is a *barometer* of the three Pillars where some degree of equilibrium leads to inclusive, sustainable prosperity.
Economic development strategies can thus be tailored by vieweing the three Pillars together.
'''

ned_text4 = '''
The general categories that cover inclusive economic prosperity and well-being follow: 

* **Basic Needs** – to assess environmental, physical, and food health, security, housing, and transport.

* **Access** – to assess access to financial institutions and insurance, and broadband.

* **Education and Talent** – to assess educational attainment, schooling outcomes, and opportunity youth.

* **Social Capital** – to access social networks and cohesion.

* **Growth and Prosperity** – to assess the size and standard of living of local economies, alongside productivity.

* **Labor Market** – to assess jobs, employment, participation, and earnings.

* **Household Income** – to assess household budgets, poverty, financial assistance, and income inequality.

* **Household Wealth** – to assess home and asset ownership, banking availability, and financial resilience.

* **Business Environment** – to assess entrepreneurial outcomes and opportunities.

These form the cornerstone of the NED approach and were accumulated largely from local and regional economic development research (spanning urban and economic geography papers, macroeconomics, and labor economics) along with social capital research and social psychology. At the same time, field-derived learning about local economic development best practices, needs being elevated, community engagement, best practices for elevating  voices, 
They defined the range of what a quality life was, one with equitable opportunity for prosperity, for well-being, and also consdierate of local characteristics. Ultimately they makes up the Subjects (*ii.*) that we will see below.
'''

futurework_text1 = '''
As this work develops, the aim remains to provide local and regional policymakers with a means to make evidence-based decisions about inclusive local economic development.

There are three main avenues of work that the NED tool opens up:

1. Academic research to understand the determinants of inclusive local and regional economic development.
2. Applying the NED tool to a variety of other studies to provide the ecosystem context and impact following specific decisions.
3. Informing social investors and entrepreneurs about the places most in need of, or most poised to benefit from funds, and why.
'''


#-----------------------------------------------------------------------------------------------------------------------
# Build components
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
pillarcirclesfig.update_layout(height=315, plot_bgcolor='white', font=dict(size=17))


pillar_circles = dcc.Graph(figure=pillarcirclesfig,config={'displayModeBar': False})



treemap = px.treemap(df_treemap, path=[px.Constant("NED"), 'pillar', 'topic', 'subject'], values=None,
                     color_discrete_sequence= colorscale_phsce)
treemap.update_traces(root_color='lightgrey')
treemap.update_layout(margin = dict(t=50, l=25, r=25, b=25))
treemap.update_traces(hovertemplate = None, hoverinfo = "skip")

treemap_graph = dcc.Graph(figure=treemap,config={'displayModeBar': False})
#-----------------------------------------------------------------------------------------------------------------------
# Registering page
dash.register_page(
    __name__,
    path='/about',
    title='About this tool',
    name='About tool'
)
#-----------------------------------------------------------------------------------------------------------------------


layout = dbc.Container([
    html.H3('The NED approach', style={'fontsize': '24px', 'text-align': 'left', 'color': 'rgb(52,60,68)'}),
    dcc.Markdown(ned_text1),
    dbc.Row(
        [
            dbc.Col([pillar_circles], width = {"size": 12})
        ]
    ),
    dbc.Row(
        [
            dbc.Col(dcc.Markdown(ned_text2place), width = {"size": 4}),
            dbc.Col(dcc.Markdown(ned_text2humancap), width = {"size": 4}),
            dbc.Col(dcc.Markdown(ned_text2econact), width = {"size": 4}),
        ]
    ),
    html.Br(),
    dcc.Markdown(ned_text3),
    dcc.Markdown(ned_text4),
    html.Br(),
#------------
    html.H3('NED Hierarchy', style={'fontsize': '24px', 'text-align': 'left', 'color': 'rgb(52,60,68)'}),
    dcc.Markdown('''The NED tool is made up as follows:'''),
    dcc.Markdown('''
                    $$
                    NED \impliedby i.~Pillars \impliedby ii.~Subjects \impliedby iii.~Topics
                    $$''', mathjax=True, style={"font-size": "17pt"}),
    html.Br(),
    dcc.Markdown('''
    See below a Treemap displaying the data comprising the hierarchy of Pillars (*i.*), Subjects (*ii.*), and Topics (*iii.*) within the overall NED framework. Click into the modules to zoom in, and use the bar at the top to zoom out.
    '''),
    dbc.Row([
        dbc.Col([treemap_graph], width=12)
    ]),
    dcc.Markdown('''
        *Visit the [Methodology](/methodology) page for more information about the data and approach. And, see the [NED tool](/) in action!*'''),
    html.Br(),
#------------
    html.H3('Aim and Future Developments', style={'fontsize': '24px', 'text-align': 'left', 'color': 'DarkSlateGrey'}),
    html.Br(),
    dbc.Row([
        dcc.Markdown(children=futurework_text1)
    ]),
    html.Br(),
    dbc.Row([
        dcc.Markdown('''##### Please feel free to reach out concerning collaborations or discussing this work!''')
    ])
#------------
#    footerbar
], fluid=False, className="dbc")
#------------