#!/usr/bin/env python3
import click
import requests
import json
from pathlib import Path

@click.command()
@click.argument('location', required=True)
def main(location):
    """Check the weather for a given location using OpenWeatherMap API."""
    # Load API key from config in artifacts
    config_path = Path(__file__).parent.parent / 'artifacts' / 'config.json'
    try:
        with open(config_path) as f:
            config = json.load(f)
            api_key = config['api_key']
    except (FileNotFoundError, KeyError):
        click.echo("Error: API key not found. Please add your OpenWeatherMap API key to artifacts/config.json")
        return

    # Make API request
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'appid': api_key,
        'units': 'metric'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Format and display weather information
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']

        click.echo(f"\nWeather forecast for {location}:")
        click.echo(f"🌡️  Temperature: {temp}°C")
        click.echo(f"☁️  Conditions: {weather}")
        click.echo(f"💧 Humidity: {humidity}%")
        click.echo(f"💨 Wind Speed: {wind} m/s\n")

    except requests.exceptions.RequestException as e:
        click.echo(f"Error fetching weather data: {e}")
    except KeyError as e:
        click.echo(f"Error parsing weather data: {e}")

if __name__ == '__main__':
    main()
