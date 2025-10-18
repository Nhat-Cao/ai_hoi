from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os 
from openai import AzureOpenAI
from dotenv import load_dotenv

# Envỉonment variables & OpenAI Azure Client Setup
load_dotenv()
def is_env_missing(var):
    v = os.getenv(var)
    return v is None or v.strip() == ""

if (
    is_env_missing("AZURE_OPENAI_API_KEY") or
    is_env_missing("AZURE_OPENAI_ENDPOINT") or
    is_env_missing("AZURE_OPENAI_MODEL_NAME")
):
    raise ValueError("Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_MODEL_NAME in your environment variables.")

client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

# Define system message
system_message = {
    "role": "system",
    "content": (
        """
        You are an expert Vietnamese food reviewer. 
        Provide detailed and engaging reviews of various dishes and restaurants.
        Output should be formatted for easy reading.
        """
    )
}
# Function to Generate Instructions
def gen_answer(input):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        messages=[
            system_message,
            {"role": "user", "content": input}
        ],
        max_tokens=1000,
        temperature=0
    )
    return response.choices[0].message.content.strip()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(message: ChatMessage):
    # Here you can add your chatbot logic
    # For now, we'll just echo the message back
    return { "message": gen_answer(message.message) }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)