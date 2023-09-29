import requests

# Initialize API key and endpoint
api_key = "tAryEQrD4HRUqAxF"
agency_id = "d3dcb567-03dc-4c17-8918-e119b0bd579d"
endpoint_url = f"https://api.hostfully.com/v2/properties?agencyId={agency_id}"

# Set up headers
headers = {
    "accept": "application/json",
    "X-HOSTFULLY-APIKEY": api_key,
}


# Function to fetch properties
def fetch_properties():
    response = requests.get(endpoint_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


# Function to calculate dynamic pricing
def calculate_dynamic_price(base_price, some_factor):
    # Implement your dynamic pricing logic here
    return base_price * some_factor


# Fetch properties
properties = fetch_properties()
if properties:
    for property_data in properties:
        property_id = property_data.get("property_id")
        base_price = property_data.get("base_price")  # Assuming the API returns a 'base_price' field
        some_factor = 1.1  # Replace this with real factors that affect pricing

        # Calculate dynamic price
        final_price = calculate_dynamic_price(base_price, some_factor)

        print(f"Property ID: {property_id}, Dynamic Price: ${final_price}")
else:
    print("Failed to fetch properties.")
