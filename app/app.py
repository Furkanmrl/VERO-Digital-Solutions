from flask import Flask, jsonify, request
import requests
from typing import List
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

class ServerError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

def get_access_token():
    url = "https://api.baubuddy.de/index.php/login"
    payload = {
        "username": "365",
        "password": "1"
    }
    headers = {
        "Authorization": "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise ServerError(status_code=response.status_code, detail=response.text)

    return response.json()["oauth"]["access_token"]

def get_color_code(label_id, access_token):
    url = f"https://api.baubuddy.de/dev/index.php/v1/labels/{label_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None  # Handle the error case appropriately

    return response.json().get("colorCode", None)

def filter_resources(resources):
    return [resource for resource in resources if resource.get("hu")]

@app.route('/process_csv', methods=['POST'])
def process_csv():
    try:
        access_token = get_access_token()

        # Fetch resources from external API
        resources_url = "https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active"
        headers = {"Authorization": f"Bearer {access_token}"}
        resources_response = requests.get(resources_url, headers=headers)
        
        if resources_response.status_code != 200:
            raise ServerError(status_code=resources_response.status_code, detail=resources_response.text)

        external_resources = resources_response.json()

        # Merge resources with CSV data
        merged_resources = merge_resources(request.json, external_resources)

        # Filter resources based on 'hu' field
        filtered_resources = filter_resources(merged_resources)

        # Prepare response with color codes
        colored_resources = []
        for resource in filtered_resources:
            color_code = get_color_code(resource.get("labelIds")[0], access_token) if resource.get("labelIds") else None
            colored_resources.append({"resource": resource, "colorCode": color_code})

        return jsonify(colored_resources), 200
    except ServerError as e:
        return jsonify({"error": e.detail}), e.status_code

def merge_resources(csv_data, external_resources):
    # Perform the merging logic based on your requirements
    # You need to implement this based on the structure of your data
    # Here is a simple example assuming 'labelIds' is the key for merging
    merged_resources = []
    for csv_entry in csv_data:
        for external_entry in external_resources:
            if csv_entry["labelIds"] == external_entry["labelIds"]:
                merged_entry = {**csv_entry, **external_entry}
                merged_resources.append(merged_entry)
                break
    return merged_resources

@app.route('/')
def index():
    colored_resources = []
    return jsonify(colored_resources), 200

if __name__ == "__main__":
    app.run(debug=True)
