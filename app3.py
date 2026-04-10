from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__, template_folder="templates3", static_folder="static3")

# SQLAlchemy konfiguracija
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///history3.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "skrivnostniKljucZa3Nalogo"

# Inicializacija baze
db = SQLAlchemy(app)


# =====================================================
# HELPER FUNKCIJE
# =====================================================

def get_client_ip():
    """Vrne IP naslov trenutnega uporabnika"""
    return request.remote_addr


# =====================================================
# ROUTE - dodaj nove route tukaj
# =====================================================


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True, port=5003)