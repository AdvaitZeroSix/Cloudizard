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


def get_weather(query):
    return "Weather API will be called here."


def get_pokemon(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
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

    prompt = f"""You are a routing assistant. Given the user query below, decide what to do.

If the query is about a Pokemon, reply with exactly: POKEMON <pokemon_name>
If the query is about weather, reply with exactly: WEATHER
Otherwise, just answer the question directly in plain text.

User query: {query}"""

    response = model.generate_content(prompt)
    result = response.text.strip()

    if result.startswith("POKEMON"):
        pokemon_name = result.split(" ", 1)[1].strip()
        return get_pokemon(pokemon_name)

    elif result.startswith("WEATHER"):
        return get_weather(query)

    else:
        return result


@app.route("/", methods=["GET", "POST"])
def home():

    response = ""

    if request.method == "POST":
        user_query = request.form["query"]
        response = route_query(user_query)

    return render_template(
        "index.html",
        response=response
    )


if __name__ == "__main__":
    app.run(debug=True)