# Backend Manual Testing Guide

The backend (Chunk 6) is fully implemented! To manually test the entire orchestrator, tool execution, and API endpoints, follow this step-by-step guide.

## Step 1: Update the Groq API Key

Currently, the `GROQ_API_KEY` in `backend/.env` is a placeholder, which causes the `/chat` endpoint to return a 401 error when the AI orchestrator tries to run.

1. Open `backend/.env`.
2. Find the line: `GROQ_API_KEY=your_groq_api_key_here`.
3. Replace `your_groq_api_key_here` with your actual Groq API key.
4. Save the file.

## Step 2: Start the FastAPI Server

Open your terminal (PowerShell) and start the backend server:

```powershell
& ".\venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
You should see: `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

## Step 3: Use the CLI Tester

We have built a dedicated test script that exercises all endpoints sequentially. While the server is running, open a **new** terminal window and run:

```powershell
& ".\venv\Scripts\python.exe" backend\test_cli.py
```

### What this script tests:
1. **`GET /health`**: Confirms the database and embedding models are reachable.
2. **`POST /chat`**: Sends a prompt ("How many customers do we have in total?"). 
    - *Expected behavior*: The LLM should route this to the `query_customer_db` tool, execute the SQL, and return a final answer.
3. **`POST /chat` (Follow-up)**: Sends a second prompt in the same conversation ("How many of them have open tickets?").
    - *Expected behavior*: The LLM should remember the context, query the DB again, and answer.
4. **`GET /conversations/{id}`**: Fetches the chat history to verify persistence.
5. **`GET /admin/logs`**: Verifies that the tool calls and latencies were successfully logged for the dashboard.

## Step 4: (Optional) Test Endpoints Manually via Curl/Postman

If you want to poke at the API directly, here are the commands you can use in PowerShell:

### Health Check
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health | ConvertTo-Json
```

### Send a Chat Message
```powershell
$body = @{
    message = "Check if there are any open issues for 'auth'"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method POST -Body $body -ContentType 'application/json'
```

### View Admin Logs
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/admin/logs?limit=5 | ConvertTo-Json
```

## Congratulations!
Once your API key is in place and the `test_cli.py` script succeeds without errors, your backend is 100% complete and ready for the Frontend (Chunk 7).
