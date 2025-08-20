# 🚀 Quick Start Guide - Data Quality Platform

## 🎯 Getting Started in 5 Minutes

### 1. **Start the Application**
```bash
# Backend (Terminal 1)
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)  
cd frontend
npm run dev
```

### 2. **Access the Application**
- 🌐 **Web Interface**: http://localhost:3000
- 📋 **API Docs**: http://localhost:8000/docs

### 3. **Upload & Process Files**
1. **Upload**: Drag & drop CSV files or click "Choose File"
2. **Select Agents**: 
   - ✅ UC1 Agent: Data completeness analysis
   - ✅ UC4 Agent: Duplicate detection & removal
3. **Process**: Click "Process File" button
4. **Monitor**: Watch progress in "Processing Jobs" section
5. **Download**: Get results from "Results Files" section

---

## 🔧 Quick Commands

### **Clear All Data**
```bash
cd backend
python clear_jobs.py  # Clear all jobs and metrics
rm -rf uploads/*      # Clear uploaded files
rm -rf outputs/*      # Clear output files
```

### **Check Status**
```bash
# Test backend
curl http://localhost:8000/jobs

# Test file upload
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_file.csv"
```

### **Restart Services**
```bash
# Kill existing processes
pkill -f uvicorn
pkill -f "npm run dev"

# Restart (run in separate terminals)
uvicorn main:app --reload --port 8000
npm run dev
```

---

## 🎨 Features Overview

### **Theme Support**
- 🌞 **Light Mode**: Clean, professional interface
- 🌙 **Dark Mode**: Easy on the eyes, modern look
- 🔄 **Toggle**: Click theme button in header

### **File Processing**
- 📤 **Upload**: CSV files up to 100MB
- 🔄 **Batch Processing**: Multiple files simultaneously  
- 📊 **Real-time Monitoring**: Live job status updates
- 📁 **Organized Results**: Job-specific file organization

### **AI Agents**
- 🧠 **UC1**: Data quality & completeness analysis
- 🔍 **UC4**: Advanced duplicate detection & removal
- ⚡ **Sequential Processing**: UC1 → UC4 workflow

---

## 📁 File Structure

```
📦 Your Files
├── 📤 uploads/           # Your uploaded CSV files
├── 📊 outputs/           # Processed results
│   └── batch_20250820_143022/
│       ├── job_123_20250820_143022_processed.csv
│       └── job_124_20250820_143025_processed.csv
├── 📋 reference_files/   # Reference data for agents
└── 📝 logs/             # Application logs
```

---

## 🚨 Troubleshooting

### **Common Issues**

| Problem | Solution |
|---------|----------|
| 🔴 Backend won't start | Check port 8000: `sudo lsof -i :8000` |
| 🔴 Upload fails | Check file size (<100MB) and format (CSV) |
| 🔴 Jobs stuck | Restart backend: `pkill uvicorn && uvicorn main:app --reload` |
| 🔴 No results showing | Check if jobs completed successfully |

### **Quick Fixes**
```bash
# Reset everything
cd backend && python clear_jobs.py
rm -rf uploads/* outputs/*

# Restart services
pkill -f uvicorn && uvicorn main:app --reload --port 8000
```

---

## 📞 Need Help?

1. 📖 **Full Documentation**: `DOCUMENTATION.md`
2. 🛠️ **API Reference**: http://localhost:8000/docs  
3. 📊 **Check Logs**: `backend/logs/application.log`
4. 🔍 **Test Endpoints**: Use Swagger UI at `/docs`

---

*Happy Data Processing! 🎉*
