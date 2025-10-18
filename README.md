# AI Hỏi Chatbot

A chatbot application built with React.js frontend and Python FastAPI backend.

## Project Structure

```
ai_hoi/
├── frontend/           # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js     # Main chat interface
│   │   ├── index.js   # React entry point
│   │   └── index.css  # Styles including Tailwind
│   ├── package.json
│   └── tailwind.config.js
└── backend/           # Python FastAPI backend
    ├── main.py       # FastAPI server
    └── requirements.txt
```

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- npm (comes with Node.js)
- pip (Python package manager)

## Setup Instructions

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Unix or MacOS
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

You'll need to run both the frontend and backend servers.

### Start the Frontend Server

1. In a terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at http://localhost:3000

### Start the Backend Server

1. In a new terminal, navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

The backend API will be available at http://localhost:8000

### API Documentation

- FastAPI automatic documentation is available at: http://localhost:8000/docs
- OpenAPI specification is available at: http://localhost:8000/openapi.json

## Features

- Real-time chat interface
- Clean, responsive UI with Tailwind CSS
- Message history display
- Easy to extend backend chatbot logic

## Development

- Frontend code is in `frontend/src/App.js`
- Backend API is in `backend/main.py`
- Modify the `/chat` endpoint in `main.py` to implement your chatbot logic

## Stopping the Application

To stop the servers:
1. Press `Ctrl+C` in both terminal windows
2. Deactivate the Python virtual environment if you used one:
   ```bash
   deactivate
   ```
