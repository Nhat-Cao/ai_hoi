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
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

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

# Initialize embedding client
embedding_client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
    api_key=os.getenv("AZURE_EMBEDDING_API_KEY"),
)

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Initialize Pinecone
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "ai-hoi-conversations"

    # Create index if it doesn't exist (text-embedding-3-small has 1536 dimensions)
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # Connect to the index
    index = pc.Index(index_name)
    print("✅ Pinecone initialized successfully")
except Exception as e:
    print(f"⚠️ Pinecone initialization failed: {e}")
    index = None

# Initialize LangChain components
try:
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-07-01-preview",
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        temperature=0.7
    )
    print("✅ LangChain LLM initialized successfully")
except Exception as e:
    print(f"⚠️ LangChain initialization failed: {e}")
    llm = None
    embeddings = None

# System prompt (Vietnamese) used by LangChain and fallback
system_content = (
    "You are an expert Vietnamese food reviewer who is friendly, approachable, and cheerful.\n"
    "Answer in detail, engagingly, and with awareness of location; when possible, always provide the restaurant's specific address.\n"
    "Use a friendly, approachable, and occasionally humorous tone; you may use icons/emojis to make answers more lively.\n"
    "Always answer in English.\n\n"
    "Only answer questions related to food, dishes, restaurants, or other cuisine-related topics.\n"
    "If the user asks about unrelated subjects (for example: politics, specialized medical or legal advice, or other off-topic matters), politely decline and explain that you only answer food-related questions; suggest they ask an appropriate question.\n\n"
    "You have access to similar past conversations to provide better context:\n{similar_conversations}"
)

# A dict usable for the fallback OpenAI client
system_message = {"role": "system", "content": system_content}

# Create LangChain prompt template (use the same system_content)
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_content),
    ("human", "{context}")
])


# ---------------------- Models ----------------------
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatMessage(BaseModel):
    text: str
    location: str  # current location text, e.g. "10.762622,106.660172"
    history: list[Message] = []  # Conversation history

class Location(BaseModel):
    lat: float
    lon: float

# ---------------------- Helper ----------------------
def summarize_conversation(messages: list):
    """Summarize conversation using Azure OpenAI for better context storage."""
    if len(messages) < 2:
        return None
    
    # Messages are already dicts with 'role' and 'content' keys
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    
    summary_prompt = f"""Summarize the following conversation into a short paragraph (1-2 sentences),
    including: dishes mentioned, locations, and any restaurants recommended.

    Conversation:
    {conversation_text}

    Summary (1-2 sentences):"""
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.5,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error summarizing conversation: {e}")
        return None

