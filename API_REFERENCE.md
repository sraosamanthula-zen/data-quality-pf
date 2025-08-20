# 📡 API Reference Guide

## 🌐 Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

---

## 📤 File Upload Endpoints

### Upload File
```http
POST /upload
```

**Request:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.csv"
```

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "data.csv",
  "file_path": "./uploads/data.csv",
  "file_size": 15420
}
```

**Error Response:**
```json
{
  "detail": "File size exceeds maximum limit of 100MB"
}
```

---

## 🔄 Batch Processing Endpoints

### Process Directory
```http
POST /batch/process-directory
```

**Request:**
```bash
curl -X POST "http://localhost:8000/batch/process-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./uploads",
    "selected_agents": ["uc1_agent", "uc4_agent"],
    "reference_file_uc1": "reference.csv",
    "reference_file_uc4": "reference.csv"
  }'
```

**Response:**
```json
{
  "message": "Batch processing started",
  "job_ids": [1, 2, 3],
  "total_jobs": 3,
  "estimated_time": "5-10 minutes"
}
```

### Get Batch Status
```http
GET /batch/status/{job_ids}
```

**Request:**
```bash
curl "http://localhost:8000/batch/status/1,2,3"
```

**Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "status": "completed",
      "progress": 100,
      "filename": "data1.csv"
    },
    {
      "id": 2,
      "status": "processing", 
      "progress": 65,
      "filename": "data2.csv"
    }
  ]
}
```

---

## 💼 Job Management Endpoints

### Get All Jobs
```http
GET /jobs
```

**Response:**
```json
[
  {
    "id": 1,
    "filename": "customer_data.csv",
    "status": "completed",
    "progress": 100,
    "start_time": "2025-08-20T14:30:22",
    "end_time": "2025-08-20T14:35:45",
    "agent_type": "uc1_agent"
  }
]
```

### Get Specific Job
```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "id": 1,
  "filename": "customer_data.csv",
  "file_path": "./uploads/customer_data.csv",
  "status": "completed",
  "progress": 100,
  "start_time": "2025-08-20T14:30:22",
  "end_time": "2025-08-20T14:35:45",
  "agent_type": "uc1_agent",
  "results_json": {
    "output_file": "job_1_20250820_143022_processed.csv",
    "quality_score": 85.5,
    "issues_found": 12
  }
}
```

### Delete Job
```http
DELETE /jobs/{job_id}
```

**Response:**
```json
{
  "message": "Job 1 deleted successfully"
}
```

---

## 📁 File Management Endpoints

### Get Output Files
```http
GET /jobs/outputs
```

**Response:**
```json
{
  "files": [
    {
      "name": "job_1_20250820_143022_processed.csv",
      "size": 15420,
      "modified": "2025-08-20T14:35:45",
      "job_id": 1,
      "job_status": "completed",
      "download_url": "/download/job_1_20250820_143022_processed.csv"
    }
  ],
  "directory": "./outputs",
  "total_files": 1,
  "completed_jobs": 1
}
```

### Download File
```http
GET /download/{filename}
```

**Response:**
- File download stream
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="file.csv"`

### Preview File
```http
GET /upload/preview-file?file_path={path}&lines={number}
```

**Request:**
```bash
curl "http://localhost:8000/upload/preview-file?file_path=./uploads/data.csv&lines=10"
```

**Response:**
```json
{
  "headers": ["name", "age", "salary"],
  "rows": [
    ["John Doe", "30", "75000"],
    ["Jane Smith", "28", "68000"]
  ],
  "total_rows": 1000,
  "preview_rows": 10
}
```

---

## 📋 Reference File Endpoints

### Upload Reference File
```http
POST /upload/reference-file
```

**Request:**
```bash
curl -X POST "http://localhost:8000/upload/reference-file" \
  -F "file=@reference.csv" \
  -F "uc_type=UC1"
```

**Response:**
```json
{
  "message": "Reference file uploaded successfully",
  "uc_type": "UC1",
  "filename": "reference.csv",
  "file_path": "./reference_files/UC1_20250820_143022_reference.csv"
}
```

### Get Reference Files
```http
GET /upload/reference-files
```

**Response:**
```json
{
  "UC1": {
    "filename": "reference.csv",
    "file_path": "./reference_files/UC1_20250820_143022_reference.csv",
    "uploaded_at": "2025-08-20T14:30:22"
  },
  "UC4": null
}
```

### Delete Reference File
```http
DELETE /upload/reference-file/{uc_type}
```

**Response:**
```json
{
  "message": "Reference file for UC1 deleted successfully"
}
```

---

## 📊 System Information Endpoints

### Get Concurrency Info
```http
GET /batch/concurrency-info
```

**Response:**
```json
{
  "max_concurrent_jobs": 5,
  "current_active_jobs": 2,
  "available_slots": 3,
  "queued_jobs": 1
}
```

