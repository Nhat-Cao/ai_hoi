from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from markdown_helper import parse_restaurant_markdown, restaurant_to_text
import os 
from openai import AzureOpenAI
from dotenv import load_dotenv
from location_helper import get_coordinates_from_text, get_location_from_coordinates, search_restaurants_as_string
from elevenlabs import ElevenLabs
from db_helper import query_data, upsert_data

# ---------------------- Setup ----------------------
load_dotenv()

# Clear any proxy settings to avoid 407 errors
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

system_message = {
    "role": "system",
    "content": """
    You are an expert Vietnamese food reviewer.
    Provide detailed, engaging, and location-aware food and restaurant reviews.
    Each restaurant recommendation should include specific address if any.
    Always answer in Vietnamese.
    You will be provided data from database and nearby restaurant search to help you answer better.
    If user's query is unrelated to food or restaurants, politely inform them that you can only assist with food and restaurant-related inquiries.
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
             If user says "nearby", "gần tôi", "around me", "gần đây" or somethings similar or no specific location provided. Return None for location property."""},
            {"role": "user", "content": input_text}
        ],
        functions=[
            {
                "name": "extract_food_and_location",
                "description": "Extracts food name and location name from text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "food": {"type": "string", "description": "Food or dish name mentioned, if no food mentioned, return null/None"},
                        "location": {"type": "string", "description": "Location mentioned in text, If user says 'nearby', 'gần tôi', 'around me', 'gần đây', 'near me' or somethings similar or no specific location provided, return null/None"},
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
    
    context = ""
    if ((food is not None or food != "") or (place_text is not None or place_text != "")):
        query = f"'{food}' '{place_text}'."
        results = query_data(query, top_k=5, namespace="restaurants")
        if results and len(results) > 0:
            context += "Thông tin tham khảo từ cơ sở dữ liệu:\n"
            for res in results:
                context += f"- {res}\n"
            context += "\n"
        print(f"🗄️ Retrieved {len(results)} context entries from DB.")
    
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
    context += f"Những nhà hàng liên quan ở gần đó:\n{nearby_restaurants}\n\nNgười dùng hỏi: {user_input}"
    print(f"🗒️ Context for LLM:\n{context}")
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
    print(f"📝 Received chat request: {message.dict()}")
    try:
        answer = gen_answer(message.text, message.location)
        print(f"✅ Generated answer successfully")
        return {"message": answer}
    except Exception as e:
        print(f"❌ Error generating answer: {str(e)}")
        raise

@app.post("/location")
async def reverse_geocode(location: Location):
    return get_location_from_coordinates(location.lat, location.lon)

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert audio file to text using ElevenLabs Speech-to-Text API optimized for Vietnamese"""
    try:
        # Read the uploaded audio file
        audio_content = await audio.read()
        print(f"🎙️ Received audio file: {len(audio_content)} bytes")
        
        # Create BytesIO object from audio content
        from io import BytesIO
        audio_data = BytesIO(audio_content)
        
        # Use ElevenLabs Speech-to-Text with Vietnamese language specification
        print("🎙️ Calling ElevenLabs Speech-to-Text API...")
        transcription = elevenlabs_client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",  # Only scribe_v1 is supported
            language_code="vi"  # Explicitly set to Vietnamese for better accuracy
        )
        
        print(f"✅ Transcription successful: {transcription.text}")
        return {"text": transcription.text}
    
    except TimeoutError as e:
        print(f"⏱️ Speech-to-text timeout: {e}")
        return {"error": "Request timeout. Please try again.", "text": ""}
    except Exception as e:
        print(f"🎙️ Speech-to-text error: {e}")
        return {"error": f"Transcription failed: {str(e)}", "text": ""}

@app.post("/text-to-speech")
async def text_to_speech(message: dict):
    """Convert text to speech using ElevenLabs TTS API"""
    try:
        text = message.get("text", "")
        if not text:
            return Response(content=b"", media_type="audio/mpeg")
        
        # Use ElevenLabs TTS with turbo v2.5 model (v3) for better Vietnamese support
        audio_generator = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id="deC6NEXcbavaVWbzjgzb",
            model_id="eleven_v3",  # Human-like and expressive speech generation
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.5,  # Balanced stability for clear Vietnamese pronunciation
                "similarity_boost": 0.75,  # Higher similarity for natural Vietnamese tone
                "style": 0.5,  # Moderate style for conversational Vietnamese
                "use_speaker_boost": True  # Enhanced clarity for Vietnamese speech
            }
        )
        
        # Convert generator to bytes
        audio_bytes = b"".join(audio_generator)
        
        return Response(content=audio_bytes, media_type="audio/mpeg")
    
    except Exception as e:
        print(f"🔊 Text-to-speech error: {e}")
        return Response(content=b"", media_type="audio/mpeg")
    


class MarkdownData(BaseModel):
    content: str
    namespace: str = "restaurants"

@app.post("/ingest-restaurants")
async def ingest_restaurants(data: MarkdownData):
    """
    Ingest restaurants data from markdown text into the vector database.
    The markdown should follow the specified format with ## headers for each restaurant.
    """
    try:
        # Parse markdown content
        restaurants = parse_restaurant_markdown(data.content)
        if not restaurants:
            raise HTTPException(status_code=400, detail="No restaurant information found in the markdown")
        
        # Store each restaurant in the database
        success_count = 0
        for restaurant in restaurants:
            text = restaurant_to_text(restaurant)
            if upsert_data(text, namespace="restaurants"):
                success_count += 1
        
        return JSONResponse(
            content={
                "message": f"Successfully ingested {success_count} restaurants into the database",
                "total_processed": len(restaurants),
                "successful": success_count
            },
            status_code=200
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing markdown: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI-HOI Backend is running with ElevenLabs Voice features."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
