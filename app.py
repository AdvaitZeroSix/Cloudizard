import os
import logging
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)
model = genai.GenerativeModel("gemini-3.1-flash-lite")


def get_weather(city):
    api_key = os.getenv("WEATHER_API_KEY")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException:
        return "Sorry, I couldn't reach the weather service right now."

    if response.status_code != 200:
        return f"Sorry, I couldn't find weather for '{city}'. Try a different city name."

    data = response.json()

    # Convert sunrise/sunset (unix UTC) into the city's local time using its UTC offset
    tz_offset = data.get("timezone", 0)  # seconds
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


def get_pokemon(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        return "Sorry, I couldn't reach the Pokémon service right now."

    if response.status_code != 200:
        return f"Sorry, I couldn't find a Pokémon named '{pokemon_name}'."

    data = response.json()

    # PokéAPI returns height in decimetres and weight in hectograms - convert to metres/kg
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

    # Single Gemini call handles both routing AND extraction (city / pokemon name)
    # to stay well under the free-tier rate limit (5 requests/minute).
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

    if result.startswith("POKEMON"):
        pokemon_name = result.split(" ", 1)[1].strip()
        return get_pokemon(pokemon_name)

    elif result.startswith("WEATHER"):
        city = result.split(" ", 1)[1].strip()
        return get_weather(city)

    else:
        return result


@app.route("/", methods=["GET", "POST"])
def home():

    response = ""
    query = ""

    if request.method == "POST":
        query = request.form["query"]
        response = route_query(query)

    return render_template(
        "index.html",
        response=response,
        query=query
    )


if __name__ == "__main__":
    app.run(debug=True)