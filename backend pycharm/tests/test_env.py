import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key and api_key.startswith("sk-"):
    print("✅ Environment setup successful! OPENAI_API_KEY is detected.")
else:
    print("⚠️  Warning: OPENAI_API_KEY is missing or invalid in your .env file.")