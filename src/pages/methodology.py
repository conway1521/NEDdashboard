import dash
import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template("lux")
import plotly.express as px
import pathlib

location = pathlib.Path(__file__).parent.parent


#-----------------------------------------------------------------------------------------------------------------------
# Registering page

dash.register_page(
    __name__,
    path='/methodology',
    title='Methodology',
    name='Methodology'
)
#-----------------------------------------------------------------------------------------------------------------------
 #Data of webpage


color_graphbg = '#fafbfb' #'rgba(247,247,249,255)' #grey of dropdown men, 'rgba(179, 205, 227, 0.15)' light blue
#dbc LUX colors
color_NED = "#d8534f"
color_p = "#4abf73"
color_hsc = "#f0ad4e"
color_e = "#209bcf"


#-----------------------------------------------------------------------------------------------------------------------
# Build components






#-----------------------------------------------------------------------------------------------------------------------
# LAYOUT OF THE WEBPAGE
layout= dbc.Container(
    [
        html.H3("General methodology"),
        dcc.Markdown('''
            The New Economic Development (NED) Index provides a barometer of three key Pillars of equitable local and regional economic development: Place-based Conditions, Human Capital, and Economic Activity. Through this lens, economic development is represented not as a singular value but rather as three mutually inclusive dimensions.
        '''),
        dcc.Markdown('''
            NED includes 83 variables spanning the breadth of the factors of inclusive sustainable local economic growth and wellbeing derived from economic and social science research along with field-generated learning. These are then aggregated by relatedness into 30 Subjects, themselves forming 9 Topics.
        '''),
        html.Br(),
        html.H4("Data"),
        dcc.Markdown('''
            The main data sources are the US Census Bureau data (namely the American Community Survey 5-year Estimates, Quarterly Workforce Indicators, Prosperity Now Scorecard, US Bureau of Economic Analysis, Federal Financial Institutions Examination Council, US Patent and Trademark Office, California County Health Records, Homeless Data Integration System (HDIS), National Eviction Lab, California Department of Education, Measure for America, and Opportunity Insights. 
            
            2018 data was used for two reasons: firstly, I wanted to use a full-year of widely available indicators pre-pandemic. This year worked particularly because I wanted to include the significant dataset that [Chetty *et al*, 2022](https://socialcapital.org) recently published. Having the Social Cohesion information adds a significant dimension to the interconnectedness of households in the economic development ecosystem.
        ''', link_target="_blank"),
        dcc.Markdown('''
            The methodology of aggregating variables into Subjects, Topics, and Pillars is similar to that used by the OECD in their [Better Life Index](https://www.oecdbetterlifeindex.org) and the original [Human Development Index (HDI)](https://hdr.undp.org/system/files/documents/technical-notes-calculating-human-development-indices.pdf). Whereas the current HDI methodology involves geometric mean averaging, it also brings up significant issues (for well-explained discussions, see Martin Ravallion's [2010 paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1713611) or Sudhir Anand's [2018 paper](https://hdr.undp.org/content/recasting-human-development-measures)). In essence, keeping a simple arithmetic mean method allows for equal weighting to be assigned to each category without assigning any substitutative value for increases or decreases, which the geometric mean implies. 
        '''),
        html.Br(),
        html.H4("Inequality-adjustment"),
        dcc.Markdown('''
            Current HDI work has however introduced an interesting metric, the Inequality-adjusted HDI or IHDI, which adds a distritbuional dimension to the average attainments of each indicator. By calculating an Atkinson measure of inequality for each indicator and subsequently using it to weigh the HDI indicators, the spread of outcomes within indicators is taken into account. In other words, while the HDI provides a mean, it ignores the distribution of outcomes across the population it represents. IHDI captures the inequality within each component of human development. However, in order to do so, data *at least* one level of granularity below the given component's is required (*i.e.*, a state's IHDI score requires county-level data, or a county's needs census tract data). Due to the lack of more granularity in the NED Dataset, calculating the Atkinson measure of inequality was not possible.
            
            Nevertheless, a simpler way is devised for adding inequity to the NED dashboard: differences in demographic and other characteristics weigh the calculation of the Subjects. For example, the Employment Subject combines *Employment-to-population*, *College attainment employment-to-population gap*, and *16-29 years vs. 30-64 years employment-to-population gap* variables; the Earnings Subject weighs *Average earnings* with *Black-White average earning gap*, *Male-female earning gap*, and *Black-White earning gap from stable jobs*; or Homeownership is weighted by *Black-White homeownership gap* and *High-school attainment homeownership gap*. The NED dashboard's aggregate descriptors of development are thus nuanced by some of the distributional outcomes that exist within its indicators. And again, by using a simple arithmetic average no assumptions are made about the significance of this ponderance. This inequality-adjustment process is preliminary, and deepening it could be the subject of future work. 
        '''),
        dcc.Markdown('''
            Inequality-adjusting does have some important considerations to keep in mind.
            
            By being based on the Atkinson measure of Inequality, IHDI satisfies 'subgroup consistency'. This property ensures that improvements (deteriorations) in the distribution of human development within only a certain group of the society imply improvements (deteriorations) in the distribution across the entire society. While not intended yet to carry the same standardisation weight, the inequality-adjustment of the NED Dashboard cannot claim the same.  
            One of the main drawbacks of inequality-adjustment like the IHDI is that it is not 'association sensitive', which means that it cannot capture any overlapping inequalities. To rectify this, a full dataset from the same sources is required, which is not the case with the current NED Dashboard (or the IHDI), but in this work's case may become possible with more refinement. 
        '''

        )

    ], fluid = False, className="dbc"
)