def save_conversation_to_pinecone(conversation_history: list, location: str):
    """Save conversation summary to Pinecone - append to single vector."""
    if not index:
        print("⚠️ Pinecone not available, skipping save")
        return
    
    try:
        # Generate summary
        summary = summarize_conversation(conversation_history)
        if not summary:
            print("⚠️ No summary generated, skipping Pinecone save")
            return
        
        print(f"📝 Summary: {summary}")
        
        # Use a fixed ID for all conversations
        conversation_id = "all-conversations"
        
        import json
        
        # Try to fetch existing vector to append to it
        try:
            existing = index.fetch(ids=[conversation_id])
            if conversation_id in existing.vectors:
                # Get existing metadata
                existing_metadata = existing.vectors[conversation_id].metadata or {}
                existing_summaries_json = existing_metadata.get("summaries_json", "[]")
                existing_summaries = json.loads(existing_summaries_json)
                
                # Append new summary
                existing_summaries.append({
                    "summary": summary,
                    "location": location,
                    "timestamp": datetime.now().isoformat(),
                    "message_count": len(conversation_history),
                    "user_prompts": [msg['content'] for msg in conversation_history if msg['role'] == 'user']
                })
                
                # Create combined text for embedding
                combined_text = "\n".join([s["summary"] for s in existing_summaries])
                
                # Generate new embedding from combined text
                embedding_response = embedding_client.embeddings.create(
                    model=os.getenv("AZURE_EMBEDDING_MODEL"),
                    input=combined_text
                )
                embedding = embedding_response.data[0].embedding
                
                # Create overall summary from all conversations
                # Collect all user prompts for trend analysis
                all_user_prompts = []
                for s in existing_summaries:
                    all_user_prompts.extend(s.get("user_prompts", []))
                
                overall_summary_prompt = f"""Analyze and synthesize the following set of conversation summaries into a comprehensive written analysis (10-15 sentences).
                Place special emphasis on trends and user preferences inferred from their questions.

                Please include the following details:
                1. The most frequently asked dishes
                2. Frequently mentioned locations
                3. Users' cuisine preference trends (e.g., Vietnamese, international, street food, etc.)
                4. Search behavior patterns (e.g., prefer nearby options, willing to travel, search by dish vs. by location)
                5. Restaurants that were recommended and any noted feedback

                The summarized conversations:
                {combined_text}

                USER QUESTIONS (most important for analyzing preferences):
                {chr(10).join(all_user_prompts)}

                Overall synthesized summary (8-10 sentences, focusing on trends derived from user questions):"""
                
                try:
                    overall_response = client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
                        messages=[{"role": "user", "content": overall_summary_prompt}],
                        temperature=0.5,
                        max_tokens=400
                    )
                    overall_summary = overall_response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"⚠️ Error creating overall summary: {e}")
                    overall_summary = summary  # Fallback to latest summary
                
                # Update metadata (store as JSON string)
                metadata = {
                    "summaries_json": json.dumps(existing_summaries),
                    "total_conversations": len(existing_summaries),
                    "last_updated": datetime.now().isoformat(),
                    "latest_summary": overall_summary,  # Overall summary of all conversations
                    "latest_location": location
                }
                
                print(f"📚 Appending to existing vector (total: {len(existing_summaries)} conversations)")
            else:
                # First conversation - create initial vector
                embedding_response = embedding_client.embeddings.create(
                    model=os.getenv("AZURE_EMBEDDING_MODEL"),
                    input=summary
                )
                embedding = embedding_response.data[0].embedding
                
                summaries = [{
                    "summary": summary,
                    "location": location,
                    "timestamp": datetime.now().isoformat(),
                    "message_count": len(conversation_history),
                    "user_prompts": [msg['content'] for msg in conversation_history if msg['role'] == 'user']
                }]
                
                metadata = {
                    "summaries_json": json.dumps(summaries),
                    "total_conversations": 1,
                    "last_updated": datetime.now().isoformat(),
                    "latest_summary": summary,
                    "latest_location": location
                }
                
                print(f"📝 Creating first conversation vector")
        except Exception as fetch_error:
            print(f"⚠️ Fetch error (creating new): {fetch_error}")
            # First time - create initial vector
            embedding_response = embedding_client.embeddings.create(
                model=os.getenv("AZURE_EMBEDDING_MODEL"),
                input=summary
            )
            embedding = embedding_response.data[0].embedding
            
            summaries = [{
                "summary": summary,
                "location": location,
                "timestamp": datetime.now().isoformat(),
                "message_count": len(conversation_history),
                "user_prompts": [msg['content'] for msg in conversation_history if msg['role'] == 'user']
            }]
            
            metadata = {
                "summaries_json": json.dumps(summaries),
                "total_conversations": 1,
                "last_updated": datetime.now().isoformat(),
                "latest_summary": summary,
                "latest_location": location
            }
            
            print(f"📝 Creating first conversation vector")
        
        # Upsert (update or insert) the single vector
        index.upsert(vectors=[{
            "id": conversation_id,
            "values": embedding,
            "metadata": metadata
        }])
        
        print(f"✅ Updated conversation vector (ID: {conversation_id})")
        
    except Exception as e:
        print(f"❌ Error saving to Pinecone: {e}")

