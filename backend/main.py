from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os 
from openai import AzureOpenAI
from dotenv import load_dotenv
from location import get_coordinates_from_text, get_location_from_coordinates, search_restaurants_as_string

# ---------------------- Setup ----------------------
load_dotenv()
client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

system_message = {
    "role": "system",
    "content": """
    You are an expert Vietnamese food reviewer.
    Provide detailed, engaging, and location-aware food and restaurant reviews.
    Each restaurant recommendation should include specific address if any.
    Always answer in Vietnamese.
    """
}

# ---------------------- Models ----------------------
class ChatMessage(BaseModel):
    text: str
    location: str  # current location text, e.g. "10.762622,106.660172"

class Location(BaseModel):
    lat: float
    lon: float

# ---------------------- Helper ----------------------
def extract_entities(input_text: str):
    """Use Azure OpenAI function calling to extract food and location info."""
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        messages=[
            {"role": "system", "content": """Extract structured text data from user requests about food and location.
             If user don't mention a specific dish, return None for food property.
             If user says “nearby”, “gần tôi”, “around me”, or somethings similar and no specific location provided. Return None for location property."""},
            {"role": "user", "content": input_text}
        ],
        functions=[
            {
                "name": "extract_food_and_location",
                "description": "Extracts food name and location name from text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "food": {"type": "string", "description": "Food or dish name mentioned"},
                        "location": {"type": "string", "description": "Location mentioned in text"},
                    },
                    "required": []
                }
            }
        ],
        function_call={"name": "extract_food_and_location"},
    )

    args = response.choices[0].message.function_call.arguments
    import json
    try:
        parsed = json.loads(args)
    except:
        parsed = {"food": None, "location": None}
    return parsed.get("food"), parsed.get("location")

# ---------------------- Chat Logic ----------------------
def gen_answer(user_input, current_location):
    """Main chat logic with context injection."""
    food, place_text = extract_entities(user_input)
    print(f"🍜 Extracted food: {food}, location: {place_text}")
    
    coords = None
    # Determine coordinates
    if place_text not in [None, ""]:
        coords = get_coordinates_from_text(place_text)
    if coords is None and current_location not in [None, ""]:
        coords = get_coordinates_from_text(current_location)
    if coords is None and current_location in [None, ""]:
        return "Xin lỗi, tôi không thể xác định vị trí của bạn. Vui lòng cung cấp vị trí hợp lệ."

    # Use Foursquare search to get nearby restaurants
    nearby_restaurants = search_restaurants_as_string(coords["lat"], coords["lon"], food or "")

    # Compose context
    context = f"Những nhà hàng liên quan ở gần đó:\n{nearby_restaurants}\n\nNgười dùng hỏi: {user_input}"

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        messages=[
            system_message,
            {"role": "user", "content": context}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# ---------------------- FastAPI ----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ai-hoi-web.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(message: ChatMessage):
    return {"message": gen_answer(message.text, message.location)}

@app.post("/location")
async def reverse_geocode(location: Location):
    return get_location_from_coordinates(location.lat, location.lon)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
