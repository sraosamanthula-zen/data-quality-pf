# Quick Setup Guide

## Clone and Setup
```bash
git clone <your-remote-url>
cd Platform
```

## Backend Setup
```bash
cd backend
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Initialize database
uv run python -c "
from database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database initialized')
"

# Start server
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Frontend Setup (Future)
```bash
cd frontend
npm install
npm run dev
```

## Test the API
```bash
# Health check
curl http://localhost:8001/health

# Test async background processing
curl -X POST http://localhost:8001/batch/test-async
```

## Git Repository Status
- ✅ Initial commit completed
- ✅ Virtual environments excluded (.venv, node_modules)
- ✅ 48 files committed (11,115+ lines of code)
- ✅ Comprehensive .gitignore configured
- 📁 Repository size: ~761MB (includes dependencies)

## Ready to Push
To add a remote origin:
```bash
# GitHub example
git remote add origin https://github.com/yourusername/data-quality-platform.git
git branch -M main
git push -u origin main

# GitLab example  
git remote add origin https://gitlab.com/yourusername/data-quality-platform.git
git branch -M main
git push -u origin main
```