### Update Concurrency
```http
POST /batch/update-concurrency
```

**Request:**
```bash
curl -X POST "http://localhost:8000/batch/update-concurrency" \
  -H "Content-Type: application/json" \
  -d '{"max_concurrent_jobs": 10}'
```

### Get Stuck Jobs
```http
GET /batch/stuck-jobs
```

**Response:**
```json
{
  "stuck_jobs": [
    {
      "id": 5,
      "filename": "data.csv",
      "status": "processing",
      "start_time": "2025-08-20T10:30:22",
      "duration_minutes": 120
    }
  ],
  "total_stuck": 1
}
```

---

## 🔍 Health Check Endpoints

### API Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-20T14:30:22",
  "version": "1.0.0",
  "database": "connected",
  "ai_service": "available"
}
```

### System Status
```http
GET /status
```

**Response:**
```json
{
  "application": {
    "name": "Agentic AI Data Quality Platform",
    "version": "1.0.0",
    "uptime": "2 hours 15 minutes"
  },
  "database": {
    "status": "connected",
    "total_jobs": 45,
    "active_jobs": 3
  },
  "storage": {
    "uploads_directory": "./uploads",
    "outputs_directory": "./outputs",
    "disk_usage": "2.5 GB"
  }
}
```

---

## 🚨 Error Responses

### Standard Error Format
```json
{
  "detail": {
    "error": "Error description",
    "code": "ERROR_CODE",
    "timestamp": "2025-08-20T14:30:22",
    "request_id": "abc123"
  }
}
```

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid file format |
| `404` | Not Found | Job not found |
| `413` | Payload Too Large | File size exceeds limit |
| `422` | Unprocessable Entity | Validation error |
| `500` | Internal Server Error | Server processing error |

### Error Examples

**File Too Large:**
```json
{
  "detail": {
    "error": "File size exceeds maximum limit of 100MB",
    "code": "FILE_TOO_LARGE",
    "max_size_mb": 100,
    "file_size_mb": 150
  }
}
```

**Invalid File Format:**
```json
{
  "detail": {
    "error": "Only CSV files are supported",
    "code": "INVALID_FILE_FORMAT",
    "supported_formats": ["csv"],
    "provided_format": "xlsx"
  }
}
```

**Job Not Found:**
```json
{
  "detail": {
    "error": "Job with ID 999 not found",
    "code": "JOB_NOT_FOUND",
    "job_id": 999
  }
}
```

---

## 🔐 Authentication (Future)

### API Key Authentication
```http
Authorization: Bearer your-api-key-here
```

### Rate Limiting
- **Uploads**: 10 files per minute
- **API Calls**: 100 requests per minute
- **Batch Processing**: 5 concurrent jobs per user

---

## 📝 Request/Response Examples

### Complete Workflow Example

1. **Upload File:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@customer_data.csv"
```

2. **Start Processing:**
```bash
curl -X POST "http://localhost:8000/batch/process-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./uploads",
    "selected_agents": ["uc1_agent", "uc4_agent"]
  }'
```

3. **Monitor Progress:**
```bash
curl "http://localhost:8000/jobs/1"
```

4. **Get Results:**
```bash
curl "http://localhost:8000/jobs/outputs"
```

5. **Download Processed File:**
```bash
curl -O "http://localhost:8000/download/job_1_20250820_143022_processed.csv"
```

---

## 🛠️ SDK Examples

### Python SDK Example
```python
import requests

class DataQualityAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/upload",
                files={"file": f}
            )
        return response.json()
    
    def start_processing(self, agents=["uc1_agent", "uc4_agent"]):
        response = requests.post(
            f"{self.base_url}/batch/process-directory",
            json={
                "directory_path": "./uploads",
                "selected_agents": agents
            }
        )
        return response.json()
    
    def get_job_status(self, job_id):
        response = requests.get(f"{self.base_url}/jobs/{job_id}")
        return response.json()

# Usage
api = DataQualityAPI()
result = api.upload_file("data.csv")
processing = api.start_processing()
status = api.get_job_status(processing["job_ids"][0])
```

### JavaScript SDK Example
```javascript
class DataQualityAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async startProcessing(agents = ['uc1_agent', 'uc4_agent']) {
        const response = await fetch(`${this.baseUrl}/batch/process-directory`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directory_path: './uploads',
                selected_agents: agents
            })
        });
        
        return await response.json();
    }
    
    async getJobStatus(jobId) {
        const response = await fetch(`${this.baseUrl}/jobs/${jobId}`);
        return await response.json();
    }
}

// Usage
const api = new DataQualityAPI();
const file = document.getElementById('fileInput').files[0];
const uploadResult = await api.uploadFile(file);
const processing = await api.startProcessing();
const status = await api.getJobStatus(processing.job_ids[0]);
```

---

*API Reference v1.0.0 | Last Updated: August 20, 2025*
