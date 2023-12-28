import dash
from dash import html, dcc, Dash, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import pathlib

#important code: source /Users/ali/Dropbox/Dashboard/Python_normAggregation/venv-3.11/bin/activate
location = pathlib.Path(__file__).parent

app = Dash(__name__, use_pages = True, external_stylesheets=[dbc.themes.LUX])
server = app.server

#elements
NED_logo = f'{location}/assets/Oikos2.png'
NED_logo_base64 = base64.b64encode(open(NED_logo, 'rb').read()).decode('ascii')

linksbar = dbc.Row(
    [
        dbc.Col(dbc.NavItem(dbc.NavLink("About the author", href="https://alessandroconway.netlify.app",
                        external_link='True', target='_blank', style={"color":"#a3a6a8"})), width = 'auto'),
        dbc.Col(dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("NED Tool", href='/'),
                dbc.DropdownMenuItem("About this tool", href='/about'), #external_link='True', target="_blank"),
                dbc.DropdownMenuItem("Methodology", href='/methodology'),
            ],
            nav=True,
            in_navbar=True,
            label="Menu",
            toggle_style={"color": "#a3a6a8"},
        )),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src='data:image/png;base64,{}'.format(NED_logo_base64), height="30px")),
                        dbc.Col(dbc.NavbarBrand("OIKOS – New Economic Development", class_name="ms-2", style = {"color":"#fafafa"}), width='auto'),
                    ],
                    align="center",
                    class_name="g-0",
                ),
                href='/',
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                linksbar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    fixed = 'top',
    color="dark",
    dark=True,
)
footerbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavItem(dbc.NavLink("Copyright © 2023 Alessandro Conway. All rights reserved.", disabled=True)),
            dbc.NavItem(dbc.NavLink("Return to top", href="#")),
        ]
    ),
    color = "tertiary",
    #dark = True
)


app.layout = dbc.Container(
    [
        navbar,
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),

        dash.page_container,

        html.Br(),
        footerbar,
    ],
    fluid=False,
    className="dbc"
)

# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

#Run the app
if __name__ == '__main__':
#   app.run_server(debug=False)
   app.run(debug=False, host='127.0.0.1', port=8061)
