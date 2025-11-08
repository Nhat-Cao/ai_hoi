import requests, os
from typing import Optional
from dotenv import load_dotenv

# Envỉonment variables & OpenAI Azure Client Setup
load_dotenv()
def is_env_missing(var):
    v = os.getenv(var)
    return v is None or v.strip() == ""

if (
    is_env_missing("FOURSQUARE_API_KEY")
):
    raise ValueError("Please set FOURSQUARE_API_KEY.")

# ============================
# CONFIGURATION
# ============================
USER_AGENT = "ai-hoi/1.0 (nhatcp2000@gmail.com)"  # replace with your contact info
FSQ_HEADERS = {
    "Accept": "application/json",
    "X-Places-Api-Version": "2025-06-17",
    "Authorization": f"Bearer {os.getenv("FOURSQUARE_API_KEY")}"
}

# ============================
# FUNCTION: Get coordinates from location text
# ============================
def get_coordinates_from_text(location_text: str):
    """
    Given a location text (address, city, region…), return latitude and longitude.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_text,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {"User-Agent": USER_AGENT}
    print(f"🔍 Geocoding location text: {location_text}")
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"❌ Error querying Nominatim search API: status {res.status_code}")
            print("Response:", res.text)
            return None

        data = res.json()
        if not data:
            print(f"❌ No results found for text: {location_text}")
            return None

        first = data[0]
        lat = float(first["lat"])
        lon = float(first["lon"])
        return {"lat": lat, "lon": lon}

    except Exception as e:
        print("🚨 Exception in get_coordinates_from_text:", e)
        return None

# ============================
# FUNCTION: Get location text (area name) from coordinates
# ============================
def get_location_from_coordinates(lat: float, lon: float):
    """
    Given latitude and longitude, return human-readable location info (e.g., city, state, country).
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "accept-language": "en"
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"❌ Error querying Nominatim reverse API: status {res.status_code}")
            print("Response:", res.text)
            return None

        data = res.json()
        address = data.get("address", {})
        display_name = data.get("display_name", "")

        # derive area name from address components
        area_name = (
            address.get("suburb") or
            address.get("town") or
            address.get("city") or
            address.get("county") or
            address.get("state") or
            display_name
        )

        return {
            "display_name": display_name,
            "area_name": area_name,
            "address_details": address
        }

    except Exception as e:
        print("🚨 Exception in get_location_from_coordinates:", e)
        return None


# ===========================
# FUNCTION: Search restaurants and return as formatted string
# ===========================
def search_restaurants_as_string(
    lat: float,
    lon: float,
    dish_name: Optional[str] = None,
    radius: int = 3000,
    limit: int = 5
) -> str:
    """
    Searches for restaurants near the specified latitude & longitude using Foursquare Places API v3,
    optionally filters by dish name, then returns a single formatted string of results.
    
    :param lat: latitude of the search centre
    :param lon: longitude of the search centre
    :param dish_name: optional keyword for dish/food item to filter restaurants
    :param radius: search radius in metres
    :param limit: maximum number of results to return
    :return: a formatted string summarising found restaurants
    """
    url = "https://places-api.foursquare.com/places/search"
    params = {
        "ll": f"{lat},{lon}",
        "query": dish_name or "restaurant",
        "radius": radius,
        "limit": limit
    }
    
    try:
        res = requests.get(url, headers=FSQ_HEADERS, params=params, timeout=10)
        status_code = res.status_code
        # Log status for debugging
        print("📡 API Response Status:", status_code)
        print("📡 API Requested with:", params)
        
        if status_code != 200:
            # Return error message as string
            return f"Error: Foursquare API returned status {status_code}. Response: {res.text}"
        
        data = res.json()
        results = data.get("results", [])
        if not results:
            return "No restaurants found."
        
        # Build string result
        lines = []
        for idx, r in enumerate(results, start=1):
            name = r.get("name", "Unnamed")
            address = r.get("location", {}).get("formatted_address", "No address provided")
            distance = r.get("distance", None)
            categories = [c.get("name") for c in r.get("categories", [])]
            cat_str = ", ".join(categories) if categories else "No categories"
            if distance is not None:
                line = f"{idx}. {name} — {address} (≈ {distance} m) | Categories: {cat_str}"
            else:
                line = f"{idx}. {name} — {address} | Categories: {cat_str}"
            lines.append(line)
        
        # Join lines into single string
        result_string = "\n".join(lines)
        return result_string
    
    except Exception as e:
        # Return exception message as string
        return f"Exception during Foursquare API call: {e}"