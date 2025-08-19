# Agentic AI Data Quality Platform

An enterprise-grade data quality platform powered by Agno framework and Azure OpenAI, designed specifically for PnP data files with comprehensive multi-agent architecture for data quality assessment and correction.

## 🎯 Overview

This platform implements two critical use cases:
- **UC1**: Incomplete/Sparse Data Files Detection and Correction
  - Analyzes data completeness and quality
  - Updates database with detailed quality metrics
  - Provides actionable improvement recommendations
- **UC4**: Duplicate Records Detection and Resolution
  - Detects various types of duplicates (exact, semantic, business-rule)
  - Produces cleaned files with duplicates removed
  - Maintains original and cleaned file versions

Each use case is powered by 5 specialized AI agents working in orchestration to provide comprehensive data quality analysis with real-time status updates.

## 🏗️ Architecture

### Technology Stack
- **AI Framework**: Agno (docs.agno.com)
- **AI Models**: Azure OpenAI GPT-4
- **Backend**: FastAPI + Python 3.13
- **Package Manager**: uv (ultra-fast Python package installer)
- **Database**: SQLite for job management
- **Data Validation**: Pydantic

### Multi-Agent Architecture

#### UC1 - Sparse Data Detection (5 Agents)
1. **DataCompletenessAgent**: Analyzes overall data completeness patterns
2. **SparseColumnDetectionAgent**: Identifies columns with high missing value rates
3. **EmptyRowAnalysisAgent**: Detects and analyzes completely empty rows
4. **DataQualityScoreAgent**: Calculates comprehensive quality scores
5. **UC1OrchestrationAgent**: Synthesizes all analyses into actionable insights

#### UC4 - Duplicate Detection (5 Agents)
1. **ExactDuplicateDetectionAgent**: Finds exact row duplicates
2. **SemanticDuplicateAgent**: Identifies semantically similar records
3. **BusinessKeyDuplicateAgent**: Detects business logic duplicates
4. **DeduplicationStrategyAgent**: Recommends deduplication approaches
5. **UC4OrchestrationAgent**: Coordinates all duplicate detection methods

## 🚀 Prerequisites

### Azure OpenAI Configuration
1. Azure OpenAI resource with GPT-4 deployment
2. Required environment variables:
```bash
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### System Requirements
- Python 3.13+
- uv package manager
- 8GB+ RAM recommended for large files

## 📦 Installation

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd Platform
```

### 3. Backend Setup
```bash
cd backend
uv sync  # Installs all dependencies from pyproject.toml
```

### 4. Environment Configuration
Create `.env` file in backend directory:
```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
DATABASE_URL=sqlite:///./jobs.db
LOG_LEVEL=INFO
```

### 5. Initialize Database
```bash
uv run python -c "
from database.models import Base, engine
Base.metadata.create_all(bind=engine)
print('Database initialized successfully')
"
```

## 🎮 Usage

### Start the Platform
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Upload File for Analysis
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_data_file.csv" \
  -F "use_case=UC1"
```

#### Check Job Status
```bash
curl "http://localhost:8000/jobs/{job_id}/status"
```

#### Get Analysis Results
```bash
curl "http://localhost:8000/jobs/{job_id}/results"
```

### Example Workflow

1. **Upload CSV File**:
```python
import requests

with open('Quality_Sugar_Daily_Article_Data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f},
        data={'use_case': 'UC1'}
    )
