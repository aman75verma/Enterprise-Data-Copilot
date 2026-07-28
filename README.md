# Enterprise Data Copilot

Enterprise Data Copilot is an internal support assistant powered by **Groq** and the **Model Context Protocol (MCP)**. It provides a conversational AI interface capable of executing complex tools and database queries securely, all wrapped in a modern, dynamic React frontend.

**🌐 Live Demo:** [https://enterprise-data-copilot-1.onrender.com/](https://enterprise-data-copilot-1.onrender.com/)

---

## ✨ Features

- **Agentic AI Assistant**: Chat with an AI that can intelligently call internal tools to query databases, search documentation, and check issue trackers.
- **Model Context Protocol (MCP)**: Utilizes the emerging MCP standard to securely isolate tool execution in a subprocess.
- **Dual-Path Latency Benchmarking**: Includes an Admin Dashboard to compare the execution speed of direct Python tool calls vs. MCP-based calls in real-time.
- **Dynamic Frontend**: A beautiful, highly responsive Single Page Application built with React, Vite, and Lucide Icons.
- **Robust Backend**: A fast and asynchronous Python backend powered by FastAPI.
- **Automated Database Initialization**: Uses PostgreSQL with automated schema generation on startup, making it incredibly easy to deploy to cloud providers.
- **Production Ready**: Fully containerized with multi-stage Docker builds and an Nginx proxy.

---

## 🚀 Getting Started

You can run this application locally using either the pre-built Docker images from Docker Hub (easiest) or by building it directly from the source code.

### Option A: Run via Docker Hub (No Building Required)

If you just want to run the app quickly without compiling code, you can use the pre-built images.

1. Create a `docker-compose.yml` file anywhere on your machine:
   ```yaml
   services:
     postgres:
       image: pgvector/pgvector:pg16
       environment:
         POSTGRES_DB: copilot_db
         POSTGRES_USER: copilot
         POSTGRES_PASSWORD: copilot_pass
       ports:
         - "5433:5432"
         
     backend:
       image: amanverma75/copilot-backend:latest
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://copilot:copilot_pass@postgres:5432/copilot_db
         - GROQ_API_KEY=${GROQ_API_KEY}
         
     frontend:
       image: amanverma75/copilot-frontend:latest
       ports:
         - "80:80"
       depends_on:
         - backend
   ```
2. Create a `.env` file in the same directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. Run the application:
   ```bash
   docker-compose up -d
   ```
4. Open `http://localhost` in your browser.

---

### Option B: Build from Source (GitHub)

If you want to modify the code or contribute to the project:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/amanverma75/Enterprise-Data-Copilot.git
   cd Enterprise-Data-Copilot
   ```

2. **Set up your environment variables:**
   Create a `.env` file in the root directory (or in the `backend/` directory):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Build and start the containers:**
   ```bash
   docker-compose up --build -d
   ```

4. **Verify the deployment:**
   - Frontend: `http://localhost`
   - Backend API Docs: `http://localhost:8000/docs`

---

## 🔌 Using the MCP Server Externally

This project exposes all of its internal tools (database querying, documentation search, etc.) over the **Model Context Protocol (MCP)**. This means you can connect external AI clients (like the Claude Desktop app) directly to this repository!

To use these tools in Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-data-copilot": {
      "command": "python",
      "args": [
        "-m",
        "backend.tools.mcp_server"
      ],
      "env": {
        "DATABASE_URL": "postgresql://copilot:copilot_pass@localhost:5433/copilot_db",
        "PYTHONPATH": "/absolute/path/to/Enterprise-Data-Copilot"
      }
    }
  }
}
```
*(Make sure to update the `PYTHONPATH` to point to the actual folder where you cloned this repository, and adjust `DATABASE_URL` if your database is hosted elsewhere).*

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, React Router, Vanilla CSS
- **Backend**: Python 3.12, FastAPI, Uvicorn, Psycopg2
- **AI & Tools**: Groq API, Model Context Protocol (MCP) SDK
- **Database**: PostgreSQL (with pgvector support)
- **Deployment**: Docker, Docker Compose, Nginx, Render (Cloud)

---

## 📖 Documentation

For a deeper dive into the architecture and deployment strategies, check out our internal guides:
- [Frontend Structure & React Concepts](docs/frontend_structure.md)
- [Production Deployment & Docker Guide](docs/deployment_guide.md)
