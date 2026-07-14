# Cloudizard

Live app: https://cloudizard.onrender.com

Note: the app is hosted on Render's free tier. If it hasn't been used in the last 15 minutes, the server spins down and the first request can take 30 to 60 seconds to respond while it restarts.

## What it does

Cloudizard is a Flask app with one text box. You type a question, and Gemini figures out what kind of question it is before deciding what to do with it:

- If it's about a Pokemon, it calls the PokeAPI and returns stats, types, and abilities.
- If it's about weather, it pulls the city name out of your question and calls the OpenWeatherMap API for current conditions.
- For anything else, Gemini just answers directly.

## How it works

1. The query is sent to Gemini (`gemini-3.1-flash-lite`) with a routing prompt.
2. Gemini responds with either `POKEMON <name>`, `WEATHER <city>`, or a plain text answer. The name or city is extracted in this same call, so there's no second API request.
3. Based on that response, the app calls the matching API and renders the result.

## APIs used

- Google Gemini API, for classifying the query and answering general questions
- OpenWeatherMap API, for current weather data
- PokeAPI, for Pokemon data (no key required)

## Running it locally

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/cloudizard.git
   cd cloudizard
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   WEATHER_API_KEY=your_openweathermap_api_key_here
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in a browser.

## Project structure

```
cloudizard/
    app.py
    requirements.txt
    README.md
    templates/
        index.html
    static/
        style.css
```

## Deployment

Deployed on Render's free tier, connected to this GitHub repo with auto deploy enabled. Every push to main triggers a new build.

Build command: `pip install -r requirements.txt`
Start command: `gunicorn app:app`

Environment variables (`GEMINI_API_KEY`, `WEATHER_API_KEY`) are set in the Render dashboard, not committed to the repo.

## Notes

`.env` is excluded from version control through `.gitignore`. Don't commit API keys.

Gemini API keys can be created for free at Google AI Studio. OpenWeatherMap API keys can be created for free at openweathermap.org.

Gemini model names change often as Google releases and retires versions. If the app throws a 404 model not found error, check Google AI Studio for the model names currently available on your account and update the `genai.GenerativeModel(...)` line in `app.py`.