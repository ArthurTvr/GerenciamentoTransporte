from flask import Flask, jsonify
from flask_cors import CORS
from db import get_espera_collection

app = Flask(__name__)
CORS(app)  # Permite que o frontend do GitHub Pages acesse a API

espera_col = get_espera_collection()

@app.route("/api/espera")
def lista_espera():
    lista = list(espera_col.find({}, {"_id": 0}))  # remove o _id do Mongo
    return jsonify(lista)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
