from flask import Flask, render_template, request, Response, redirect, url_for, send_file
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import io
from sqlalchemy import create_engine
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote as url_quote  # Importing quote from urllib.parse

# Database connection
engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                       .format(user="root", pw="ariz786", db="ds"))

app = Flask(__name__)

# Routes

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/success', methods=["GET", "POST"])
def success():
    if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)
        connecting_routes = pd.read_csv("connecting_routes.csv")
        connecting_routes = connecting_routes.iloc[0:50, 1:8]

        for_g = nx.Graph()
        for_g = nx.from_pandas_edgelist(connecting_routes, source='source airport', target='destination airport')
        data = pd.DataFrame({
            "closeness": pd.Series(nx.closeness_centrality(for_g)),
            "Degree": pd.Series(nx.degree_centrality(for_g)),
            "eigenvector": pd.Series(nx.eigenvector_centrality(for_g)),
            "betweenness": pd.Series(nx.betweenness_centrality(for_g))
        })

        # Transfer file to database using 'to_sql' method
        data.to_sql('centralities', con=engine, if_exists='replace', chunksize=1000, index=False)
        html_table = data.to_html(classes='table table-striped')

        return render_template("data.html", frame=f"""
            <style>
                .table {{
                    width: 50%;
                    margin: 0 auto;
                    border-collapse: collapse;
                }}
                .table thead {{
                    background-color: #3ee6ca;
                }}
                .table th, .table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }}
                .table td {{
                    background-color: #ed2bc6;
                }}
                .table tbody th {{
                    background-color: #ab2c3f;
                }}
            </style>
            {html_table}
        """)

@app.route('/plots')
def plots():
    return render_template('plot.html')

@app.route('/graph')
def graph():
    connecting_routes = pd.read_csv("connecting_routes.csv")
    connecting_routes = connecting_routes.iloc[0:50, 1:8]

    for_g = nx.Graph()
    for_g = nx.from_pandas_edgelist(connecting_routes, source='source airport', target='destination airport')

    # Graph visualization
    fig = Figure()
    pos = nx.spring_layout(for_g, k=0.015)
    nx.draw_networkx(for_g, pos, ax=fig.add_subplot(111), node_size=15, node_color='blue')
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