def retrieve_similar_conversations(query: str, top_k: int = 3):
    """Retrieve overall summary of all conversations from Pinecone."""
    if not index:
        print("⚠️ Pinecone not available")
        return "Không có cuộc hội thoại tương tự từ trước."
    
    try:
        import json
        
        # Fetch the single vector containing all conversations
        conversation_id = "all-conversations"
        existing = index.fetch(ids=[conversation_id])
        
        if conversation_id not in existing.vectors:
            print("📭 No conversation history found")
            return "Không có cuộc hội thoại tương tự từ trước."
        
        # Get overall summary from metadata
        metadata = existing.vectors[conversation_id].metadata
        latest_summary = metadata.get("latest_summary", "")
        total_conversations = metadata.get("total_conversations", 0)
        
        if not latest_summary:
            return "Không có cuộc hội thoại tương tự từ trước."
        
        print(f"📚 Retrieved overall summary from {total_conversations} conversations")
        return f"Tóm tắt từ {total_conversations} cuộc hội thoại trước:\n{latest_summary}"
    
    except Exception as e:
        print(f"❌ Error retrieving from Pinecone: {e}")
        return "Không có cuộc hội thoại tương tự từ trước."

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
def gen_answer(user_input, current_location, conversation_history=None):
    """Main chat logic with context injection, conversation history, and RAG from Pinecone."""
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
    
    # Retrieve similar conversations from Pinecone
    similar_conversations = retrieve_similar_conversations(user_input)
    print(f"📚 Retrieved similar conversations:\n{similar_conversations}")

    # Compose context
    context += f"Những nhà hàng liên quan ở gần đó:\n{nearby_restaurants}\n\nNgười dùng hỏi: {user_input}"
    print(f"🗒️ Context for LLM:\n{context}")
    
    # Use LangChain if available, otherwise fallback to OpenAI client
    if llm and prompt_template:
        # Use LangChain prompt template
        formatted_prompt = prompt_template.invoke({
            "similar_conversations": similar_conversations,
            "context": context
        })

        # Generate response using LangChain
        response = llm.invoke(formatted_prompt)
        return response.content.strip()
    else:
        # Fallback to original OpenAI client
        print("⚠️ Using fallback OpenAI client (LangChain not available)")
        messages = [system_message]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": context})
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        messages=messages,
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
    print(f"📚 Conversation history length: {len(message.history)}")
    try:
        answer = gen_answer(message.text, message.location, message.history)
        print(f"✅ Generated answer successfully")
        # Save conversation to Pinecone if there's meaningful history (at least 2 exchanges)
        if len(message.history) >= 2:
            # Convert Message objects to dicts
            full_conversation = [
                {"role": msg.role, "content": msg.content} for msg in message.history
            ]
            # Add current exchange
            full_conversation.extend([
                {"role": "user", "content": message.text},
                {"role": "assistant", "content": answer}
            ])
            save_conversation_to_pinecone(full_conversation, message.location)
        return {"message": answer}
    except Exception as e:
        print(f"❌ Error generating answer: {str(e)}")
        raise

@app.post("/location")
async def reverse_geocode(location: Location):
    return get_location_from_coordinates(location.lat, location.lon)

@app.get("/search-history")
async def search_conversation_history(query: str, limit: int = 5):
    """Search similar conversations from Pinecone using semantic search."""
    try:
        # Generate embedding for the search query using new embedding model
        embedding_response = embedding_client.embeddings.create(
            model=os.getenv("AZURE_EMBEDDING_MODEL"),
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Search in Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True
        )
        
        # Format results
        conversations = []
        for match in results.matches:
            conversations.append({
                "score": match.score,
                "summary": match.metadata.get("summary"),
                "location": match.metadata.get("location"),
                "timestamp": match.metadata.get("timestamp"),
                "message_count": match.metadata.get("message_count")
            })
        
        print(f"🔍 Found {len(conversations)} similar conversations")
        return {"results": conversations}
        
    except Exception as e:
        print(f"❌ Error searching Pinecone: {e}")
        return {"error": str(e), "results": []}


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
