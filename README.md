## AI Hỏi Chatbot

A chatbot application with a Python FastAPI backend and a React Native (Expo) frontend.

## Project structure

```
ai_hoi/
├── frontend/        # Expo React Native frontend (App.js)
├── backend/         # Python FastAPI backend (main.py)
└── README.md
```

## Prerequisites

- Node.js (v16+ recommended)
- npm or yarn
- Python (v3.8+)

## Setup

Frontend (Expo)

1. Open a terminal and go to the frontend folder:

   ```powershell
   cd frontend
   ```

2. Install JS dependencies:

   ```powershell
   npm install
   ```

Note: the frontend now includes additional packages to improve web and UI support (e.g. `react-native-paper`, `@expo/vector-icons`). If you run into missing peer dependencies when starting Expo on web, run `npx expo install` as prompted by the Expo CLI.

3. Start Expo:

   ```powershell
   npm run start
   ```

Notes on backend URL from mobile:

- The app uses `http://10.0.2.2:8000` by default which works for Android emulators (maps to host machine).
- For iOS simulator, use `http://localhost:8000`.
- For a physical device, replace the backend URL in `frontend/App.js` with your machine IP, e.g. `http://192.168.1.100:8000`.

See `frontend/README.md` for more details about running the Expo app.

Frontend quick start (copied here)

1. Install dependencies (requires Node.js and npm/yarn):

   ```powershell
   cd frontend
   npm install
   ```

2. Start Expo:

   ```powershell
   npm run start
   ```

3. Run on device/emulator:

   - Web: open the web option in the Expo DevTools
   - Android emulator: npm run android (NEED ANDROID STUDIO TO BE INSTALLED)
   - iOS simulator: npm run ios (macOS only)

Backend URL

The app by default uses `http://10.0.2.2:8000` as the backend address (Android emulator loopback to host). If you're using a physical device, replace `DEFAULT_BACKEND` in `frontend/api.js` with your machine's local network IP (for example: `http://192.168.1.100:8000`).

CORS

Ensure the FastAPI backend has CORS enabled for the origin the Expo app uses (Expo web uses `http://localhost:19006` by default). See the backend `main.py` for CORS middleware configuration.

Backend (FastAPI)

1. Open a terminal and go to the backend folder:

   ```powershell
   cd backend
   ```

2. (Optional) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv; .venv\Scripts\activate
   ```

3. Install Python dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create a `.env` file in `backend/` with the following values (fill your keys):

   ```text
   AZURE_OPENAI_ENDPOINT=https://...
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_MODEL_NAME=your-model
   ```

5. Start the server:

   ```powershell
   uvicorn main:app --reload
   ```

The backend will be available at `http://localhost:8000`.

## API

- POST /chat — accepts JSON { "message": "..." } and returns { "message": "..." } from the bot.

## Development notes

- Frontend structure (refactored for reuse/maintenance):

   - `frontend/App.js` — main app wiring and state
   - `frontend/components/MessageList.js` — message list wrapper (uses FlatList)
   - `frontend/components/MessageBubble.js` — single message bubble component
   - `frontend/components/MessageInput.js` — input area + send button
   - `frontend/api.js` — small API helper for POST /chat

- Adjust the backend URL used in `frontend/api.js` (DEFAULT_BACKEND) when testing on devices or different emulators.
- The backend FastAPI app is in `backend/main.py`.

## Stopping

- Press Ctrl+C in the terminals running Expo and uvicorn.

---

For more frontend-specific tips, see `frontend/README.md`.
