import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)
model = genai.GenerativeModel("gemini-2.5-flash")


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

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"]
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
    name = data["name"]
    height = data["height"]
    weight = data["weight"]
    image = data["sprites"]["front_default"]
    pokemon_type = data["types"][0]["type"]["name"]

    return {
        "name": name,
        "height": height,
        "weight": weight,
        "image": image,
        "type": pokemon_type
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
    except Exception:
        return "Cloudizard is getting a lot of questions right now — please wait a few seconds and try again."

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