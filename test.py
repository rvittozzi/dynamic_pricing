from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta  # for date manipulations

app = Flask(__name__)

# Your existing API details for properties
url_properties = "https://api.hostfully.com/v2/properties?agencyUid=d3dcb567-03dc-4c17-8918-e119b0bd579d&limit=20&offset=0"
url_pricing = "https://api.hostfully.com/v2/pricingPeriods?propertyUid={property_uid}"
headers = {
    "accept": "application/json",
    "X-HOSTFULLY-APIKEY": "tAryEQrD4HRUqAxF"
}


def fetch_base_rate(uid):
    # Make an API call to fetch pricing information for the property with UID=uid
    pricing_url = url_pricing.format(property_uid=uid)
    response = requests.get(pricing_url, headers=headers)
    pricing_data = json.loads(response.text)

    # Extract the base rate from the pricing_data (assuming the key is 'baseRate')
    # Here, we just take the first pricing period's base rate for demonstration.
    # You may need to adapt this logic as per your exact requirement.
    base_rate = pricing_data.get('pricingPeriods', [{}])[0].get('baseRate', 0)

    return base_rate


def update_pricing_period(uid, calculated_price, date_range, min_nights):
    # Simulated function to update the pricing period
    print(
        f"Updating pricing for UID {uid} with calculated price {calculated_price}, date range {date_range}, and minimum nights {min_nights}")


def dynamic_pricing(base_rate, is_weekend, days_until_booking, season):
    calculated_price = base_rate

    if is_weekend:
        calculated_price += (base_rate * 0.2)
    if days_until_booking <= 7:
        calculated_price -= (base_rate * 0.1)
    if days_until_booking >= 30:
        calculated_price -= (base_rate * 0.05)
    if season == 'summer':
        calculated_price += (base_rate * 0.15)
    elif season == 'winter':
        calculated_price -= (base_rate * 0.05)

    return calculated_price


@app.route('/')
def index():
    response = requests.get(url_properties, headers=headers)
    properties = json.loads(response.text)

    property_data = []
    for uid in properties['propertiesUids']:  # Assuming 'propertiesUids' contains list of UIDs as strings
        # Directly use uid because it's a string
        property_data.append({'uid': uid, 'name': ''})  # Assuming you will populate name later or it's not necessary

    return render_template('index.html', properties=property_data)


@app.route('/update_pricing', methods=['POST'])
def update_pricing():
    selected_uids = request.json.get('selected_uids', [])
    date_range = request.json.get('date_range', '')
    new_price = request.json.get('new_price', 0)
    min_nights = request.json.get('min_nights', 2)

    for uid in selected_uids:
        base_rate = fetch_base_rate(uid)

        is_weekend = False  # Replace with actual logic
        days_until_booking = 10  # Replace with actual logic
        season = 'summer'  # Replace with actual logic

        calculated_price = dynamic_pricing(base_rate, is_weekend, days_until_booking, season)
        update_pricing_period(uid, calculated_price, date_range, min_nights)

    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(debug=True)
