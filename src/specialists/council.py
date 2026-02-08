from .base import Specialist
from typing import Dict, Any


class Plumber(Specialist):
    """
    The Backend Specialist.
    Dual-mode: Node/Express OR Python/FastAPI based on stack_profile.
    """

    def __init__(self):
        super().__init__(
            name="Plumber",
            owned_patterns=[
                # Node patterns
                "server.js",
                "app.js",
                "db/*",
                "models/*",
                "routes/*",
                "controllers/*",
                "middleware/*",
                # Python patterns
                "main.py",
                "app.py",
                "routers/*",
                "schemas/*",
                "services/*",
                "database/*",
                "core/*",
                "api/*",
            ],
            requires=["Professor"],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        skill_context = shared_context.get(
            "SKILL_DATA", "No additional skill data provided."
        )
        stack = shared_context.get("stack_profile", {})
        backend = stack.get("backend", "node/express")

        if backend.startswith("python/"):
            framework = backend.split("/")[1]  # fastapi, flask, django
            code_prompt = f"""
            {self.ANTI_GASLIGHTING_PROMPT}

            Generate a HIGH-FIDELITY, INDUSTRIAL-GRADE Python backend implementation for: {file_path}
            Framework: {framework.upper()}
            
            Specs Context:
            {specs[:50000]}
            
            DOMAIN EXPERTISE (SKILL BATTERY):
            {skill_context}
            
            CRITICAL REQUIREMENTS:
            - NO SKELETAL CODE. Implement FULL logic for all routes.
            - Use {framework} with proper async patterns.
            - **FastAPI specifics**: Use Pydantic v2 models for request/response validation.
            - **API Docs**: Do NOT disable docs_url or redoc_url. Swagger UI at /docs and ReDoc at /redoc must remain active (FastAPI default).
            - **Health Endpoint**: MUST include a GET /health endpoint returning JSON with: status, uptime_seconds, database_connected (bool), version, stack info.
            - **Database**: Use SQLAlchemy 2.0 async with proper session management.
            - **Dynamic Port**: Use `int(os.environ.get("PORT", 8000))` for uvicorn.
            - Error Handling: Use proper HTTP exception classes with detail messages.
            - Type hints on ALL function signatures.
            - Professional docstrings explaining complex logic.
            - Use python-dotenv for environment configuration.
            - Use bcrypt/passlib for password hashing, python-jose for JWT.
            """
            system = f"You are the {self.name}, a Python backend expert. Output ONLY Python code. Use {framework} patterns."
        else:
            code_prompt = f"""
            {self.ANTI_GASLIGHTING_PROMPT}

            Generate a HIGH-FIDELITY, INDUSTRIAL-GRADE backend implementation for: {file_path}
            Expertises: Node.js, Express, PostgreSQL, Auth, Media Processing, Auditing logic.
            
            Specs Context:
            {specs[:50000]}
            
            DOMAIN EXPERTISE (SKILL BATTERY):
            {skill_context}
            
            CRITICAL REQUIREMENTS:
            - NO SKELETAL CODE. Implement FULL logic for all routes.
            - **Dynamic Port**: MUST use `process.env.PORT || 3000` for the listener.
            - **Health Endpoint**: MUST include a GET /health or /api/health endpoint returning JSON with: status, uptime, database_connected, version.
            - Data Validation: Use Zod or similar for all request bodies.
            - Error Handling: Implement robust try-catch blocks with helpful error messages.
            - Professional Comments: Explain complex logic for high-fidelity auditing.
            """
            system = f"You are the {self.name}. Output ONLY code. Provide EXHAUSTIVE, production-ready logic."

        return await worker.generate(code_prompt, system_prompt=system)


class Sculptor(Specialist):
    """
    The Frontend Specialist.
    Supports: React (default), HTMX, or None (API-only).
    """

    def __init__(self):
        super().__init__(
            name="Sculptor",
            owned_patterns=[
                "src/App.tsx",
                "src/components/*",
                "src/pages/*",
                "src/views/*",
                "src/index.css",
                "index.html",
                "src/main.tsx",
                "src/renderers/*",
                # HTMX patterns
                "templates/*",
                "static/*",
            ],
            requires=["Professor"],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        stack = shared_context.get("stack_profile", {})
        frontend = stack.get("frontend", "react")

        # Skip generation if no frontend
        if frontend == "none":
            return ""

        # HTMX mode
        if frontend == "htmx":
            return await self._generate_htmx(file_path, specs, shared_context, worker)

        # React mode (default)
        return await self._generate_react(file_path, specs, shared_context, worker)

    async def _generate_react(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        if file_path == "index.html":
            prompt = """
            Generate a SOTA, PREMIUM index.html for a Vite + React project.
            - MUST include <div id="root"></div>.
            - MUST include <script type="module" src="/src/main.tsx"></script>.
            - Include Google Fonts (Inter, Outfit, or Poppins).
            - Set base background color to a sleek dark theme (#09090b).
            """
        elif file_path == "src/main.tsx":
            prompt = """
            Generate React 18 /src/main.tsx.
            - MUST import React, { StrictMode }.
            - MUST import { createRoot } from 'react-dom/client'.
            - MUST import App from './App'.
            - MUST import './index.css'.
            - Render <App /> with a <StrictMode> wrapper.
            """
        elif file_path == "src/App.tsx":
            prompt = f"""
            Generate the SOTA HIGH-FIDELITY shell for the application: /src/App.tsx.
            - Use Framer Motion for page transitions.
            - Implement a GORGEOUS Responsive Navbar with Glassmorphism (backdrop-blur).
            - Routing: use react-router-dom for all pages defined in the specs.
            - Design: Dark mode by default, high-contrast, premium typography.
            - Context: {specs[:50000]}
            """
        else:
            prompt = f"""
            Generate a STUNNING, HIGH-FIDELITY React component: {file_path}
            Expertises: Tailwind CSS, Framer Motion, Glassmorphism, Micro-animations.
            
            Specs Context: {specs[:50000]}
            
            DOMAIN EXPERTISE (SKILL BATTERY):
            {shared_context.get("SKILL_DATA", "")}
            
            {self.ANTI_GASLIGHTING_PROMPT}

            AESTHETIC PROTOCOLS:
            - **Glassmorphism**: Use `bg-white/10 backdrop-blur-md border border-white/20`.
            - **Typography**: Large, bold headings, clean sans-serif (Inter/Outfit).
            - **Interactivity**: Every button must have a hover scale effect.
            - **Content Density**: DO NOT generate skeleton loaders. Include dense, realistic content.
            - **Visuals**: Use Lucide-React icons for every list item/button.
            - **Grid/Layout**: Use complex Bento Grid or modern flex layouts.
            """

        return await worker.generate(
            prompt,
            system_prompt=f"You are the {self.name}, a world-class UI/UX designer and frontend engineer. Use Tailwind CSS for all styling.",
        )

    async def _generate_htmx(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate a HIGH-FIDELITY HTMX template for: {file_path}
        Expertises: Jinja2 templates, HTMX attributes (hx-get, hx-post, hx-swap, hx-trigger), Alpine.js for client state.
        
        Specs Context: {specs[:50000]}
        
        CRITICAL REQUIREMENTS:
        - Use Jinja2 template syntax with template inheritance (extends base.html).
        - Use HTMX for all dynamic interactions (no page reloads).
        - Use Alpine.js (x-data, x-show, x-on) for client-side reactivity.
        - Tailwind CSS for styling.
        - Mobile-first responsive design.
        - NO React, NO JSX, NO JavaScript frameworks.
        """
        return await worker.generate(
            prompt,
            system_prompt=f"You are the {self.name}. Generate HTMX + Jinja2 templates. Output ONLY template code.",
        )


class Librarian(Specialist):
    """
    The Documentation Specialist.
    Expert in technical writing and API documentation.
    Requires: Plumber (to know what APIs were built).
    """

    def __init__(self):
        super().__init__(
            name="Librarian",
            owned_patterns=["README.md", "docs/*"],
            requires=["Plumber"],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        stack = shared_context.get("stack_profile", {})
        backend = stack.get("backend", "node/express")

        # The Librarian reads the Plumber's output to ensure 100% accuracy
        plumber_output = shared_context.get("Plumber", {})
        # Find the main backend file based on stack
        if backend.startswith("python/"):
            backend_entry = "main.py"
            install_cmd = "pip install -r requirements.txt"
            run_cmd = "uvicorn main:app --reload"
        else:
            backend_entry = "server.js"
            install_cmd = "npm install"
            run_cmd = "npm run dev"

        backend_code = plumber_output.get(backend_entry, f"No {backend_entry} found.")

        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate an EXHAUSTIVE, multi-section README.md for this project.
        Expertise: Technical Writing, API Documentation, Professional Markdown.
        
        Tech Stack: {backend} backend
        
        Specs Summary: {specs[:50000]}
        
        INPUT - ACTUAL BACKEND CODE (use for route documentation):
        {backend_code[:2500]}
        
        MUST INCLUDE THESE SECTIONS:
        1. # Project Title (Industrial & Descriptive)
        2. ## Overview (What does this app do?)
        3. ## Features (List at least 5 key features based on Specs)
        4. ## Tech Stack (Frontend/Backend/DB)
        5. ## API Reference (Document every route found in the provided code)
        6. ## Database Schema (Document the SQL structure)
        7. ## Getting Started (Step-by-step install and run)
           - Install: `{install_cmd}`
           - Run: `{run_cmd}`
        
        CRITICAL: Do NOT just output SQL. The output must be valid Markdown text. 
        Aim for a long, high-fidelity file.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY Markdown."
        )


class Professor(Specialist):
    """
    The Skill Battery Specialist.
    Loads specialized domain knowledge from the local /skills directory.
    """

    def __init__(self):
        super().__init__(
            name="Professor",
            owned_patterns=["skills/*"],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        import os

        # 1. Analyze Specs to find the best skill
        skill_selection_prompt = f"""
        Analyze these application specs and identify the most relevant domain.
        Available local skills: {os.listdir("skills") if os.path.exists("skills") else "None"}
        
        Specs: {specs[:50000]}
        
        Output ONLY the filename of the best matching skill or "None".
        """

        skill_filename = await worker.generate(
            skill_selection_prompt,
            system_prompt="You are the Skill Selector. Output ONLY the filename.",
        )
        skill_filename = skill_filename.strip().strip('"').strip("'")

        skill_content = ""
        if (
            skill_filename
            and skill_filename != "None"
            and os.path.exists(f"skills/{skill_filename}")
        ):
            with open(f"skills/{skill_filename}", "r", encoding="utf-8") as f:
                skill_content = f.read()
            # Inject into shared context for all specialists to see
            shared_context["SKILL_DATA"] = skill_content
            return f"Successfully loaded skill: {skill_filename}"

        return "No specific skill loaded."


class Registrar(Specialist):
    """
    The Infrastructure Specialist.
    Dual-mode: generates package.json/vite.config for Node, or
    requirements.txt/pyproject.toml for Python. Both for hybrid stacks.
    """

    def __init__(self):
        super().__init__(
            name="Registrar",
            owned_patterns=[
                "package.json",
                "vite.config.ts",
                ".env*",
                "requirements.txt",
                "pyproject.toml",
                "Dockerfile",
                "docker-compose.yml",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        stack = shared_context.get("stack_profile", {})
        backend = stack.get("backend", "node/express")
        frontend = stack.get("frontend", "react")
        database = stack.get("database", "sqlite")

        if file_path == "requirements.txt":
            prompt = self._python_requirements_prompt(backend, database)
        elif file_path == "pyproject.toml":
            prompt = self._pyproject_prompt(specs)
        elif file_path == "package.json":
            if backend.startswith("python/"):
                # Hybrid: Python backend + React frontend
                prompt = self._frontend_only_package_json_prompt()
            else:
                prompt = self._fullstack_node_package_json_prompt()
        elif file_path == "vite.config.ts":
            backend_port = "8000" if backend.startswith("python/") else "3000"
            prompt = f"""
            Generate a standard vite.config.ts for a React project using @vitejs/plugin-react.
            - Use the 'vite' and '@vitejs/plugin-react' imports.
            - Configuration must include the React plugin.
            - Ensure it's compatible with a flat project structure where package.json is at root.
            - DISABLE middlewareMode. (Standard dev server).
            - **Dynamic Ports**: 
                - Use `process.env.VITE_PORT || 5173` for the dev server port.
                - Add a PROXY for '/api' pointing to `http://localhost:${{process.env.PORT || {backend_port}}}`.
            """
        elif file_path == "Dockerfile":
            if backend.startswith("python/"):
                prompt = f"""
                Generate a production Dockerfile for a Python {backend.split('/')[1]} application.
                - Use python:3.12-slim as base.
                - Copy requirements.txt and install deps first (layer caching).
                - Copy source code.
                - Expose port 8000.
                - CMD: uvicorn main:app --host 0.0.0.0 --port 8000
                - Use non-root user.
                """
            else:
                prompt = """
                Generate a production Dockerfile for a Node.js Express application.
                - Use node:20-slim as base.
                - Copy package.json and install deps first (layer caching).
                - Copy source code.
                - Expose port 3000.
                - CMD: node server.js
                - Use non-root user.
                """
        else:
            prompt = f"""
            {self.ANTI_GASLIGHTING_PROMPT}
            Generate infrastructure file: {file_path}
            Stack: backend={backend}, frontend={frontend}, database={database}
            """

        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code/config."
        )

    @staticmethod
    def _python_requirements_prompt(backend: str, database: str) -> str:
        framework = backend.split("/")[1] if "/" in backend else "fastapi"
        db_deps = {
            "postgresql": "psycopg2-binary\nasyncpg",
            "mysql": "pymysql\naiomysql",
            "mongodb": "motor\npymongo",
            "sqlite": "aiosqlite",
        }
        db_pkgs = db_deps.get(database, "aiosqlite")

        if framework == "fastapi":
            return f"""
            Generate a requirements.txt for a production FastAPI application.
            Include these packages (latest versions, no pinning):
            
            # Core
            fastapi
            uvicorn[standard]
            pydantic>=2.0
            pydantic-settings
            python-dotenv
            
            # Database
            sqlalchemy>=2.0
            alembic
            {db_pkgs}
            
            # Auth
            python-jose[cryptography]
            passlib[bcrypt]
            python-multipart
            
            # HTTP
            httpx
            
            # Utils
            python-dateutil
            
            Output ONLY the requirements.txt content, one package per line.
            """
        elif framework == "flask":
            return f"""
            Generate a requirements.txt for a production Flask application.
            Include: flask, flask-cors, flask-sqlalchemy, flask-migrate,
            marshmallow, python-dotenv, {db_pkgs}, gunicorn.
            Output ONLY the requirements.txt content.
            """
        else:
            return f"""
            Generate a requirements.txt for a production Django application.
            Include: django>=5.0, djangorestframework, django-cors-headers,
            python-dotenv, {db_pkgs}, gunicorn.
            Output ONLY the requirements.txt content.
            """

    @staticmethod
    def _pyproject_prompt(specs: str) -> str:
        return f"""
        Generate a pyproject.toml for a Python project based on these specs.
        Use modern Python packaging (PEP 621).
        Include [project] metadata, [build-system] with setuptools.
        Specs: {specs[:5000]}
        Output ONLY the pyproject.toml content.
        """

    @staticmethod
    def _fullstack_node_package_json_prompt() -> str:
        return """
        Generate a production-ready package.json for a Full Stack React + Express app.
        
        CRITICAL SCRIPTS:
        "start": "node server.js",
        "server": "nodemon server.js",
        "client": "vite",
        "dev": "concurrently \\"npm run server\\" \\"npm run client\\""
        
        REQUIRED DEPENDENCIES (Use '*' for versions):
        - CORE: express, cors, dotenv, bcryptjs, jsonwebtoken, sequelize, pg, pg-hstore, morgan, helmet
        - UI: react, react-dom, react-router-dom, axios, framer-motion, lucide-react, clsx, tailwind-merge
        - FORMS: react-hook-form, zod
        - CHARTS: recharts, d3
        - UTILS: date-fns, lodash, multer, node-cron, uuid
        - STATE: @reduxjs/toolkit, react-redux
        
        REQUIRED DEV DEPENDENCIES:
        - vite, @vitejs/plugin-react, concurrently, nodemon, typescript
        """

    @staticmethod
    def _frontend_only_package_json_prompt() -> str:
        return """
        Generate a package.json for a React frontend (Vite) that connects to a Python backend via API proxy.
        
        CRITICAL SCRIPTS:
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
        
        REQUIRED DEPENDENCIES (Use '*' for versions):
        - UI: react, react-dom, react-router-dom, axios, framer-motion, lucide-react, clsx, tailwind-merge
        - FORMS: react-hook-form, zod
        - CHARTS: recharts
        - STATE: @reduxjs/toolkit, react-redux
        
        REQUIRED DEV DEPENDENCIES:
        - vite, @vitejs/plugin-react, typescript, @types/react, @types/react-dom, tailwindcss, postcss, autoprefixer
        
        No Express, no backend deps. This is frontend-only.
        """


class Nervos(Specialist):
    """
    The System Heartbeat & Plugin Specialist.
    Expert in App lifecycle, Messaging Connectors (WhatsApp/Email), and Plugin Architecture.
    """

    def __init__(self):
        super().__init__(
            name="Nervos",
            owned_patterns=[
                "src/services/nervos/*",
                "src/plugins/*",
                "src/hooks/useHeartbeat.ts",
                "src/components/StatusMonitor.tsx",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate system health or connector logic for: {file_path}
        Expertises: Heartbeat monitoring, Messaging APIs (WhatsApp/Nodemailer/Telegram), Plugin Systems (Registry/Loading), WebSockets.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of robust service connectors.
        - Proper plugin lifecycle management.
        - Efficient status monitoring (heartbeat) logic.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class Auditor(Specialist):
    """
    The MS Office & Audit Specialist.
    Expert in Excel, Word, and "Cook my books" data validation.
    """

    def __init__(self):
        super().__init__(
            name="Auditor",
            owned_patterns=[
                "src/services/audit/*",
                "src/components/ExcelViewer.tsx",
                "src/hooks/useAudit.ts",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate Office file processing or auditing logic for: {file_path}
        Expertises: MS Excel (XLSX/ExcelJS), Word (DocxTemplater), Data Validation, Error checking in formulas, "Cook my books" auditing patterns.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of high-fidelity Excel/Word parsing and auditing.
        - Efficient processing of complex spreadsheet formulas.
        - Clear error reporting and validation summaries.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class Raggy(Specialist):
    """
    The RAG & Vector Search Specialist.
    Expert in Embeddings, Vector Stores, and Retrieval logic.
    """

    def __init__(self):
        super().__init__(
            name="Raggy",
            owned_patterns=[
                "src/services/rag/*",
                "src/hooks/useRag.ts",
                "src/components/ChatWithDocs.tsx",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate RAG/Vector search logic for: {file_path}
        Expertises: OpenAI/Gemini Embeddings, Vector Databases (Pinecone, ChromaDB, HNSWLIB), Semantic Search, Chunking strategies, LangChain.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of vector embedding generation and storage logic.
        - Efficient retrieval patterns (similarity search).
        - Proper integration with Chat UIs for context-augmented generation.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class WebFinder(Specialist):
    """
    The Web Scraping & Embedding Specialist.
    Expert in Wikipedia API, TVTropes scraping, and content extraction.
    """

    def __init__(self):
        super().__init__(
            name="WebFinder",
            owned_patterns=[
                "src/services/web/*",
                "src/hooks/useWebFinder.ts",
                "src/components/WebEmbed.tsx",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate web-scraping or embedding logic for: {file_path}
        Expertises: Wikipedia API, RSS/Atom parsing, Cheerio, TVTropes-specific extraction patterns, iframe safe-embedding.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of efficient content fetchers and parsers.
        - Robust error handling for external site changes.
        - Sanitization of extracted HTML/content.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class Archivist(Specialist):
    """
    The Digital Book & Calibre Specialist.
    Expert in ePub, PDF, and Mobi parsing.
    """

    def __init__(self):
        super().__init__(
            name="Archivist",
            owned_patterns=[
                "src/services/library/*",
                "src/components/Reader.tsx",
                "src/hooks/useLibrary.ts",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate library/book extraction logic for: {file_path}
        Expertises: Calibre library structure, EPUB/PDF/Mobi parsing (epub-parser, pdf-parse), text extraction, and metadata management.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of high-fidelity document parsers.
        - Efficient processing of large binary files (streams).
        - Clean representation of book metadata and content.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class Maestro(Specialist):
    """
    The Music & Audio Specialist.
    Expert in Suno/Udio API patterns, Tone.js, and Web Audio.
    """

    def __init__(self):
        super().__init__(
            name="Maestro",
            owned_patterns=[
                "src/audio/*",
                "src/components/AudioPlayer.tsx",
                "src/hooks/useAudio.ts",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate music/audio logic for: {file_path}
        Expertises: Tone.js, Web Audio API, Suno/Udio API integration patterns, MIDI generation, FOSS audio tools.
        
        Specs Context: {specs[:50000]}
        
        REQUIREMENTS:
        - Implementation of audio synthesis, generative music, or AI music client logic.
        - Proper handling of AudioContext and browser autoplay policies.
        - High-quality, functional code only.
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )


class Generalist(Specialist):
    """
    The Catch-all Specialist.
    Handles any file not claimed by others.
    """

    def __init__(self):
        super().__init__(
            name="Generalist",
            owned_patterns=["*"],
            requires=[
                "Sculptor",
                "Plumber",
                "Librarian",
                "Registrar",
                "Maestro",
                "WebFinder",
                "Archivist",
                "Raggy",
                "Nervos",
                "Auditor",
                "Professor",
            ],
        )

    async def generate(
        self, file_path: str, specs: str, shared_context: Dict[str, Any], worker: Any
    ) -> str:
        prompt = f"""
        {self.ANTI_GASLIGHTING_PROMPT}

        Generate code for: {file_path}. Based on specs: {specs[:50000]}
        """
        return await worker.generate(
            prompt, system_prompt=f"You are the {self.name}. Output ONLY code."
        )
