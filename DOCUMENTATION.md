# 🚀 Agentic AI Data Quality Platform - Complete Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation & Setup](#installation--setup)
5. [User Guide](#user-guide)
6. [API Documentation](#api-documentation)
7. [Agent System](#agent-system)
8. [Database Schema](#database-schema)
9. [File Organization](#file-organization)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)
12. [Development Guide](#development-guide)

---

## Overview

The **Agentic AI Data Quality Platform** is a comprehensive solution for automated data quality assessment and processing. It leverages AI agents to analyze CSV files, detect data quality issues, and provide intelligent recommendations for data improvement.

### 🎯 Key Capabilities

- **Automated Data Quality Assessment**: AI-powered analysis of completeness, consistency, and accuracy
- **Duplicate Detection & Removal**: Advanced algorithms to identify and handle duplicate records
- **Batch Processing**: Process multiple files efficiently with queue management
- **Real-time Monitoring**: Live job status tracking and progress monitoring
- **Interactive UI**: Modern, responsive interface with dark/light theme support
- **File Management**: Organized output structure with download capabilities

### 🏗️ Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.13, SQLAlchemy
- **Database**: SQLite with migration support
- **AI Integration**: Azure OpenAI GPT-4
- **Data Processing**: DuckDB, Pandas
- **File Handling**: Multipart uploads, CSV processing

---

## Architecture

### 🏛️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Agents     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (UC1, UC4)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  File Storage   │
                       │ (Local/Cloud)   │
                       └─────────────────┘
```

### 🔄 Data Flow

1. **File Upload**: Users upload CSV files through the web interface
2. **Job Creation**: System creates job records and queues processing
3. **Agent Processing**: AI agents analyze files based on selected criteria
4. **Results Generation**: Processed files and reports are generated
5. **Status Updates**: Real-time job status updates via WebSocket/polling
6. **File Access**: Users can preview and download results

---

## Features

### ✨ Core Features

#### 🎨 **Modern UI/UX**
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark/Light Theme**: Toggle between themes with persistence
- **Card-based Layout**: Intuitive file browser and results display
- **Real-time Updates**: Live job status and progress tracking
- **Download Management**: Icon-based download buttons with file metadata

#### 📁 **File Management**
- **Drag & Drop Upload**: Easy file upload with validation
- **Preview Capability**: View file contents before processing
- **Organized Storage**: Structured output directories with unique naming
- **Batch Operations**: Process multiple files simultaneously
- **File History**: Track processing history and results

#### 🤖 **AI-Powered Analysis**
- **UC1 Agent - Completeness Analysis**:
  - Missing value detection
  - Data type validation
  - Statistical analysis
  - Quality scoring

- **UC4 Agent - Duplicate Detection**:
  - Advanced similarity matching
  - Configurable thresholds
  - Intelligent deduplication
  - Record linking

#### 🔄 **Processing Pipeline**
- **Sequential Processing**: UC1 → UC4 with shared outputs
- **Unique Naming**: Job-based filename generation
- **Error Handling**: Robust error recovery and reporting
- **Progress Tracking**: Detailed job status monitoring

### 🛡️ **Security & Reliability**
- **Input Validation**: Comprehensive file and data validation
- **Error Recovery**: Automatic job recovery on system restart
- **Logging**: Detailed activity logging for debugging
- **Concurrency Control**: Configurable concurrent job limits

---

## Installation & Setup

### 📋 Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **npm**: 9.0 or higher
- **Git**: Latest version

### 🚀 Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/sraosamanthula-zen/data-quality-pf.git
   cd data-quality-pf
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

4. **Database Initialization**
   ```bash
   python migrate_db.py
   ```

5. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

6. **Start Services**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

7. **Access Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### 🔧 Environment Variables

Create a `.env` file in the backend directory:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-02-01

# File Storage Paths
UPLOADS_DIRECTORY=./uploads
OUTPUT_DIRECTORY=./outputs
REFERENCE_FILES_DIRECTORY=./reference_files

# Database Configuration
DATABASE_URL=sqlite:///./data_quality_platform.db

# Application Settings
MAX_CONCURRENT_JOBS=5
LOG_LEVEL=INFO
```

---

## User Guide

### 📤 **File Upload**

1. **Navigate** to the main application page
2. **Upload Files**:
   - Click "Choose File" or drag & drop CSV files
   - Supported formats: CSV (up to 100MB per file)
3. **Preview**: Review file contents before processing
4. **Select Agents**: Choose UC1 (Completeness) and/or UC4 (Duplicates)
5. **Process**: Click "Process File" to start analysis

### 📊 **Monitoring Jobs**

#### Processing Jobs Section
- **Real-time Status**: See current job progress
- **Queue Position**: View job position in processing queue
- **Error Details**: Access detailed error information if processing fails
- **Cancel Jobs**: Stop running jobs if needed

#### Job Statuses
- 🟡 **Queued**: Waiting to be processed
- 🔵 **Processing**: Currently being analyzed
- 🟢 **Completed**: Successfully processed
- 🔴 **Failed**: Processing encountered errors

### 📁 **Results Management**

#### Results Files Section
- **File Listing**: View all processed files with metadata
- **Job Information**: See which job generated each file
- **Download**: One-click download with icon buttons
- **Preview**: View file contents directly in browser
- **Filtering**: Only shows files from completed jobs

#### File Naming Convention
- Format: `job_{job_id}_{timestamp}_processed.csv`
- Example: `job_123_20250820_143022_processed.csv`

### 🎨 **Theme Management**

- **Toggle**: Click the theme button in header
- **Persistence**: Theme preference saved across sessions
- **Smooth Transitions**: Animated theme changes

---

## API Documentation

### 🔗 **Base Endpoints**

#### File Upload
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
- file: CSV file (required)

Response:
{
  "message": "File uploaded successfully",
  "filename": "uploaded_file.csv",
  "file_path": "./uploads/uploaded_file.csv"
}
```

#### Batch Processing
```http
POST /batch/process-directory
Content-Type: application/json

Body:
{
  "directory_path": "./uploads",
  "selected_agents": ["uc1_agent", "uc4_agent"],
  "reference_file_uc1": "reference.csv",
  "reference_file_uc4": "reference.csv"
}

Response:
{
  "message": "Batch processing started",
  "job_ids": [1, 2, 3],
  "total_jobs": 3
}
```

#### Job Status
```http
GET /jobs/{job_id}

Response:
{
  "id": 1,
  "filename": "data.csv",
  "status": "completed",
  "progress": 100,
  "start_time": "2025-08-20T14:30:22",
  "end_time": "2025-08-20T14:35:45",
  "results_json": {
    "output_file": "job_1_20250820_143022_processed.csv"
  }
}
```

#### Output Files
```http
GET /jobs/outputs

Response:
{
  "files": [
    {
      "name": "job_1_20250820_143022_processed.csv",
      "size": 15420,
      "modified": "2025-08-20T14:35:45",
      "job_id": 1,
      "job_status": "completed"
    }
  ],
  "directory": "./outputs",
  "total_files": 1,
  "completed_jobs": 1
}
```

### 📝 **Error Handling**

#### Standard Error Response
```json
{
  "detail": {
    "error": "Error message",
    "code": "ERROR_CODE",
    "timestamp": "2025-08-20T14:30:22"
  }
}
```

#### Common HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found
- `422`: Unprocessable Entity (invalid data)
- `500`: Internal Server Error

---

## Agent System

### 🤖 **UC1 Agent - Data Completeness Analysis**

#### Purpose
Analyzes data completeness, quality, and consistency patterns in CSV files.

#### Capabilities
- **Missing Value Detection**: Identifies null, empty, or invalid values
- **Data Type Validation**: Ensures data types match expected formats
- **Statistical Analysis**: Provides descriptive statistics
- **Quality Scoring**: Generates overall quality scores (0-100)
- **Recommendations**: Suggests data improvement strategies

#### Configuration
```python
{
  "analysis_type": "completeness",
  "missing_value_threshold": 0.1,  # 10% missing values threshold
  "quality_score_weights": {
    "completeness": 0.4,
    "consistency": 0.3,
    "accuracy": 0.3
  }
}
```

#### Output Format
```json
{
  "overall_quality_score": 85.5,
  "completeness_analysis": {
    "total_records": 1000,
    "complete_records": 855,
    "missing_value_percentage": 14.5
  },
  "column_analysis": {
    "name": {"completeness": 95.2, "data_type": "string"},
    "age": {"completeness": 88.7, "data_type": "integer"}
  },
  "recommendations": [
    "Address missing values in 'age' column",
    "Validate data types for 'salary' column"
  ]
}
```

### 🔍 **UC4 Agent - Duplicate Detection & Removal**

#### Purpose
Identifies and removes duplicate records using advanced similarity algorithms.

#### Capabilities
- **Exact Matching**: Finds identical records
- **Fuzzy Matching**: Detects similar records with configurable thresholds
- **Smart Deduplication**: Intelligently chooses which records to keep
- **Performance Optimization**: Efficient processing for large datasets
- **Detailed Reporting**: Provides duplicate analysis reports

#### Configuration
```python
{
  "similarity_threshold": 0.85,  # 85% similarity threshold
  "key_columns": ["name", "email"],  # Primary matching columns
  "fuzzy_matching": True,
  "preserve_latest": True  # Keep most recent record in duplicates
}
```

#### Output Format
```json
{
  "total_records": 1000,
  "duplicates_found": 45,
  "duplicates_removed": 40,
  "final_record_count": 960,
  "duplicate_groups": [
    {
      "group_id": 1,
      "records": [123, 456],
      "similarity_score": 0.92,
      "kept_record": 456
    }
  ]
}
```

### 🔄 **Sequential Processing**

When both agents are selected:
1. **UC1 Processing**: Analyzes data quality and generates quality report
2. **UC4 Processing**: Uses UC1's output as input, removes duplicates
3. **Combined Results**: Both analysis report and cleaned data

#### Workflow
```
Original File → UC1 Agent → Quality Analysis + Cleaned File → UC4 Agent → Final Deduplicated File
```

---

## Database Schema

### 📊 **Core Tables**

#### JobRecord
```sql
CREATE TABLE job_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0,
    start_time DATETIME,
    end_time DATETIME,
    error_message TEXT,
    results_json TEXT,
    agent_type VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### FileProcessingMetrics
```sql
CREATE TABLE file_processing_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT,
    metric_details TEXT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES job_record (id)
);
```

#### ReferenceFile
```sql
CREATE TABLE reference_file (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uc_type VARCHAR(10) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### AgentActivity (Optional)
```sql
CREATE TABLE agent_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    agent_name VARCHAR(100) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    activity_details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES job_record (id)
);
```

### 🔄 **Database Operations**

#### Job Lifecycle
1. **Creation**: Job record created with 'queued' status
2. **Processing**: Status updated to 'processing', progress tracked
3. **Completion**: Status set to 'completed', results stored in results_json
4. **Error Handling**: Status set to 'failed', error details stored

#### Metrics Collection
- Performance metrics stored for each processing step
- Quality scores and analysis results tracked
- Processing time and resource usage monitored

---

## File Organization

### 📁 **Directory Structure**

```
Platform/
├── backend/
│   ├── .venv/                 # Python virtual environment
│   ├── agents/               # AI agent implementations
│   │   ├── base_config.py    # Shared agent configuration
│   │   ├── uc1_agent.py      # Completeness analysis agent
│   │   ├── uc1_duckdb_agent.py # DuckDB-based UC1 agent
│   │   ├── uc4_agent.py      # Duplicate detection agent
│   │   └── uc4_duckdb_agent.py # DuckDB-based UC4 agent
│   ├── routes/               # API route handlers
│   │   ├── upload.py         # File upload endpoints
│   │   ├── batch.py          # Batch processing endpoints
│   │   └── jobs.py           # Job management endpoints
│   ├── logs/                 # Application logs
│   ├── uploads/              # Uploaded files storage
│   ├── outputs/              # Processed files output
│   ├── reference_files/      # Reference files for agents
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database models and operations
│   ├── models.py            # Pydantic models
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   │   ├── FileUpload.tsx   # File upload component
│   │   ├── JobMonitoring.tsx # Job status monitoring
│   │   ├── OutputFilesSection.tsx # Results display
│   │   └── ThemeToggle.tsx  # Theme switching
│   ├── lib/                 # Utility libraries
│   ├── styles/              # CSS and styling
│   ├── types/               # TypeScript type definitions
│   ├── package.json         # Node.js dependencies
│   └── next.config.js       # Next.js configuration
├── config/                  # Configuration files
├── tests/                   # Test files
└── documentation/           # Additional documentation
```

### 📂 **File Naming Conventions**

#### Input Files
- Format: `{original_filename}.csv`
- Example: `customer_data.csv`

#### Output Files
- Format: `job_{job_id}_{timestamp}_processed.csv`
- Example: `job_123_20250820_143022_processed.csv`

#### Reference Files
- Format: `{uc_type}_{timestamp}_{original_name}.csv`
- Example: `UC1_20250820_074245_reference_data.csv`

#### Batch Directories
- Format: `batch_{timestamp}`
- Example: `batch_20250820_143022/`

### 🗂️ **Storage Organization**

#### Uploads Directory
```
uploads/
├── customer_data.csv
├── sales_records.csv
└── inventory_list.csv
```

#### Outputs Directory
```
outputs/
├── batch_20250820_143022/
│   ├── job_123_20250820_143022_processed.csv
│   ├── job_124_20250820_143025_processed.csv
│   └── job_125_20250820_143028_processed.csv
└── batch_20250820_150015/
    └── job_126_20250820_150015_processed.csv
```

---

## Configuration

### ⚙️ **Application Configuration**

#### Backend Configuration (.env)
```env
# Azure OpenAI Settings
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# File Storage
UPLOADS_DIRECTORY=./uploads
OUTPUT_DIRECTORY=./outputs
REFERENCE_FILES_DIRECTORY=./reference_files

# Database
DATABASE_URL=sqlite:///./data_quality_platform.db

# Processing
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/application.log

# Security
MAX_FILE_SIZE_MB=100
ALLOWED_FILE_TYPES=csv,txt

# Performance
CHUNK_SIZE=10000
MEMORY_LIMIT_MB=1024
```

#### Frontend Configuration (next.config.js)
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
    APP_NAME: 'Agentic AI Data Quality Platform',
    APP_VERSION: '1.0.0'
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*'
      }
    ];
  }
};

module.exports = nextConfig;
```

### 🔧 **Agent Configuration**

#### UC1 Agent Settings
```python
UC1_CONFIG = {
    "analysis_depth": "comprehensive",  # basic, standard, comprehensive
    "missing_value_threshold": 0.1,
    "data_type_strict_validation": True,
    "generate_recommendations": True,
    "include_statistical_analysis": True,
    "quality_score_weights": {
        "completeness": 0.4,
        "consistency": 0.3,
        "accuracy": 0.3
    }
}
```

#### UC4 Agent Settings
```python
UC4_CONFIG = {
    "similarity_algorithm": "fuzzy",  # exact, fuzzy, hybrid
    "similarity_threshold": 0.85,
    "key_columns": ["name", "email"],
    "fuzzy_matching_enabled": True,
    "preserve_latest_record": True,
    "batch_size": 1000,
    "performance_mode": "balanced"  # fast, balanced, accurate
}
```

---

## Troubleshooting

### 🐛 **Common Issues**

#### 1. **Backend Won't Start**
**Symptoms**: Server fails to start, port errors
**Solutions**:
```bash
# Check if port is in use
sudo lsof -i :8000

# Kill existing process
sudo kill -9 <PID>

# Start with different port
uvicorn main:app --port 8001
```

#### 2. **Database Connection Issues**
**Symptoms**: SQLite errors, table not found
**Solutions**:
```bash
# Reinitialize database
cd backend
python migrate_db.py

# Check database file permissions
ls -la data_quality_platform.db
```

#### 3. **File Upload Failures**
**Symptoms**: Upload timeouts, file size errors
**Solutions**:
- Check file size (max 100MB)
- Verify file format (CSV only)
- Ensure uploads directory exists and is writable
```bash
mkdir -p uploads
chmod 755 uploads
```

#### 4. **Azure OpenAI Connection Issues**
**Symptoms**: API key errors, endpoint unreachable
**Solutions**:
```bash
# Test API connectivity
curl -H "api-key: YOUR_API_KEY" \
     "https://your-endpoint.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-01"

# Verify environment variables
echo $AZURE_OPENAI_API_KEY
```

#### 5. **Frontend Build Issues**
**Symptoms**: TypeScript errors, dependency issues
**Solutions**:
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check TypeScript configuration
npx tsc --noEmit
```

### 📊 **Performance Optimization**

#### 1. **Memory Management**
- Increase `MEMORY_LIMIT_MB` for large files
- Reduce `CHUNK_SIZE` for memory-constrained environments
- Monitor memory usage during processing

#### 2. **Concurrent Processing**
- Adjust `MAX_CONCURRENT_JOBS` based on system resources
- Monitor CPU and memory usage
- Use job queue for peak load management

#### 3. **File Processing**
- Use streaming for large files
- Implement file compression for storage
- Consider database indexing for better query performance

### 🔍 **Debugging**

#### Enable Debug Logging
```env
LOG_LEVEL=DEBUG
```

#### Check Application Logs
```bash
# Backend logs
tail -f backend/logs/application.log

# Agent activity logs
tail -f backend/logs/agent_activities.log
```

#### Monitor Job Status
```bash
# Check job queue
curl http://localhost:8000/jobs

# Monitor specific job
curl http://localhost:8000/jobs/123
```

---

## Development Guide

### 🛠️ **Development Setup**

#### 1. **Development Environment**
```bash
# Clone repository
git clone <repository-url>
cd data-quality-platform

# Setup pre-commit hooks
pip install pre-commit
pre-commit install

# Install development dependencies
cd backend
pip install -r requirements-dev.txt

cd ../frontend
npm install --include=dev
```

#### 2. **Code Quality Tools**
```bash
# Python code formatting
black backend/
isort backend/

# TypeScript checking
cd frontend
npm run type-check
npm run lint
```

### 🧪 **Testing**

#### Backend Testing
```bash
cd backend
pytest tests/ -v
pytest tests/test_agents.py -v
pytest tests/test_api.py -v
```

#### Frontend Testing
```bash
cd frontend
npm test
npm run test:e2e
```

#### Integration Testing
```bash
# Test complete workflow
python tests/test_integration.py
```

### 📦 **Building for Production**

#### Backend Deployment
```bash
cd backend
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Deployment
```bash
cd frontend
npm run build
npm start
```

#### Docker Deployment
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### 🔄 **Contributing**

#### Development Workflow
1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Run code quality checks
4. Submit pull request with descriptive commit messages
5. Ensure all tests pass in CI/CD pipeline

#### Code Standards
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, proper type definitions
- **Documentation**: Update documentation for new features
- **Testing**: Maintain test coverage above 80%

### 📈 **Monitoring & Analytics**

#### Application Metrics
- Job processing times
- Success/failure rates
- File processing throughput
- Resource utilization

#### User Analytics
- File upload patterns
- Agent usage statistics
- Error frequency analysis
- Performance bottlenecks

---

## 📞 Support & Resources

### 🆘 **Getting Help**

- **Documentation**: This comprehensive guide
- **API Reference**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs and request features
- **Community**: Join our developer community

### 🔗 **Useful Links**

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Next.js Documentation**: https://nextjs.org/docs
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Azure OpenAI Documentation**: https://docs.microsoft.com/azure/cognitive-services/openai/

### 📋 **Changelog**

#### Version 1.0.0 (Current)
- ✅ Complete UI/UX redesign with dark theme support
- ✅ Enhanced file organization with unique naming
- ✅ Sequential agent processing workflow
- ✅ Job-specific file filtering and management
- ✅ Improved error handling and recovery
- ✅ Comprehensive API documentation
- ✅ Performance optimizations and monitoring

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Last Updated: August 20, 2025*
*Version: 1.0.0*
*Documentation Generated: 2025-08-20*
