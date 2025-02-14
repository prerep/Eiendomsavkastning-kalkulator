from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        purchase_price = float(request.form["purchase_price"])
        rent_income = float(request.form["rent_income"]) * 12
        common_costs = float(request.form["common_costs"]) * 12
        maintenance_costs = float(request.form["maintenance_costs"]) * 12
        other_costs = float(request.form["other_costs"]) * 12
        equity = float(request.form["equity"])
        tax_rate = float(request.form["tax_rate"]) / 100
        inflation_rate = float(request.form["inflation_rate"]) / 100
        years = int(request.form["years"])

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

        return render_template("index.html", gross_yield=round(gross_yield, 2),
                               net_yield=round(net_yield, 2),
                               roi=round(roi, 2),
                               inflation_adjusted_roi=round(inflation_adjusted_roi, 2))

    except ValueError:
        return render_template("index.html", error="Vennligst fyll ut alle feltene med gyldige tall.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
