import os
import openai
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')

# Set the API key for the OpenAI package
openai.api_key = api_key

# Use the OpenAI package to make API requests
response = openai.Completion.create(
    engine="davinci",
    prompt="Hello, World!",
    max_tokens=100
)

print(response.choices[0].text)