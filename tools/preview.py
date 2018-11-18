from flask import Flask, request, jsonify, redirect
from tools.generate_parser import graph
from string import Template
app = Flask(__name__)

with open('index.html', 'r') as f:
    html = f.read()


@app.route('/graph.json')
def data():
    return jsonify(**graph)


@app.route('/')
def index():
    return html


app.debug = True
app.run(port=8080)
