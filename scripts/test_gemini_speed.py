
import time

from google import genai
from google.genai import types
from devmate.config import settings

client = genai.Client(api_key=settings.gemini_api_key)

try:
    start = time.perf_counter()

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents="What does a Python class do? Answer in 2 sentences.",
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=150,
        ),
    )

    print("Response:")
    print(response.text)

    print(
        f"\nGeneration time: "
        f"{time.perf_counter() - start:.2f} seconds"
    )

finally:
    client.close()
