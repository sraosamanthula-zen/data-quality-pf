# Agentic AI Data Quality Platform - Copilot Instructions

## Project Overview
This is an Agentic AI-powered data quality platform designed to handle PnP data files with specific focus on:
- **UC1**: Incomplete/Sparse Data Files Detection and Correction
- **UC4**: Duplicate Records Detection and Resolution

## Technology Stack
- **Backend**: Python 3.13, FastAPI, Pydantic, SQLAlchemy, SQLite
- **AI/ML**: LangGraph, LangChain for agentic workflows
- **Frontend**: React JS, Next JS
- **Database**: SQLite for job management and processing state

## Project Structure
- `backend/`: FastAPI application with agentic workflows
- `frontend/`: React/Next.js dashboard interface  
- `agents/`: Individual AI agents for data quality tasks
- `database/`: SQLite schema and models
- `config/`: Configuration files and environment variables
- `tests/`: Unit and integration tests
- `docs/`: API documentation and user guides

## Key Features to Implement
1. File upload and validation system
2. Agentic workflow orchestration (UC1 & UC4)
3. Job scheduling and monitoring
4. Real-time dashboard with status indicators
5. Data quality metrics and reporting
6. Audit trail and traceability

## Development Guidelines
- Follow FastAPI best practices for async operations
- Implement proper error handling and logging
- Use Pydantic models for data validation
- Create modular, testable agentic workflows
- Maintain clean separation between agents and business logic
