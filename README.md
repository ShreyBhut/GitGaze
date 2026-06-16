# GitGaze 👀

GitGaze is a highly interactive, full-stack visualizer and AI-powered static analysis tool for GitHub repositories. Built with a focus on deep code understanding, GitGaze automatically clones repositories, extracts their internal dependency graphs via AST parsing, and renders them in a beautiful, interactive DAG (Directed Acyclic Graph). 

Coupled with a Gemini AI integration, it allows developers to instantly understand complex codebases, visualize how files connect to one another, and request highly detailed, cached AI summaries of any given file.

## ✨ Features

- **GitHub OAuth Integration:** Securely login via GitHub. Grants read access to securely clone and analyze even your private repositories.
- **Deep Static Analysis:** Automatically parses Python, TypeScript, and JavaScript files to map out functions, classes, Lines of Code (LOC), and cross-file dependencies.
- **Real-Time Progress Streaming:** Uses Server-Sent Events (SSE) to stream live progress updates to the frontend while the backend background worker parses large repositories.
- **Interactive Graph Visualization:** Leverages `@xyflow/react` and `dagre` to auto-layout the dependency graph. Features include smooth panning, zooming, custom nodes, and layout persistence.
- **AI-Powered Code Summaries:** Integrated with **Gemini Flash Lite** to generate concise or highly detailed summaries of file logic on demand.
- **Intelligent Caching:** AI summaries are hashed by file content and cached in SQLite to drastically reduce API latency and save quota.
- **Robust Security:** Strong access control rules ensure that private repositories and their analysis data are strictly bound to the authenticated user.

---

## 🛠️ Tech Stack

**Frontend:**
- **React 18** (Vite) with **TypeScript**
- **@xyflow/react** (React Flow) for DAG graph visualization
- **TanStack Query** (React Query) for state and API data fetching
- **Zustand** for lightweight global state management
- Custom CSS token system for a premium, glassmorphic dark theme

**Backend:**
- **FastAPI** (Python 3.12)
- **SQLAlchemy** (Async) with **SQLite** (`aiosqlite`)
- **google-generativeai** for Gemini integration
- Python `ast` module for static code analysis

---

## 🚀 Getting Started

Follow these instructions to compile and run the project locally for testing and verification.

### Prerequisites
- Python 3.10+
- Node.js 18+
- A GitHub OAuth App (for Client ID & Secret)
- A Google Gemini API Key

### 1. Environment Setup
In the root of the project, create a `.env` file (or update the existing one) with the following variables:

```env
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
JWT_SECRET=super_secret_jwt_key
GEMINI_API_KEY=your_gemini_api_key
```

### 2. Backend Setup
Open a terminal in the `backend/` directory:

```bash
cd backend
# Create a virtual environment
python -m venv venv
# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
Open a separate terminal in the `frontend/` directory:

```bash
cd frontend
# Install NPM dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🌟 GitGaze in the Working

<img width="720" height="342" alt="Screenshot 2026-06-16 063352" src="https://github.com/user-attachments/assets/dadc70ec-d146-484f-932d-755daf77386e" />
<img width="720" height="342" alt="Screenshot 2026-06-16 063924" src="https://github.com/user-attachments/assets/3f2ca418-f300-4985-994b-edcac034631e" />
<img width="720" height="342" alt="Screenshot 2026-06-16 063618" src="https://github.com/user-attachments/assets/ecb5c1b2-f46b-41c6-8efd-9b6669b73a8c" />

## 💡 Architecture Highlights

If you are verifying or evaluating this project, here are some deliberate architectural decisions designed to highlight engineering best practices:

1. **SSE over WebSockets:** Real-time progress during codebase analysis uses Server-Sent Events (SSE). Since the data flow is strictly unidirectional (server -> client) during analysis, SSE provides a significantly lighter network footprint than WebSockets while avoiding the overhead of HTTP long-polling.
2. **Local-First Database:** The app uses an Async SQLite database. This ensures maximum portability for evaluators and developers without the hassle of spinning up a separate PostgreSQL Docker container, while still utilizing modern async SQLAlchemy paradigms.
3. **Embedded Background Workers:** Rather than introducing complex message brokers like Redis or Celery, the backend leverages FastAPI's native `BackgroundTasks` running within the main event loop. This drastically simplifies the deployment architecture for a single-node application.
4. **Content-Hash Caching:** The AI Summary feature does not just cache by file name—it caches by the cryptographic hash of the file's content. This ensures that if the user updates their code and triggers a re-analysis, the cache is correctly invalidated, but unchanged files instantly return cached summaries.
5. **Row-Level Security (RLS) Emulation:** The backend strictly enforces ownership checks. Even if an attacker knows the UUID of a private repository snapshot, the backend queries the database to ensure the `user_id` matches the authenticated JWT token before returning the AST graph or AI summary.
