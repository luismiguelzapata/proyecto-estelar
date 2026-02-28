import os
from google import genai
from google.genai import types
from PIL import Image
import io


client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Generate an image
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="A serene mountain lake at sunset with reflections",
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)

# Save the generated image
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        image = Image.open(io.BytesIO(part.inline_data.data))
        image.save("generated_image.png")
        print("Image saved successfully!")
    elif part.text is not None:
        print(f"Model response: {part.text}")