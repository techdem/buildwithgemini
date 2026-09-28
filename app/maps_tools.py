import json
import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

def _get_maps_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    return key

def geocode_address(address: str) -> str:
    """Converts a street address or city name into latitude and longitude geographic coordinates using the Google Geocoding API."""
    api_key = _get_maps_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return json.dumps({
            "status": "ERROR",
            "message": "GOOGLE_MAPS_API_KEY is missing or set to placeholder in .env file."
        })

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return json.dumps({
                    "status": "NO_RESULTS",
                    "address": address,
                    "api_status": data.get("status"),
                    "message": f"Could not geocode address '{address}'."
                })

            result = data["results"][0]
            loc = result["geometry"]["location"]
            
            return json.dumps({
                "status": "SUCCESS",
                "name": result.get("formatted_address", address),
                "address": result.get("formatted_address"),
                "location": {
                    "latitude": loc["lat"],
                    "longitude": loc["lng"]
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "address": address,
            "message": f"Geocoding API request failed: {str(e)}"
        })

def search_nearby_places(latitude: float, longitude: float, place_type: str = "supermarket", radius: float = 1500.0) -> str:
    """Finds nearby places (e.g. grocery stores, supermarkets, restaurants) around given coordinates using the Places API (New)."""
    api_key = _get_maps_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return json.dumps({
            "status": "ERROR",
            "message": "GOOGLE_MAPS_API_KEY is missing or set to placeholder in .env file."
        })

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        }
    }

    try:
        json_data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            places = res_data.get("places", [])

            if not places:
                return json.dumps({
                    "status": "NO_RESULTS",
                    "latitude": latitude,
                    "longitude": longitude,
                    "place_type": place_type,
                    "message": f"No nearby '{place_type}' places found within {radius} meters."
                })

            results = []
            for p in places:
                loc = p.get("location", {})
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown Place"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude")
                    }
                })

            return json.dumps({
                "status": "SUCCESS",
                "count": len(results),
                "places": results
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "message": f"Places API (New) request failed: {str(e)}"
        })
