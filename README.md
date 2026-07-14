# Cloudizard

Cloudizard is an AI-powered router built with Flask. You type a question in plain
English, and Gemini decides what you're actually asking for — a Pokémon lookup,
a weather report, or a general question — and routes it to the right API
automatically.

## How it works

1. You submit a query through the web form (e.g. "what's the weather in Tokyo"
   or "tell me about pikachu").
2. Gemini (`gemini-2.5-flash`) classifies the query as `POKEMON`, `WEATHER`,
   or general knowledge.
3. Based on that classification:
   - **Pokémon queries** hit the [PokéAPI](https://pokeapi.co/) and return
     name, type, height, weight, and sprite image.
   - **Weather queries** have the city name extracted by Gemini, then hit the
     [OpenWeatherMap API](https://openweathermap.org/api) for current
     temperature, conditions, humidity, and wind speed.
   - **Everything else** gets answered directly by Gemini.

## APIs used

- **Google Gemini API** — query routing/classification and general Q&A
- **OpenWeatherMap API** — real-time weather data
- **PokéAPI** — Pokémon data (no key required)

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/cloudizard.git
   cd cloudizard
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   WEATHER_API_KEY=your_openweathermap_api_key_here
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## Project structure

```
cloudizard/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Notes

- `.env` is excluded from version control via `.gitignore` — never commit API keys.
- Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).
- Get a free OpenWeatherMap API key at [openweathermap.org](https://openweathermap.org/api).