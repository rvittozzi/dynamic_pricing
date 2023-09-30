from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# Your existing API details for properties
url_properties = "https://api.hostfully.com/v2/properties?agencyUid=d3dcb567-03dc-4c17-8918-e119b0bd579d&limit=20&offset=0"
url_pricing = "https://api.hostfully.com/v2/pricingPeriods?propertyUid={property_uid}"
headers = {
    "accept": "application/json",
    "X-HOSTFULLY-APIKEY": "tAryEQrD4HRUqAxF"
}


def fetch_property_names(uids):
    property_names = []

    for uid in uids:
        response = requests.get(f"https://api.hostfully.com/v2/properties/{uid}", headers=headers)
        property_data = json.loads(response.text)
        if 'name' in property_data:
            property_names.append(property_data['name'])
        else:
            property_names.append('Name not found')

    return property_names


def fetch_base_rate(uid):
    # Make an API call to fetch property information for the property with UID=uid
    property_url = f"https://api.hostfully.com/v2/properties/{uid}"
    response = requests.get(property_url, headers=headers)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        property_data = json.loads(response.text)

        # Extract the baseDailyRate from the property_data
        base_daily_rate = property_data.get('baseDailyRate', 0)

        return base_daily_rate
    else:
        print(f"Failed to fetch property information. Status code: {response.status_code}")
        return None  # Return None to indicate failure


def update_pricing_period(uid, calculated_price, date_range, min_nights):
    # Simulated function to update the pricing period
    print(
        f"Updating pricing for UID {uid} with calculated price {calculated_price}, date range {date_range}, and minimum nights {min_nights}")


def dynamic_pricing(base_rate, is_weekend, days_until_booking, season):
    calculated_price = base_rate

    return calculated_price


def fetch_pricing_rules(property_uid):
    # Make an API call to fetch pricing rules for the property with the given UID
    pricing_rules_url = f"https://api.hostfully.com/v2/pricingrules/{property_uid}"
    response = requests.get(pricing_rules_url, headers=headers)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        pricing_rules_data = json.loads(response.text)

        # Extract pricing rules from the response (assuming the key is 'pricingRules')
        pricing_rules = pricing_rules_data.get('pricingRules', [])

        return pricing_rules
    else:
        # Handle the case where the API request was not successful
        print(f"Failed to fetch pricing rules. Status code: {response.status_code}")
        return []  # Return an empty list to indicate no pricing rules available


@app.route('/')
def index():
    response = requests.get(url_properties, headers=headers)
    properties = json.loads(response.text)

    property_data = []
    if 'propertiesUids' in properties:
        uids = properties['propertiesUids']
        property_names = fetch_property_names(uids)

        for uid, name in zip(uids, property_names):
            property_data.append({'uid': uid, 'name': name})

    return render_template('index.html', properties=property_data)


@app.route('/update_pricing', methods=['GET'])
def update_pricing():
    selected_uids = request.json.get('selected_uids', [])
    date_range = request.json.get('date_range', '')
    min_nights = request.json.get('min_nights', 2)

    calculated_prices = []  # List to store all calculated prices

    for uid in selected_uids:
        base_rate = fetch_base_rate(uid)

        is_weekend = False  # Replace with actual logic
        days_until_booking = 10  # Replace with actual logic
        season = 'summer'  # Replace with actual logic

        calculated_price = dynamic_pricing(base_rate, is_weekend, days_until_booking, season)

        payload = {
            "propertyUid": uid,
            "from": "2023-09-30",
            "to": "2023-09-30",
            "amount": calculated_price,
            "minimumStay": "1",
            "isCheckinAllowed": "string",
            "isCheckoutAllowed": "string"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"Successfully updated pricing for {uid}")
        else:
            print(f"Failed to update pricing for {uid}. Response: {response.text}")

        calculated_prices.append({'uid': uid, 'amount': calculated_price})

        update_pricing_period(uid, calculated_price, date_range, min_nights)
        print(f"Final Calculated Price for UID {uid}: {calculated_price}")  # Printing the final price to the console

    return jsonify({"status": "success", "calculated_prices": calculated_prices})


@app.route('/show_price', methods=['POST'])
def show_price():
    property_uid = request.form.get('property_uid')
    base_rate = fetch_base_rate(property_uid)

    if base_rate is not None:
        return f"The base rate for selected property is: {base_rate}"
    else:
        return "Failed to fetch the base rate for the selected property."


if __name__ == '__main__':
    app.run(debug=True)
