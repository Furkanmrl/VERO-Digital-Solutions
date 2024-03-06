import argparse
import requests
import pandas as pd
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Client script for processing CSV on the server.")
    parser.add_argument("-k", "--keys", nargs="+", help="Additional keys for columns", required=True)
    parser.add_argument("-c", "--colored", action="store_true", help="Color rows based on 'hu' logic")
    parser.add_argument("--file", help="Path to the CSV file", required=True)
    args = parser.parse_args()

    # Read CSV file
    try:
        csv_data = pd.read_csv(args.file, encoding="utf-8-sig", na_values=[""], keep_default_na=False, quoting=3).fillna("").to_dict("records")
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return

    # Send CSV data to server
    server_url = "http://127.0.0.1:5000/process_csv"  # Update with your server URL
    try:
        response = requests.post(server_url, json=csv_data)
        response.raise_for_status()
        processed_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with the server: {str(e)}")
        return

    # Generate Excel file
    generate_excel(processed_data, args)

def generate_excel(processed_data, args):
    # Extract resources and color codes from the processed data
    resources = [entry["resource"] for entry in processed_data]
    color_codes = [entry["colorCode"] for entry in processed_data]

    # Sort by 'gruppe' field
    resources.sort(key=lambda x: x.get("gruppe", ""))

    # Extract keys based on input arguments
    keys_to_include = ["rnr"] + args.keys

    # Create a DataFrame with selected keys and resources
    df = pd.DataFrame([{key: resource[key] for key in keys_to_include} for resource in resources])

    # Check if 'hu' is present in the DataFrame before applying styling
    if 'hu' in df.columns and args.colored:
        colors = get_colors_based_on_hu(resources)
        df_style = df.style.apply(lambda x: [f"background-color: {colors[val]}" for val in x], subset=["hu"])
    else:
        df_style = df.style

    # Write the DataFrame to an Excel file
    current_date_iso_formatted = datetime.now().isoformat()[:19].replace(":", "-")
    excel_filename = f"vehicles_{current_date_iso_formatted}.xlsx"
    df_style.to_excel(excel_filename, index=False)
    print(f"Excel file '{excel_filename}' created successfully.")



def get_colors_based_on_hu(resources):
    colors = {"hu": ""}
    for resource in resources:
        hu_value = resource.get("hu", "")
        if isinstance(hu_value, str) and "months" in hu_value:
            # Extract the number of months
            months = int(hu_value.split()[0])
            # Apply color logic based on the number of months
            if months <= 3:
                colors[hu_value] = "#007500"  # Green
            elif 3 < months <= 12:
                colors[hu_value] = "#FFA500"  # Orange
            else:
                colors[hu_value] = "#b30000"  # Red
    return colors

if __name__ == "__main__":
    main()
