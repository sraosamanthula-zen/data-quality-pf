# Enhanced Platform Features Documentation

## 🚀 New Features Implemented

Based on user requirements, the platform has been significantly enhanced with the following improvements:

### 1. ✅ Reference File Upload at UC Selection

**Feature**: Reference files are now uploaded directly at UC selection, eliminating the need for separate upload steps.

**Implementation**:
- Each UC selection card (UC1 and UC4) now includes an integrated reference file upload dropzone
- Reference files are displayed immediately below each UC selection
- Once uploaded, the filename is shown persistently until a new file is uploaded
- Visual indicators show upload status and file readiness

**User Flow**:
1. Select analysis types (UC1/UC4)
2. Upload reference files directly in each UC card
3. Reference filenames are displayed and persist
4. Upload new files to replace existing ones

### 2. ✅ Environment Variables for Configurable Paths

**Environment Variables Added**:
```bash
# Data Processing Configuration
DATA_DIRECTORY=/home/sraosamanthula/ZENLABS/RCL_Files
UPLOADS_DIRECTORY=/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend/uploads
REFERENCE_FILES_DIRECTORY=/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend/reference_files
STORAGE_DIRECTORY=/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend/storage
RESULT_SUFFIX=_processed
BATCH_PROCESSING=true
```

**Benefits**:
- Configurable file paths without code changes
- Easy deployment across different environments
- Centralized configuration management
- Platform shows current configuration in the UI

### 3. ✅ Directory Input with Default from Environment

**Feature**: Directory path input textbox with environment variable defaults

**Implementation**:
- Text input field for custom directory paths
- Pre-populated with default from `DATA_DIRECTORY` environment variable
- "Set Directory" button to validate and switch directories
- Real-time validation of directory existence and CSV file count
- Visual feedback for directory validation success/failure

**User Flow**:
1. Default directory loaded from environment on page load
2. User can modify directory path in text input
3. Click "Set Directory" to validate and switch
4. System shows directory validation results
5. File list updates automatically for new directory

### 4. ✅ Comprehensive Directory-Based Processing

**Feature**: Automated processing of all CSV files in specified directory

**Implementation**:
- Automatic discovery of all unprocessed CSV files in directory
- Real-time status tracking for each file
- Background processing with job queue management
- Reference file validation before processing starts
- Parallel processing of multiple files with different UCs

**Processing Flow**:
1. User selects UCs and uploads reference files
2. User sets directory path (or uses default)
3. System scans directory for CSV files
4. User clicks "Start Processing" to begin batch processing
5. All files processed automatically with selected UCs
6. Real-time status updates in database and UI
7. Results stored with configurable naming patterns

### 5. ✅ Enhanced Backend Architecture

**New API Endpoints**:
- `GET /config` - Returns platform configuration
- `POST /upload/set-directory` - Validates and sets processing directory
- `GET /upload/directory-files?directory=<path>` - Lists files in specific directory
- Enhanced `POST /batch/process-directory` - Processes all files in directory

**Database Enhancements**:
- UC-specific reference file management
- Improved job status tracking
- Enhanced file processing metrics
- Better error handling and logging

### 6. ✅ Improved Frontend User Experience

**UI Enhancements**:
- Integrated UC selection with reference file upload
- Configuration display showing current platform settings
- Directory input with validation feedback
- Real-time file list updates
- Enhanced status indicators and progress tracking
- Better error messaging and user guidance

**User Experience Improvements**:
- Single-page workflow - no separate upload steps
- Clear visual feedback for all operations
- Persistent reference file display
- Automatic directory file discovery
- Real-time processing status updates

## 🔧 Configuration Setup

### Environment Variables Setup

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Configure paths in `.env`**:
```bash
# Customize these paths for your deployment
DATA_DIRECTORY=/path/to/your/csv/files
UPLOADS_DIRECTORY=/path/to/uploads
REFERENCE_FILES_DIRECTORY=/path/to/reference/files
STORAGE_DIRECTORY=/path/to/results/storage
RESULT_SUFFIX=_processed
BATCH_PROCESSING=true
```

3. **Restart backend to apply changes**:
```bash
cd backend
uv run python main.py
```

