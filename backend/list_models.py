from google import genai
from core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

print("Available models that support generateContent:\n")
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(f"  {model.name}")