job_id = response.json()['job_id']
```

2. **Monitor Progress**:
```python
status_response = requests.get(f'http://localhost:8000/jobs/{job_id}/status')
print(status_response.json())
```

3. **Get Results**:
```python
results_response = requests.get(f'http://localhost:8000/jobs/{job_id}/results')
analysis = results_response.json()
```

## 🔧 Agent Capabilities

### UC1 - Sparse Data Analysis
- **Completeness Assessment**: Row-level and column-level completeness analysis
- **Missing Pattern Detection**: Identifies systematic missing data patterns
- **Quality Scoring**: Comprehensive 0-100 quality scores with detailed breakdowns
- **Database Integration**: Real-time updates of quality metrics in database
- **Status Tracking**: Multi-stage processing with detailed status updates (analyzing_completeness → analysis_complete)
- **Actionable Recommendations**: Specific suggestions for data improvement

### UC4 - Duplicate Detection
- **Multi-Algorithm Detection**: Exact, fuzzy, and semantic matching
- **Business Rule Validation**: Custom business logic for duplicate identification
- **File Cleaning**: Automatic generation of cleaned CSV files without duplicates
- **Confidence Scoring**: Probabilistic duplicate assessment
- **Status Tracking**: Multi-stage processing (detecting_duplicates → cleaning_file → cleaning_complete)
- **Deduplication Strategies**: Merge, keep-first, keep-best recommendations
- **Impact Analysis**: Assessment of deduplication effects on data integrity

## 📊 Sample Outputs

### UC1 Results Structure
```json
{
  "overall_completeness_score": 85.2,
  "sparse_columns": ["column_x", "column_y"],
  "empty_rows": [123, 456, 789],
  "quality_breakdown": {
    "completeness": 85.2,
    "consistency": 92.1,
    "accuracy": 88.7
  },
  "recommendations": [
    "Consider data imputation for sparse columns",
    "Remove empty rows: 123, 456, 789"
  ]
}
```

### UC4 Results Structure
```json
{
  "total_duplicates": 45,
  "exact_duplicates": 12,
  "semantic_duplicates": 28,
  "business_duplicates": 5,
  "deduplication_strategy": "merge_with_conflict_resolution",
  "confidence_scores": [0.95, 0.87, 0.92],
  "recommended_actions": [
    "Merge records 1,2,3 using latest timestamp",
    "Manual review required for records 45,46"
  ]
}
```

## 🛠️ Development

### Project Structure
```
Platform/
├── backend/
│   ├── agents/              # Multi-agent system
│   │   ├── base_config.py   # Shared agent configuration
│   │   ├── uc1_sparse_data_agent.py
│   │   └── uc4_duplicate_agent.py
│   ├── database/            # SQLite models
│   ├── models/              # Pydantic schemas
│   ├── main.py             # FastAPI application
│   └── pyproject.toml      # uv dependencies
├── frontend/               # React dashboard (future)
└── tests/                 # Test suites
```

### Adding New Agents
1. Inherit from `Agent` (Agno framework)
2. Use `AgentConfig.get_azure_openai_model()` for model setup
3. Implement detailed instruction prompts
4. Return standardized `BaseAgentResults`

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_API_VERSION` | API version | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT-4 deployment name | Yes |
| `DATABASE_URL` | SQLite database path | No (default provided) |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

## 🧪 Testing

### Run Unit Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Run Integration Tests
```bash
uv run pytest tests/integration/ -v
```

### Test with Sample Data
```bash
# Test UC1 with provided sample files
curl -X POST "http://localhost:8000/upload" \
  -F "file=@Quality_Sugar_Daily_Article_Data-133565508097027794.csv" \
  -F "use_case=UC1"

# Test UC4 with duplicate detection
curl -X POST "http://localhost:8000/upload" \
  -F "file=@Quality_Sugar_Daily_Article_Data-133571556013916867.csv" \
  -F "use_case=UC4"
```

## 📈 Performance

### Optimization Tips
- Large files (>100MB): Process in chunks using streaming
- High-volume processing: Consider batch job queuing
- Memory optimization: Use uv's efficient dependency resolution
- Azure OpenAI: Monitor token usage and implement rate limiting

### Scaling Considerations
- **Horizontal**: Deploy multiple FastAPI instances behind load balancer
- **Vertical**: Increase memory for large file processing
- **Database**: Consider PostgreSQL for production workloads
- **Caching**: Implement Redis for frequent analysis caching

## 🔒 Security

- Environment variables for sensitive configuration
- File upload validation and size limits
- Azure OpenAI secure connection handling
- Input sanitization for all user data

## 📝 License

[Add your license information here]

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For questions and support:
- Documentation: [Internal docs link]
- Issues: Create GitHub issue with detailed description
- Azure OpenAI: Ensure proper API key and endpoint configuration

---

**Built with ❤️ using Agno framework and Azure OpenAI**
