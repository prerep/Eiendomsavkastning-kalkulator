from flask import Flask, render_template, request, redirect
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Unngår GUI-feil på server
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Opprett database for lagring av beregninger
DB_FILE = "calculations.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS calculations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  purchase_price REAL, rent_income REAL, common_costs REAL, 
                  maintenance_costs REAL, other_costs REAL, equity REAL, 
                  tax_rate REAL, inflation_rate REAL, years INTEGER, 
                  gross_yield REAL, net_yield REAL, roi REAL, inflation_adjusted_roi REAL)''')
    conn.commit()
    conn.close()

init_db()

# Hjemmeside
@app.route("/")
def home():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM calculations ORDER BY id DESC LIMIT 5")  # Henter de siste 5 beregningene
    previous_calculations = c.fetchall()
    conn.close()
    return render_template("index.html", previous_calculations=previous_calculations)

# Beregn avkastning og lagre i database
@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        purchase_price = float(request.form["purchase_price"])
        rent_income = float(request.form["rent_income"]) * 12
        common_costs = float(request.form["common_costs"]) * 12
        maintenance_costs = float(request.form["maintenance_costs"]) * 12
        other_costs = float(request.form["other_costs"]) * 12
        equity = float(request.form["equity"])
        tax_rate = float(request.form["tax_rate"]) / 100 if request.form["tax_rate"] else 0
        inflation_rate = float(request.form["inflation_rate"]) / 100 if request.form["inflation_rate"] else 0
        years = int(request.form["years"]) if request.form["years"] else 0

        # Beregninger
        annual_expenses = common_costs + maintenance_costs + other_costs
        net_income = rent_income - annual_expenses

        gross_yield = (rent_income / purchase_price) * 100
        net_yield = (net_income / purchase_price) * 100
        roi = (net_income / equity) * 100

        # Skatt
        if "include_tax" in request.form:
            net_income = net_income * (1 - tax_rate)
            roi = (net_income / equity) * 100

        # Inflasjon
        inflation_adjusted_roi = roi
        if "include_inflation" in request.form:
            adjusted_price = purchase_price * ((1 + inflation_rate) ** years)
            inflation_adjusted_roi = (net_income / adjusted_price) * 100

        # Lagre beregningen i databasen
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO calculations 
                     (purchase_price, rent_income, common_costs, maintenance_costs, other_costs, equity, 
                      tax_rate, inflation_rate, years, gross_yield, net_yield, roi, inflation_adjusted_roi) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (purchase_price, rent_income, common_costs, maintenance_costs, other_costs, equity,
                   tax_rate, inflation_rate, years, gross_yield, net_yield, roi, inflation_adjusted_roi))
        conn.commit()
        conn.close()

        # Generer graf for ROI over tid
        graph_path = "static/roi_chart.png"
        years_list = list(range(1, years + 1))
        roi_list = [(roi * (1 + inflation_rate) ** year) for year in years_list]

        plt.figure(figsize=(6, 4))
        plt.plot(years_list, roi_list, marker='o', linestyle='-', color='b', label="ROI over tid")
        plt.xlabel("År")
        plt.ylabel("ROI (%)")
        plt.title("ROI Utvikling over Tid")
        plt.legend()
        plt.grid(True)
        plt.savefig(graph_path)
        plt.close()

        return render_template("index.html", gross_yield=round(gross_yield, 2),
                               net_yield=round(net_yield, 2),
                               roi=round(roi, 2),
                               inflation_adjusted_roi=round(inflation_adjusted_roi, 2),
                               graph_path=graph_path)

    except ValueError:
        return render_template("index.html", error="Vennligst fyll ut alle feltene med gyldige tall.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
