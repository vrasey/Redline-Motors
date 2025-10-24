import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Initialize the Flask App ---
app = Flask(__name__)
# --- This is the magic line that fixes the "failed to fetch" error ---
# It allows your .tech domain to make requests to your .azurewebsites.net domain
CORS(app)


# --- This is your scraper function, upgraded to get the image ---
def get_yahoo_auction_details(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        name_tag = soup.find("h1", class_="ProductTitle__text")
        name = name_tag.text.strip() if name_tag else "Name not found"

        price_tag = soup.find("span", class_="Price__value")
        price = price_tag.text.strip() if price_tag else "Price not found"
        
        # This selector is often for the "Buy Now" price
        endprice_tag = soup.find("span", class_="Price--buynow")
        endprice = endprice_tag.text.strip() if endprice_tag else "N/A"

        end_tag = soup.find("span", class_="ProductDetails__remainingTime")
        end_time = end_tag.text.strip() if end_tag else "End time not found"

        # --- NEW: Get the main image ---
        image_tag = soup.find("div", class_="ProductImage__image").find("img")
        image_url = image_tag["src"] if image_tag else None

        return {
            "name": name,
            "price": price,
            "endprice": endprice,
            "end_time": end_time,
            "imageUrl": image_url # Your JavaScript is looking for "imageUrl"
        }
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return None


# --- This is the API Endpoint ---
# Your JavaScript will send its request to this URL path
@app.route("/scrape", methods=["POST", "OPTIONS"])
def scrape():
    # Get the JSON data sent from the JavaScript
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Run your scraper function
    details = get_yahoo_auction_details(url)

    if details:
        # Send the details back to the JavaScript as JSON
        return jsonify(details)
    else:
        return jsonify({"error": "Failed to scrape details or item page is invalid"}), 500

# This allows Azure to run the app
if __name__ == "__main__":
    app.run()