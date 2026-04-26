---
name: weather
description: Get current weather and forecasts for any location. No API key required.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - curl
---

# Weather

Get current weather and forecasts for any city or location.
Uses wttr.in and Open-Meteo — both free, no API key needed.

## Usage

```
What's the weather in Amsterdam?
Weather forecast for London this week
Current temperature in Tokyo
```

## How to get weather

**Current conditions:**
Run: `curl -s "wttr.in/{CITY}?format=j1"`
Parse the JSON for temp_C, weatherDesc, humidity, windspeedKmph.

**7-day forecast:**
Get coordinates first: `curl -s "https://geocoding-api.open-meteo.com/v1/search?name={CITY}&count=1"`
Then: `curl -s "https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&forecast_days=7&timezone=auto"`

**One-liner summary:**
`curl -s "wttr.in/{CITY}?format=3"` returns: `{city}: ⛅️ +18°C`

## Weather codes (Open-Meteo)
- 0: Clear sky
- 1-3: Partly cloudy
- 45,48: Fog
- 51-67: Rain/drizzle
- 71-77: Snow
- 80-82: Rain showers
- 95: Thunderstorm

## Output format

Always present weather as:
```
📍 {City}
🌡️ Temperature: {temp}°C (feels like {feels_like}°C)
🌤️ Conditions: {description}
💧 Humidity: {humidity}%
💨 Wind: {wind} km/h
🌅 Sunrise: {sunrise} | 🌇 Sunset: {sunset}
```

For forecasts, show a table with emoji per day.
