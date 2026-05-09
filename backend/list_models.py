import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit()

genai.configure(api_key=api_key)

print("--- AVAILABLE GEMINI MODELS ---")
# Loop through and list models that support text generation
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")
print("-------------------------------")