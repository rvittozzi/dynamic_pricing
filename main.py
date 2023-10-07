import json
from datetime import datetime, timedelta

import requests
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

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
    property_url = f"https://api.hostfully.com/v2/properties/{uid}"
    response = requests.get(property_url, headers=headers)

    if response.status_code == 200:
        property_data = json.loads(response.text)

        base_daily_rate = property_data.get('baseDailyRate', 0)

        return base_daily_rate
    else:
        print(f"Failed to fetch property information. Status code: {response.status_code}")
        return None


def fetch_price_for_date(uid, date):
    url = f"https://api.hostfully.com/v2/pricingForDate?propertyUid={uid}&date={date}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get('amount', 0)
    else:
        return 0


def update_pricing_period(uid, calculated_price, from_date, to_date, min_nights):
    update_url = f"https://api.hostfully.com/v2/pricingperiods/"

    payload = {
        "uid": uid,
        "from": from_date,
        "to": to_date,
        "amount": calculated_price,
        "minimumStay": min_nights
    }

    response = requests.post(update_url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Successfully updated pricing for property UID {uid}.")
    else:
        print(
            f"Failed to update pricing for property UID {uid}. Status code: {response.status_code}, Response: {response.text}")


def dynamic_pricing(base_rate, pricing_rules, stay_date, num_nights):
    calculated_price = base_rate

    for rule in pricing_rules:
        price_rule_type = rule.get('priceRuleType')
        threshold = rule.get('threshold')
        price_change_type = rule.get('priceChangeType')
        price_change = rule.get('priceChange')

        if price_rule_type == "STAY_IS_SHORTER_THAN_X_DAYS" and num_nights < threshold:
            if price_change_type == "PERCENT":
                calculated_price *= (1 + price_change / 100)

        if price_rule_type == "STAY_IS_LONGER_THAN_X_DAYS" and num_nights > threshold:
            if price_change_type == "PERCENT":
                calculated_price *= (1 - price_change / 100)

    return calculated_price


def fetch_pricing_rules(uid):
    url = f"https://api.hostfully.com/v2/pricingrules/{uid}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get('pricingRules', [])
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
        if 'pricingRules' in data:
            if data['pricingRules']:
                for key in data['pricingRules'][0].keys():
                    print(key)
    else:
        print(f"Failed to fetch pricing rules. Status code: {response.status_code}")


def apply_weekend_rate(daily_rate, day, weekend_increase_percent, min_weekend_nights):
    if day.weekday() >= 5:
        if min_weekend_nights <= 1:
            return daily_rate * (1 + weekend_increase_percent / 100)
    return daily_rate


def apply_last_minute_discount(daily_rate, day, today, discount_days, discount_percents):
    # Convert day to a date object
    if isinstance(day, datetime):
        day = day.date()

    for days, percent in zip(discount_days, discount_percents):
        if today + timedelta(days=days) >= day:
            return daily_rate * (1 - percent / 100)
    return daily_rate


def apply_seasonal_rate(daily_rate, day, seasonal_rates):
    for season in seasonal_rates:
        start, end, percent, min_nights = season['start'], season['end'], season['percent'], season['min_nights']
        if start <= day <= end:
            if min_nights <= 1:
                return daily_rate * (1 + percent / 100)
    return daily_rate


def apply_gap_pricing(daily_rate, day, gap_sizes, gap_discounts):
    detected_gap = 3

    for size, percent in zip(gap_sizes, gap_discounts):
        if detected_gap == size:
            return daily_rate * (1 - percent / 100)
    return daily_rate


def update_pricing_periods_bulk(pricing_periods):
    update_url = "https://api.hostfully.com/v2/pricingperiodsbulk/"

    response = requests.post(update_url, headers=headers, json={"pricingperiods": pricing_periods})

    if response.status_code == 200:
        print("Successfully updated pricing in bulk.")
    else:
        print(
            f"Failed to update pricing in bulk. Status code: {response.status_code}, Response: {response.text}")


def update_all_properties_for_next_month():
    pricing_periods_to_update = []

    today = datetime.today()
    one_month_later = today + timedelta(days=30)

    response = requests.get(url_properties, headers=headers)
    properties = json.loads(response.text)

    if 'propertiesUids' not in properties:
        print('No property UIDs found.')
        return

    uids = properties['propertiesUids']

    for uid in uids:
        base_rate = fetch_base_rate(uid)
        pricing_rules = fetch_pricing_rules(uid)
        min_nights = 1

        for n in range(1, 31):
            start_date = today + timedelta(days=n)
            end_date = start_date + timedelta(days=1)
            num_nights = (one_month_later - start_date).days

            daily_rate = fetch_price_for_date(uid, start_date.strftime('%Y-%m-%d'))
            if daily_rate == 0:
                daily_rate = base_rate

            daily_rate = dynamic_pricing(daily_rate, pricing_rules, start_date, num_nights)

            # Add to the list of pricing_periods_to_update
            pricing_periods_to_update.append({
                "uid": uid,
                "from": start_date.strftime('%Y-%m-%d'),
                "to": end_date.strftime('%Y-%m-%d'),
                "amount": daily_rate,
                "minimumStay": min_nights
            })

    # Update all properties pricing in bulk
    update_pricing_periods_bulk(pricing_periods_to_update)


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


@app.route('/update_selected_properties', methods=['POST'])
def update_selected_properties():
    global selected_properties
    selected_properties = request.form.getlist('selected_properties')
    return redirect('/')


@app.route('/show_price', methods=['POST'])
def show_price():
    # Existing fields
    property_uid = request.form['property_uid']
    from_date = datetime.strptime(request.form['from_date'], "%Y-%m-%d")
    to_date = datetime.strptime(request.form['to_date'], "%Y-%m-%d")
    minimum_stay = int(request.form['minimum_stay'])
    min_weekend_nights = int(request.form.get('min_weekend_nights', 1))  # default to 1 if not provided

    weekend_increase_percent = float(request.form.get('weekend_increase_percent', 0))
    last_minute_days_str = request.form.get('last_minute_days', '')
    last_minute_discounts_str = request.form.get('last_minute_discounts', '')

    # New: Get seasonal_rates from user input
    seasonal_rates_str = request.form.get('seasonal_rates', '[]')
    seasonal_rates = json.loads(seasonal_rates_str)  # parse the JSON string to Python list

    last_minute_days = list(map(int, last_minute_days_str.split(','))) if last_minute_days_str else []
    last_minute_discounts = [float(x) / 100 for x in
                             last_minute_discounts_str.split(',')] if last_minute_discounts_str else []

    # New: Get gap_discounts from user input
    gap_discounts_str = request.form.get('gap_discounts', '[]')  # Assuming you want to provide a default of empty list
    gap_discounts = json.loads(gap_discounts_str)  # Parse the JSON string to a Python list

    daily_rates = []
    today = datetime.now().date()
    delta = to_date - from_date
    for i in range(delta.days + 1):
        day = from_date + timedelta(days=i)
        daily_rate = fetch_base_rate(property_uid)
        daily_rate = apply_weekend_rate(daily_rate, day, weekend_increase_percent, min_weekend_nights)
        daily_rate = apply_last_minute_discount(daily_rate, day, today, last_minute_days, last_minute_discounts)
        daily_rate = apply_seasonal_rate(daily_rate, day, seasonal_rates)

        # Assume gap_days is a list containing the gap days. Replace this with your actual data.
        gap_days = []
        daily_rate = apply_gap_pricing(daily_rate, day, gap_days, gap_discounts)  # Pass gap_discounts here

        daily_rates.append({"day": day.strftime("%Y-%m-%d"), "rate": daily_rate})

    return json.dumps(daily_rates), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    app.run(debug=True)
