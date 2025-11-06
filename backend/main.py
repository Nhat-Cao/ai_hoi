from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import os 
from openai import AzureOpenAI
from dotenv import load_dotenv
import tempfile
from location import get_coordinates_from_text, get_location_from_coordinates, search_restaurants_as_string
from typing import Optional, List
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone

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

class RAGChatRequest(BaseModel):
    query: str
    namespace: Optional[str] = None

# ---------------------- Helper ----------------------
def get_rag_context(food: Optional[str] = None, place_text: Optional[str] = None) -> str:
    """Get relevant context from knowledge base using food and location."""
    try:
        # Build search query from food and location
        search_query = ""
        if food:
            search_query += f"{food} "
        if place_text:
            search_query += f"{place_text}"
        if not search_query:
            return ""

        # Initialize embeddings using the same model as LLM
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_MODEL_NAME"),
            openai_api_version="2024-07-01-preview",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Get similar documents from Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        vectorstore = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX"),
            embedding=embeddings
        )

        # Search and get text from similar documents
        print(f"🔍 Searching knowledge base with: {search_query}")
        docs = vectorstore.similarity_search(search_query, k=4)
        if not docs:
            return ""

        # Return combined text from documents
        return "\n".join(d.page_content for d in docs)

    except Exception as e:
        print(f"❌ Error getting RAG context: {e}")
        return ""

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
    # Extract food and location entities from user input
    food, place_text = extract_entities(user_input)
    print(f"🍜 Extracted food: {food}, location: {place_text}")
    
    # Get location coordinates
    coords = None
    if place_text not in [None, ""]:
        coords = get_coordinates_from_text(place_text)
    if coords is None and current_location not in [None, ""]:
        coords = get_coordinates_from_text(current_location)
    if coords is None and current_location in [None, ""]:
        return "Xin lỗi, tôi không thể xác định vị trí của bạn. Vui lòng cung cấp vị trí hợp lệ."

    try:
        # Get nearby restaurants from Foursquare
        nearby_restaurants = search_restaurants_as_string(coords["lat"], coords["lon"], food or "")

        # Get relevant knowledge from database
        kb_context = get_rag_context(food, place_text)
        rag_part = f"\nThông tin từ cơ sở dữ liệu:\n{kb_context}\n" if kb_context else ""
        
        # Compose final context
        context = f"{rag_part}Những nhà hàng gần đó:\n{nearby_restaurants}\n\nNgười dùng hỏi: {user_input}"
    except Exception as e:
        print(f"❌ Error preparing context: {e}")
        context = f"Người dùng hỏi: {user_input}"

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

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert audio file to text using Azure Whisper API"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        # Use Azure OpenAI Whisper API
        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",  # Azure OpenAI Whisper model
                file=audio_file,
                language="vi"  # Vietnamese language
            )
        
        # Clean up temp file
        os.unlink(temp_audio_path)
        
        return {"text": transcription.text}
    
    except Exception as e:
        print(f"❌ Speech-to-text error: {e}")
        return {"error": str(e), "text": ""}

@app.post("/text-to-speech")
async def text_to_speech(message: dict):
    """Convert text to speech using Azure TTS API"""
    try:
        text = message.get("text", "")
        if not text:
            return Response(content=b"", media_type="audio/mpeg")
        
        # Use Azure OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # Azure OpenAI TTS model
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        # Return audio as response
        audio_content = response.content
        return Response(content=audio_content, media_type="audio/mpeg")
    
    except Exception as e:
        print(f"❌ Text-to-speech error: {e}")
        return Response(content=b"", media_type="audio/mpeg")

async def process_lines(lines: List[str], embeddings: AzureOpenAIEmbeddings, pc: Pinecone):
    """Process lines and save to Pinecone."""
    try:
        # Convert lines to embeddings in batches
        batch_size = 32
        for i in range(0, len(lines), batch_size):
            batch = lines[i:i + batch_size]
            # Get embeddings for batch
            vectors = []
            for j, text in enumerate(batch):
                vector = {
                    "id": f"doc-{i+j}",
                    "values": embeddings.embed_query(text),
                    "metadata": {"text": text}
                }
                vectors.append(vector)
            
            # Upsert to Pinecone
            index = pc.Index(os.getenv("PINECONE_INDEX"))
            index.upsert(vectors=vectors)
            print(f"✅ Processed {len(vectors)} lines")
        
        return True
    except Exception as e:
        print(f"❌ Error processing lines: {e}")
        return False

@app.post("/ingest")
async def ingest_data(file: UploadFile = File(...)):
    """Ingest data from file (CSV, MD, JSONL) into knowledge base."""
    try:
        print(f"Processing file: {file.filename}")
        content = await file.read()
        text = content.decode('utf-8')
        lines = []

        # Process based on file type
        if file.filename.endswith('.jsonl'):
            import json
            for i, line in enumerate(text.splitlines()):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # Format the text in a way that's useful for retrieval
                    food_text = f"{data['ten_mon']} là món {data['loai_mon']} {data['khau_vi']} ở {data['khu_vuc']}. {data['dac_diem']} Món này phù hợp với {data['doi_tuong_phu_hop']}, thường được ăn vào {data['thoi_gian_phu_hop']}, đặc biệt là trong {data['thoi_tiet_phu_hop']}. Giá tham khảo: {data['gia_tham_khao']}đ."
                    lines.append(food_text)
                    print(f"Processed line {i+1}: {data['ten_mon']}")
                except Exception as e:
                    print(f"Error processing JSON line {i+1}: {e}")
                    continue
        elif file.filename.endswith('.csv'):
            for line in text.splitlines():
                if not line.strip():
                    continue
                lines.append(line)
        elif file.filename.endswith('.md'):
            # Split markdown by paragraphs
            lines = [p for p in text.split('\\n\\n') if p.strip()]
        else:
            return {"error": "Unsupported file type. Please upload CSV, MD, or JSONL."}

        if not lines:
            return {"error": "No valid content found in file."}

        # Initialize Azure OpenAI embeddings
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_MODEL_NAME"),
            openai_api_version="2024-07-01-preview",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Process and save to DB
        if await process_lines(lines, embeddings, pc):
            return {"message": f"Successfully processed {len(lines)} lines"}
        else:
            return {"error": "Error processing file"}

    except Exception as e:
        print(f"❌ Error in ingest endpoint: {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "AI-HOI Backend is running with Voice & Video features."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
