from flask import Flask, request, jsonify, redirect
from string import Template
app = Flask(__name__)

with open('index.html', 'r') as f:
    html = f.read()


@app.route('/graph.json')
def data():
    return redirect(
        'https://gist.githubusercontent.com/mbostock/'
        '4062045/raw/5916d145c8c048a6e3086915a6be464467391c62/'
        'miserables.json'
    )


@app.route('/')
def index():
    return html

app.debug = True
app.run(port=8080)
