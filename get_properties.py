from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)


# Function to get all available property UIDs from API
def get_all_property_uids():
    url = "https://api.hostfully.com/v2/properties?agencyUid=d3dcb567-03dc-4c17-8918-e119b0bd579d&limit=20&offset=0"
    headers = {
        "accept": "application/json",
        "X-HOSTFULLY-APIKEY": "tAryEQrD4HRUqAxF"
    }
    response = requests.get(url, headers=headers)
    try:
        properties = json.loads(response.text)
        if isinstance(properties, list):
            return [property['uid'] for property in properties]
        elif isinstance(properties, dict) and 'properties' in properties:
            return [property['uid'] for property in properties['properties']]
        else:
            return []
    except json.JSONDecodeError:
        print("Error decoding JSON")
        return []


# Function to get property details based on its UID
def get_property_details(uid):
    url = f"https://api.hostfully.com/v2/properties/{uid}"  # Change "uid" to {uid}
    headers = {
        "accept": "application/json",
        "X-HOSTFULLY-APIKEY": "tAryEQrD4HRUqAxF"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        property_details = json.loads(response.text)
        base_rate = property_details.get('baseRate', 0)  # Replace with the actual field for base rate
        return base_rate
    else:
        print(f"Failed to get property details: {response.status_code}, {response.text}")
        return None


# Function to calculate dynamic pricing
def dynamic_pricing(base_rate, check_in_date, check_out_date):
    check_in_date = datetime.strptime(check_in_date, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out_date, "%Y-%m-%d")
    total_days = (check_out_date - check_in_date).days
    dynamic_rate = base_rate

    for single_date in (check_in_date + timedelta(n) for n in range(total_days)):
        if single_date.weekday() >= 5:
            dynamic_rate += 20  # Add $20 for weekends

    days_until_checkin = (check_in_date - datetime.now()).days
    if days_until_checkin <= 7:
        dynamic_rate -= 15  # Subtract $15 for last-minute bookings

    if days_until_checkin >= 30:
        dynamic_rate -= 10  # Subtract $10 for early bird bookings

    if check_in_date.month in [6, 7, 8]:
        dynamic_rate += 25  # Add $25 for summer bookings

    return dynamic_rate * total_days


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_property_uids", methods=["GET"])
def get_uids():
    try:
        uids = get_all_property_uids()  # This calls the updated function
        if uids:
            return jsonify({"uids": uids})
        else:
            return jsonify({"error": "No UIDs found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/calculate_price", methods=["POST"])
def calculate_price():
    try:
        data = request.json
        uid = data['propertyUid']
        check_in = data['checkIn']
        check_out = data['checkOut']

        base_rate = get_property_details(uid)
        if base_rate is None:
            return jsonify({"error": "Could not get base rate"}), 404

        final_price = dynamic_pricing(base_rate, check_in, check_out)

        return jsonify({"final_price": final_price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
