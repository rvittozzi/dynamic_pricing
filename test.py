from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import math

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


def fetch_price_for_date(uid, date):
    # Assume API_URL is where you fetch the price for a specific date
    url = f"https://api.hostfully.com/v2/pricingForDate?propertyUid={uid}&date={date}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get('amount', 0)  # Changed 'price' to 'amount'
    else:
        return 0  # Return 0 if the API call fails


def update_pricing_period(uid, calculated_price, date_range, min_nights):
    # Simulated function to update the pricing period
    print(
        f"Updating pricing for UID {uid} with calculated price {calculated_price}, date range {date_range}, and minimum nights {min_nights}")


def dynamic_pricing(base_rate, pricing_rules, stay_date, num_nights):
    # Starting with the base_rate
    calculated_price = base_rate

    for rule in pricing_rules:
        price_rule_type = rule.get('priceRuleType')
        threshold = rule.get('threshold')
        price_change_type = rule.get('priceChangeType')
        price_change = rule.get('priceChange')

        # Increase the price by 20% when a stay is shorter than 2 days
        if price_rule_type == "STAY_IS_SHORTER_THAN_X_DAYS" and num_nights < threshold:
            if price_change_type == "PERCENT":
                calculated_price *= (1 + price_change / 100)

        # Reduce the price by 5% when a stay is longer than 7 days
        # Reduce the price by 10% when a stay is longer than 14 days
        if price_rule_type == "STAY_IS_LONGER_THAN_X_DAYS" and num_nights > threshold:
            if price_change_type == "PERCENT":
                calculated_price *= (1 - price_change / 100)

    return calculated_price


def fetch_pricing_rules(uid):
    url = f"https://api.hostfully.com/v2/pricingrules/{uid}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get('pricingRules', [])  # changed 'rules' to 'pricingRules'
    else:
        print(f"Failed to fetch pricing rules. Status code: {response.status_code}")
        return []


def fetch_pricing_rules_keys(uid):
    url = f"https://api.hostfully.com/v2/pricingrules/{uid}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)

        print("Root-level keys:")
        for key in data.keys():
            print(key)

        print("\nKeys within each rule:")
        if 'pricingRules' in data:  # changed 'rules' to 'pricingRules'
            if data['pricingRules']:
                for key in data['pricingRules'][0].keys():
                    print(key)
    else:
        print(f"Failed to fetch pricing rules. Status code: {response.status_code}")


def apply_weekend_rate(daily_rate, day, weekend_increase_percent, min_weekend_nights):
    if day.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        if min_weekend_nights <= 1:  # If it's not mandatory to stay for more than one night during weekends
            return daily_rate * (1 + weekend_increase_percent / 100)
    return daily_rate


def apply_last_minute_discount(daily_rate, day, today, discount_days, discount_percents):
    for days, percent in zip(discount_days, discount_percents):
        if today + timedelta(days=days) >= day:
            return daily_rate * (1 - percent / 100)
    return daily_rate


def apply_seasonal_rate(daily_rate, day, seasonal_rates):
    for season in seasonal_rates:
        start, end, percent, min_nights = season['start'], season['end'], season['percent'], season['min_nights']
        if start <= day <= end:
            if min_nights <= 1:  # If there is no minimum night requirement for the season
                return daily_rate * (1 + percent / 100)
    return daily_rate


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


@app.route('/show_price', methods=['POST'])
def show_price():
    property_uid = request.form.get('property_uid')
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    minimum_stay = max(int(request.form.get('minimum_stay', 2)), 2)

    # Debugging: Fetch and print keys from the pricing rules API
    print("Debugging: Fetching pricing rule keys...")
    fetch_pricing_rules_keys(property_uid)

    # Fetch the pricing rules for this property
    pricing_rules = fetch_pricing_rules(property_uid)

    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
    num_nights = (to_date_obj - from_date_obj).days

    if num_nights < minimum_stay:
        return "The number of nights should be at least the minimum stay."

    total_price = 0

    for i in range(num_nights):
        day = from_date_obj + timedelta(days=i)

        # Ensure daily_rate is defined before passing it to dynamic_pricing
        daily_rate = fetch_price_for_date(property_uid, day.strftime('%Y-%m-%d'))
        if daily_rate == 0:
            base_rate = fetch_base_rate(property_uid)
            if base_rate is None:
                return "Failed to fetch base rate for the property."
            daily_rate = base_rate
        # Now daily_rate is guaranteed to have a value
        daily_rate = dynamic_pricing(daily_rate, pricing_rules, day, num_nights)
        # Apply dynamic pricing logic
        daily_rate = dynamic_pricing(daily_rate, pricing_rules, day, num_nights)

        # Apply weekend rate
        daily_rate = apply_weekend_rate(daily_rate, day, weekend_increase_percent=20, min_weekend_nights=2)

        # Apply last-minute discount
        today = datetime.now()
        daily_rate = apply_last_minute_discount(daily_rate, day, today, [1, 3, 5], [30, 20, 10])

        # Apply seasonal rate
        seasonal_rates = [
            {'start': datetime(today.year, 12, 31), 'end': datetime(today.year, 1, 2), 'percent': 20, 'min_nights': 2}
        ]
        daily_rate = apply_seasonal_rate(daily_rate, day, seasonal_rates)

        total_price += daily_rate

        total_price = math.ceil(total_price)

    return f"The total price for the property from {from_date} to {to_date} is: {total_price}"


if __name__ == '__main__':
    app.run(debug=True)
