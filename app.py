import os
import logging
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Render sits behind a proxy, so read the real client IP from X-Forwarded-For
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# Every query costs a Gemini call, so limit how fast one visitor can send them
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

MAX_QUERY_LENGTH = 500

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)
model = genai.GenerativeModel("gemini-3.1-flash-lite")


def _fetch_weather(params, not_found_msg):
    url = "https://api.openweathermap.org/data/2.5/weather"

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException:
        return "Sorry, I couldn't reach the weather service right now."

    if response.status_code != 200:
        return not_found_msg

    data = response.json()

    tz_offset = data.get("timezone", 0)
    tz = timezone(timedelta(seconds=tz_offset))
    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(data["sys"]["sunset"], tz=tz).strftime("%I:%M %p")

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "temp_min": round(data["main"]["temp_min"]),
        "temp_max": round(data["main"]["temp_max"]),
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "visibility_km": round(data.get("visibility", 0) / 1000, 1),
        "sunrise": sunrise,
        "sunset": sunset
    }


def get_weather(city):
    api_key = os.getenv("WEATHER_API_KEY")
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    not_found_msg = f"Sorry, I couldn't find weather for '{city}'. Try a different city name."
    return _fetch_weather(params, not_found_msg)


def get_weather_by_coords(lat, lon):
    api_key = os.getenv("WEATHER_API_KEY")
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    not_found_msg = "Sorry, I couldn't find weather for your location."
    return _fetch_weather(params, not_found_msg)


def get_pokemon(pokemon_name):
    # The name comes from the model, so encode it before putting it in the URL
    url = f"https://pokeapi.co/api/v2/pokemon/{quote(pokemon_name.lower(), safe='')}"

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        return "Sorry, I couldn't reach the Pokémon service right now."

    if response.status_code != 200:
        return f"Sorry, I couldn't find a Pokémon named '{pokemon_name}'."

    data = response.json()

    height_m = data["height"] / 10
    weight_kg = data["weight"] / 10

    types = [t["type"]["name"] for t in data["types"]]
    abilities = [a["ability"]["name"].replace("-", " ") for a in data["abilities"]]

    stats = {}
    for s in data["stats"]:
        stat_name = s["stat"]["name"].replace("-", " ")
        stats[stat_name] = s["base_stat"]

    image = (
        data["sprites"]["other"]["official-artwork"]["front_default"]
        or data["sprites"]["front_default"]
    )

    return {
        "name": data["name"],
        "id": data["id"],
        "height": height_m,
        "weight": weight_kg,
        "image": image,
        "type": types[0],
        "types": types,
        "abilities": abilities,
        "stats": stats
    }


def route_query(query):

    prompt = f"""You are a routing assistant. From the user query below, decide what to do.

If the query is about a Pokemon, reply with exactly: POKEMON <pokemon_name>
If the query is about weather, reply with exactly: WEATHER <city_name>
Otherwise, just answer the question directly in plain text.

User query: {query}"""

    try:
        response = model.generate_content(prompt)
    except ResourceExhausted:
        logger.warning("Gemini rate limit hit (ResourceExhausted).")
        return "Cloudizard is getting a lot of questions right now — please wait a few seconds and try again."
    except Exception as e:
        logger.error(f"Gemini call failed: {type(e).__name__}: {e}")
        return "Something went wrong talking to Gemini. Please try again in a moment."

    result = response.text.strip()

    # "POKEMON <name>" or "WEATHER <city>"; ignore the reply if the name is missing
    parts = result.split(" ", 1)

    if parts[0] == "POKEMON" and len(parts) == 2:
        return get_pokemon(parts[1].strip())

    elif parts[0] == "WEATHER" and len(parts) == 2:
        return get_weather(parts[1].strip())

    else:
        return result


@app.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def home():

    response = ""
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()[:MAX_QUERY_LENGTH]

        if query:
            response = route_query(query)

    return render_template(
        "index.html",
        response=response,
        query=query
    )


@app.route("/location-weather", methods=["POST"])
@limiter.limit("20 per minute")
def location_weather():
    data = request.get_json(silent=True) or {}
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates."}), 400

    result = get_weather_by_coords(lat, lon)

    if isinstance(result, str):
        return jsonify({"error": result}), 502

    return jsonify(result)


if __name__ == "__main__":
    # Debug mode is for local use only; set FLASK_DEBUG=1 to turn it on
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")