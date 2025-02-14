from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Hjemmeside
@app.route("/")
def home():
    return render_template("index.html")

# Beregn avkastning
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

        return render_template("index.html",
                               gross_yield=round(gross_yield, 2),
                               net_yield=round(net_yield, 2),
                               roi=round(roi, 2),
                               inflation_adjusted_roi=round(inflation_adjusted_roi, 2))

    except ValueError:
        return render_template("index.html", error="Vennligst fyll ut alle feltene med gyldige tall.")

# Hent data fra FINN.no
@app.route("/fetch_finn", methods=["POST"])
def fetch_finn():
    try:
        finn_url = request.form["finn_url"]
        headers = {"User-Agent": "Mozilla/5.0"}

        # Hent nettsiden
        response = requests.get(finn_url, headers=headers)
        if response.status_code != 200:
            return render_template("index.html", error="Kunne ikke hente data fra FINN.")

        soup = BeautifulSoup(response.text, "html.parser")

        # 🔹 Finn kjøpspris
        price_text = soup.find(string=re.compile(r"\d+\s*\d+ kr"))  # Søker etter "kr"
        price = int(re.sub(r"\D", "", price_text)) if price_text else ""

        # 🔹 Finn felleskostnader (søker i flere HTML-strukturer)
        common_costs = ""
        possible_labels = ["Felleskostnader", "Fellesutgifter", "Månedlige felleskostnader"]
        for label in soup.find_all(["dt", "span", "strong"]):
            text = label.get_text().strip()
            if any(term in text for term in possible_labels):
                value = label.find_next("dd") or label.find_next("span")
                if value:
                    common_costs = int(re.sub(r"\D", "", value.get_text()))
                break

        # 🔹 Beregn EK = 10% av kjøpsprisen
        fetched_equity = int(price * 0.10) if price else ""

        return render_template("index.html",
                               fetched_price=price,
                               fetched_common_costs=common_costs,
                               fetched_equity=fetched_equity)

    except Exception as e:
        return render_template("index.html", error=f"Feil ved henting: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
