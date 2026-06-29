import requests
from flask import Flask, render_template, request

app = Flask(__name__)


def get_weather(query):
    return "Weather API will be called here."


def get_pokemon(query):
    
    pokemon = query.split()[-1].lower()

    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"

    response = requests.get(url)
    data=response.json()
    name=data["name"]
    height=data["height"]
    weight=data["weight"]
    image=data["sprites"]["front_default"]
    pokemon_type=data["types"][0]["type"]["name"]

    return {
    "name": name,
    "height": height,
    "weight": weight,
    "image": image,
    "type": pokemon_type
}


def get_gemini(query):
    return "Gemini API will be called here."


def route_query(query):

    query = query.lower()

    weather_keywords = [
        "weather",
        "temperature",
        "forecast",
        "rain",
        "humidity",
        "wind"
    ]

    pokemon_keywords = [
    "pokemon",
    "pikachu",
    "charizard",
    "bulbasaur",
    "squirtle",
    "charmander",
    "eevee",
    "mew",
    "mewtwo",
    "gengar",
    "lucario",
    "greninja",
    "snorlax",
    "gyarados",
    "dragonite",
    "lapras",
    "ditto",
    "rayquaza",
    "garchomp"
    ]

    if any(word in query for word in weather_keywords):
        return get_weather(query)

    elif any(word in query for word in pokemon_keywords):
        return get_pokemon(query)

    else:
        return get_gemini(query)


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