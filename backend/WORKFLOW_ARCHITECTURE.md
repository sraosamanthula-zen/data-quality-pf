# Data Quality Platform - Job Scheduling and Workflow Architecture

## High-Level Architecture Overview

The Data Quality Platform uses an **asynchronous, semaphore-controlled batch processing workflow** with FastAPI background tasks and database-backed job management.

## Job Scheduling System

### 1. **Job Creation and Queuing**
```
Client Request → Job Record Creation → Database Storage → Background Processing Queue
```

**Components:**
- **JobRecord Model**: SQLAlchemy model that tracks job state, metadata, and results
- **Database**: SQLite with proper session management for job persistence
- **FastAPI BackgroundTasks**: Non-blocking task execution
- **Asyncio Semaphore**: Concurrency control (max 5 concurrent jobs)

### 2. **Job States and Lifecycle**
```
pending → queued → processing → completed/failed
```

**State Definitions:**
- `pending`: Job created but not yet queued for processing
- `queued`: Job ready for processing, waiting for available slot
- `processing`: Job currently being executed by an agent
- `completed`: Job finished successfully with results
- `failed`: Job encountered an error and could not complete

### 3. **Workflow Types**

#### A. **Single File Upload Workflow**
1. **File Upload** (`/upload` endpoint)
2. **Job Creation** with selected UCs (UC1, UC4)
3. **Reference File Validation**
4. **Background Processing** with agents
5. **Result Storage** and status updates

#### B. **Batch Directory Processing Workflow**
1. **Directory Scan** (`/batch/process-directory`)
2. **Multiple Job Creation** (one per file)
3. **Parallel Processing** with semaphore control
4. **Concurrent Execution** (max 5 jobs simultaneously)
5. **Aggregated Results** and status reporting

## Agent Processing Architecture

### **UC1 Agent (Sparse Data Detection)**
- **Purpose**: Detects incomplete/sparse data by comparing against reference files
- **Process**: 
  1. Loads target file and reference file
  2. Performs schema comparison and completeness analysis
  3. Generates quality score and fills missing data
  4. Outputs cleaned file with quality metrics

### **UC4 Agent (Duplicate Detection)**
- **Purpose**: Identifies and removes duplicate records
- **Process**:
  1. Loads processed file (from UC1 if available)
  2. Applies duplicate detection algorithms
  3. Removes duplicates and tracks statistics
  4. Outputs deduplicated file with metrics

### **Sequential Processing Chain**
```
Original File → UC1 Agent → Cleaned File → UC4 Agent → Final File
```

## Concurrency and Performance

### **Semaphore-Based Control**
```python
MAX_CONCURRENT_JOBS = 5
job_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
```

**Benefits:**
- **Resource Management**: Prevents system overload
- **Predictable Performance**: Consistent processing times
- **Memory Control**: Limits simultaneous file operations
- **Database Connection Management**: Prevents connection pool exhaustion

### **Async Processing Pattern**
```python
async def process_with_semaphore(job_data):
    async with batch_semaphore:
        return await process_file_with_reference_async(...)
```

## Database Design

### **Core Tables**

#### **JobRecord Table**
- **Purpose**: Central job tracking and state management
- **Key Fields**:
  - `id`: Unique job identifier
  - `status`: Current job state
  - `file_path`: Location of input file
  - `selected_ucs`: Comma-separated UC types
  - `reference_file_path`: JSON mapping of UC → reference file
  - `results_json`: Serialized processing results
  - `created_at/completed_at`: Timing information

#### **FileProcessingMetrics Table**
- **Purpose**: Performance and processing statistics
- **Key Fields**:
  - `job_id`: Links to JobRecord
  - `file_size_bytes`: Input file size
  - `processing_time_seconds`: Total processing duration
  - `issues_found`: Number of data quality issues

#### **ReferenceFile Table**
- **Purpose**: Management of reference files for UC processing
- **Key Fields**:
  - `uc_type`: UC1 or UC4
  - `file_path`: Location of reference file
  - `is_active`: Whether file is currently in use

## Error Handling and Recovery

### **Job Recovery System**
- **Stuck Job Detection**: Identifies jobs stuck in processing states
- **Automatic Failover**: Marks stuck jobs as failed on restart
- **Manual Recovery**: `/batch/recover-jobs` endpoint for manual intervention
- **File Validation**: Checks for missing files during recovery

### **Error Categories**
1. **File Errors**: Missing files, corrupt data, permission issues
2. **Processing Errors**: Agent failures, memory issues, timeout
3. **System Errors**: Database connection issues, disk space
4. **Configuration Errors**: Missing reference files, invalid UC selection

## API Endpoints and Responsibilities

### **Core Processing Endpoints**
- `POST /upload`: Single file upload and processing
- `POST /batch/process-directory`: Batch directory processing
- `GET /batch/status/{job_ids}`: Multi-job status checking
- `POST /batch/recover-jobs`: Manual job recovery

### **Monitoring and Management**
- `GET /stats/`: Job statistics and metrics
- `GET /stats/health`: System health check
- `GET /batch/concurrency-info`: Current processing load
- `GET /batch/stuck-jobs`: Stuck job diagnostics

## Technology Stack Integration

### **FastAPI Framework**
- **Async Support**: Native async/await for concurrent processing
- **Background Tasks**: Non-blocking job execution
- **Dependency Injection**: Database session management
- **Type Safety**: Pydantic models for request/response validation

### **SQLAlchemy ORM**
- **Modern Patterns**: SQLAlchemy 2.0 with Mapped annotations
- **Session Management**: Context managers for safe transactions
- **Connection Pooling**: Efficient database resource usage

### **Asyncio Concurrency**
- **Semaphore Control**: Resource limiting and queue management
- **Task Scheduling**: Parallel job execution with proper coordination
- **Exception Handling**: Graceful error recovery and reporting

## Performance Characteristics

### **Throughput**
- **Concurrent Jobs**: Up to 5 simultaneous processing tasks
- **Queue Management**: Unlimited queued jobs with FIFO processing
- **Memory Efficiency**: Per-job isolation with controlled resource usage

### **Scalability**
- **Horizontal**: Can be extended with job queues (Redis/Celery)
- **Vertical**: Configurable concurrency limits based on system resources
- **Database**: SQLite suitable for moderate loads, PostgreSQL for production

### **Monitoring**
- **Real-time Status**: Live job progress tracking
- **Performance Metrics**: Processing times and resource usage
- **Error Tracking**: Comprehensive error logging and recovery

This architecture provides a robust, scalable foundation for data quality processing with proper error handling, performance monitoring, and concurrent execution management.