## 🚀 Usage Workflow

### Complete Processing Workflow

1. **Access Platform**: Open http://localhost:3001

2. **Select Analysis Types**:
   - Check UC1 for sparse data analysis
   - Check UC4 for duplicate detection
   - Upload reference files directly in each UC card

3. **Set Processing Directory**:
   - Review default directory path
   - Modify if needed and click "Set Directory"
   - Verify CSV files are detected

4. **Start Processing**:
   - Ensure selected UCs have reference files
   - Click "Start Processing" to begin batch processing
   - Monitor real-time status updates

5. **Review Results**:
   - Check job status in the Jobs panel
   - Review processing results in storage directory
   - Download processed files with `_processed` suffix

### Example Processing Session

```bash
# 1. Platform shows configuration
Configuration:
- Data Directory: /home/user/data
- Storage: /home/user/storage
- Result Suffix: _processed

# 2. Select UCs and upload references
✓ UC1 Selected - Reference: high_quality_data.csv uploaded
✓ UC4 Selected - Reference: clean_data.csv uploaded

# 3. Directory processing
Directory: /home/user/data (15 CSV files found)
✓ All files will be processed with UC1 and UC4

# 4. Processing results
✓ Processing started for 15 files
✓ Real-time status updates in database
✓ Results saved to storage directory
```

## 📊 Technical Architecture

### Backend Components

1. **Configuration Management** (`main.py`):
   - Environment variable loading with `python-dotenv`
   - Directory validation and creation
   - Configuration endpoint for frontend

2. **Enhanced Upload Routes** (`routes/upload.py`):
   - Directory-based file discovery
   - UC-specific reference file management
   - Directory validation and switching

3. **Improved Batch Processing** (`routes/batch.py`):
   - Automatic file discovery
   - Reference file validation per UC
   - Background job queue management
   - Real-time status tracking

4. **Database Models** (`database.py`):
   - Enhanced ReferenceFile model
   - Improved job tracking
   - Better metrics collection

### Frontend Components

1. **Enhanced FileUpload Component**:
   - Integrated UC selection and reference upload
   - Directory input and validation
   - Real-time status updates
   - Configuration display

2. **API Integration**:
   - Configuration fetching
   - Directory validation
   - Reference file management
   - Real-time job updates

## 🔍 Monitoring and Debugging

### Log Files
- Backend logs: `backend/logs/`
- Application logs with structured logging
- Performance metrics and error tracking

### Status Monitoring
- Real-time job status in UI
- Database job records
- File processing metrics
- Error reporting and recovery

### Health Checks
- `GET /health` - Comprehensive health check
- `GET /config` - Configuration validation
- Directory accessibility checks
- Reference file validation

## 🎯 Key Benefits

1. **Streamlined Workflow**: Single-page processing workflow eliminates multiple steps
2. **Flexible Configuration**: Environment variables allow easy deployment customization
3. **Automated Processing**: Directory-based batch processing requires minimal user intervention
4. **Real-time Monitoring**: Live status updates and progress tracking
5. **Error Recovery**: Better error handling and user feedback
6. **Scalable Architecture**: Background processing and job queue management

## 📝 Migration Notes

### From Previous Version
- Reference files now managed per UC type
- Directory processing replaces individual file uploads
- Environment variables control all file paths
- Enhanced database schema for better tracking

### Configuration Changes Required
1. Update `.env` file with new directory variables
2. Restart backend to load new configuration
3. Frontend automatically adapts to new workflow
4. No database migration required (backward compatible)

## 🎉 Summary

The platform now provides a complete, streamlined workflow for data quality processing:

- **✅ Reference files at UC selection** - Upload directly where needed
- **✅ Environment-configurable paths** - Flexible deployment configuration  
- **✅ Directory input with defaults** - Easy directory management
- **✅ Automated batch processing** - Process all files automatically
- **✅ Real-time status tracking** - Live updates throughout processing
- **✅ Enhanced user experience** - Single-page, intuitive workflow

All user requirements have been fully implemented and tested. The platform is now production-ready with enterprise-grade configuration management and processing capabilities.
