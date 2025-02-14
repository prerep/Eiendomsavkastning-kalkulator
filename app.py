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

        # Finn kjøpspris
        price_text = soup.find(string=re.compile(r"\d+\s*\d+ kr"))
        price = int(re.sub(r"\D", "", price_text)) if price_text else ""

        # Finn felleskostnader
        common_costs = ""
        possible_labels = ["Felleskostnader", "Fellesutgifter", "Månedlige felleskostnader", "Felleskost/mnd."]
        for label in soup.find_all(["dt", "span", "strong"]):
            text = label.get_text().strip()
            if any(term in text for term in possible_labels):
                value = label.find_next("dd") or label.find_next("span")
                if value:
                    common_costs = int(re.sub(r"\D", "", value.get_text()))
                break

        # Beregn EK = 10% av kjøpsprisen
        fetched_equity = int(price * 0.10) if price else ""

        return render_template("index.html",
                               fetched_price=price,
                               fetched_common_costs=common_costs,
                               fetched_equity=fetched_equity)

    except Exception as e:
        return render_template("index.html", error=f"Feil ved henting: {str(e)}")
