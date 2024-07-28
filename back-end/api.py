from distutils.log import debug
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import csv

app = Flask(__name__)
CORS(app, support_credentials=True)


@cross_origin(supports_credentials=True)
@app.get("/theatres")
def get():
    try:
        with open("output.csv", "r") as f:
            csv_reader = csv.DictReader(f)
            print(csv_reader)
            return jsonify([dict(theatre) for theatre in csv_reader]), 200
    except FileNotFoundError as f:
        return "Missing file", 410


app.run(debug=True, host="0.0.0.0")
