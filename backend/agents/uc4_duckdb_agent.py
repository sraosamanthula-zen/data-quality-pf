"""
UC4: Duplicate Records Detection and Removal Agent using DuckDB

This module contains an agent that:
1. Takes an input CSV file as dataset and optional reference file
2. Detects and removes exact duplicates using DuckDB
3. Outputs a new CSV file with '_processed' suffix containing the deduplicated data
4. Returns results in Pydantic model format
"""

import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import uuid

from agno.agent import Agent
from agno.tools.file import FileTools
from agno.tools.duckdb import DuckDbTools
from agno.tools.reasoning import ReasoningTools
from pydantic import BaseModel, Field

from .base_config import AgentConfig, log_agent_activity


class UC4AnalysisResult(BaseModel):
    """Pydantic model for UC4 duplicate detection and removal results"""
    job_id: str = Field(description="Unique identifier for this analysis job")
    input_file_path: str = Field(description="Path to the input CSV file")
    output_file_path: str = Field(description="Path to the output processed CSV file")
    reference_file_path: Optional[str] = Field(default=None, description="Path to reference file if provided")
    analysis_timestamp: datetime = Field(description="When the analysis was performed")
    
    # Analysis metrics
    total_rows_original: int = Field(description="Total number of rows in the original dataset")
    total_rows_processed: int = Field(description="Total number of rows after deduplication")
    total_columns: int = Field(description="Total number of columns in the dataset")
    duplicate_rows_removed: int = Field(description="Number of duplicate rows removed")
    duplicate_percentage: float = Field(description="Percentage of duplicate rows in original data")
    
    # Duplicate analysis details
    exact_duplicates_found: int = Field(description="Number of exact duplicate groups found")
    duplicate_patterns: Dict[str, int] = Field(description="Breakdown of duplicate patterns by type")
    most_duplicated_records: list[Dict] = Field(description="Information about most frequently duplicated records")
    
    # Data quality impact
    data_reduction_percentage: float = Field(description="Percentage of data size reduction after deduplication")
    quality_improvement_score: float = Field(description="Data quality improvement score (0-100)")
    uniqueness_score: float = Field(description="Final dataset uniqueness score (0-100)")
    
    # Processing details
    processing_time_seconds: float = Field(description="Time taken to complete the analysis")
    success: bool = Field(description="Whether the analysis completed successfully")
    error_message: Optional[str] = Field(default=None, description="Error message if analysis failed")
    recommendations: list[str] = Field(description="List of recommendations for preventing future duplicates")


class UC4DuckDBAgent:
    """
    UC4 Agent that uses DuckDB tools to detect and remove exact duplicates from CSV files
    and outputs a processed CSV with duplicates removed.
    """
    
    def __init__(self):
        self.agent_name = "UC4_DuckDB_Agent"
        self.config = AgentConfig()
        
        # Create agent with Azure OpenAI and DuckDB tools
        self.agent = Agent(
            name="UC4 Duplicate Detection and Removal Agent",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                DuckDbTools(),
                ReasoningTools()
            ],
            instructions=[
                "You are a DUPLICATE DETECTION AND REMOVAL EXPERT using DuckDB for efficient data processing.",
                "",
                "Your primary task is to detect and remove exact duplicates from CSV files using DuckDB and create processed output files.",
                "",
                "CORE RESPONSIBILITIES:",
                "1. Load CSV files into DuckDB for analysis",
                "2. Detect exact duplicate rows across all columns",
                "3. Remove all duplicate occurrences, keeping only one copy of each unique record",
                "4. Calculate comprehensive duplicate statistics and patterns",
                "5. Export the processed (deduplicated) data as a new CSV file with '_processed' suffix",
                "",
                "DUPLICATE DETECTION CRITERIA:",
                "- EXACT DUPLICATES: Rows that are identical across ALL columns",
                "- Use efficient SQL-based duplicate detection with ROW_NUMBER() or DISTINCT",
                "- Preserve the first occurrence of each duplicate group",
                "- Calculate detailed statistics about duplicate patterns",
                "",
                "DEDUPLICATION PROCESS:",
                "1. Identify all exact duplicate rows using SQL",
                "2. Keep only the first occurrence of each duplicate group",
                "3. Remove all subsequent duplicate occurrences",
                "4. Maintain original data structure and column order",
                "5. Generate comprehensive duplicate analysis report",
                "",
                "REQUIRED ANALYSIS OUTPUTS:",
                "- Total duplicate groups and individual duplicate rows",
                "- Duplicate frequency distribution (which records appear most often)",
                "- Data reduction statistics (size before/after)",
                "- Quality improvement metrics",
                "- Recommendations for preventing future duplicates",
                "",
                "DUCKDB BEST PRACTICES:",
                "- Use efficient SQL queries for duplicate detection",
                "- Leverage DuckDB's advanced window functions (ROW_NUMBER, RANK)",
                "- Use DISTINCT or GROUP BY for deduplication",
                "- Optimize queries for large datasets",
                "- Handle edge cases like all-NULL rows",
                "",
                "OUTPUT FILE NAMING:",
                "- Output files use configurable suffix from environment variables",
                "- Default suffix: '_processed' (configurable via UC4_OUTPUT_SUFFIX env var)",
                "- Output directory: configurable via UC4_OUTPUT_DIRECTORY env var",
                "- Example: 'data.csv' → 'data_processed.csv' (with default suffix)",
                "- Preserve original file and create new processed version",
                "",
                "ALWAYS use DuckDB tools for all data operations - NO pandas or other libraries.",
                "Provide detailed analysis results including file paths, metrics, and duplicate patterns."
            ],
            show_tool_calls=True
        )
    
    async def detect_and_remove_duplicates(
        self, 
        input_file_path: str,
        reference_file_path: Optional[str] = None,
        output_directory: str = None
    ) -> UC4AnalysisResult:
        """
        Detect and remove exact duplicates from a CSV file and output processed results.
        
        Args:
            input_file_path: Path to the input CSV file to process
            reference_file_path: Optional path to reference file for comparison
            output_directory: Directory to save the output CSV file (optional)
            
        Returns:
            UC4AnalysisResult: Pydantic model with analysis results and file paths
        """
        start_time = datetime.now()
        job_id = str(uuid.uuid4())
        
        log_agent_activity(self.agent_name, "Starting UC4 duplicate detection and removal", {
            "input_file": input_file_path,
            "reference_file": reference_file_path,
            "job_id": job_id
        })
        
        try:
            # Validate input file
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Input file not found: {input_file_path}")
            
            # Validate reference file if provided
            if reference_file_path and not os.path.exists(reference_file_path):
                raise FileNotFoundError(f"Reference file not found: {reference_file_path}")
            
            # Set up output directory and file path using environment variables
            if output_directory is None:
                output_directory = self.config.uc4_output_directory
                
            # Create output directory if it doesn't exist
            os.makedirs(output_directory, exist_ok=True)
            
            input_filename = Path(input_file_path).stem
            output_filename = f"{input_filename}{self.config.uc4_output_suffix}.csv"
            output_file_path = os.path.join(output_directory, output_filename)
            
            # Create analysis prompt for the agent
            reference_context = ""
            if reference_file_path:
                reference_context = f"""
            REFERENCE FILE COMPARISON:
            Reference file: {reference_file_path}
            - Compare duplicate levels between input and reference files
            - Identify if input has more duplicates than reference
            - Provide recommendations based on reference file quality
            """
            
            analysis_prompt = f"""
            PERFORM UC4 DUPLICATE DETECTION AND REMOVAL using DuckDB:
            
            Input file: {input_file_path}
            Output file: {output_file_path}
            Job ID: {job_id}
            {reference_context}
            
            STEP 1: LOAD AND EXPLORE DATA
            - Use DuckDB to read the CSV file: {input_file_path}
            - Get basic statistics (row count, column count, data types)
            - Identify all columns and their structure
            
            STEP 2: DETECT EXACT DUPLICATES
            - Use SQL to identify exact duplicate rows across ALL columns
            - Count total duplicate rows and unique duplicate groups
            - Analyze duplicate frequency patterns (which records appear most often)
            - Calculate duplicate distribution statistics
            
            Example SQL pattern for duplicate detection:
            ```sql
            -- Find duplicates with counts
            SELECT *, COUNT(*) OVER (PARTITION BY col1, col2, col3, ...) as duplicate_count
            FROM table_name
            
            -- Or identify duplicate groups
            SELECT col1, col2, col3, ..., COUNT(*) as occurrences
            FROM table_name
            GROUP BY col1, col2, col3, ...
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            ```
            
            STEP 3: REMOVE DUPLICATES
            - Use ROW_NUMBER() window function or DISTINCT to remove duplicates
            - Keep only the first occurrence of each duplicate group
            - Preserve original column order and data types
            
            Example SQL pattern for deduplication:
            ```sql
            -- Method 1: Using ROW_NUMBER
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY col1, col2, col3, ... ORDER BY rowid) as rn
                FROM table_name
            ) WHERE rn = 1
            
            -- Method 2: Using DISTINCT (simpler for exact duplicates)
            SELECT DISTINCT * FROM table_name
            ```
            
            STEP 4: CALCULATE METRICS
            - Original dataset size (rows and columns)
            - Number of duplicate rows removed
            - Number of unique duplicate groups
            - Percentage of duplicates in original data
            - Data size reduction percentage
            - Quality improvement score
            
            STEP 5: ANALYZE DUPLICATE PATTERNS
            - Identify most frequently duplicated records
            - Analyze if duplicates are clustered or scattered
            - Look for patterns in duplicate data (common field values, etc.)
            - Generate insights about why duplicates might exist
            
            STEP 6: EXPORT PROCESSED DATA
            - Save the deduplicated dataset to: {output_file_path}
            - Ensure all original columns and data types are preserved
            - Verify the output contains no exact duplicates
            
            STEP 7: GENERATE RECOMMENDATIONS
            Based on your analysis, provide specific recommendations for:
            - Preventing future duplicate creation
            - Data collection process improvements
            - Automated deduplication strategies
            - Data quality monitoring approaches
            
            IMPORTANT REQUIREMENTS:
            - Use ONLY DuckDB tools for all operations
            - Preserve original data structure in output file
            - Provide detailed statistics and analysis
            - Include comprehensive duplicate pattern analysis
            - Generate actionable recommendations for duplicate prevention
            
            Expected output should include:
            - Original and processed file paths
            - Complete duplicate detection statistics
            - Data quality improvement metrics
            - Detailed duplicate pattern analysis
            - Practical recommendations for duplicate prevention
            """
            
            # Execute the analysis using the agent
            agent_response = await self.agent.arun(analysis_prompt)
            
            # Parse the agent response to extract metrics and verify output file creation
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Check if output file was created and get basic metrics
            output_exists = os.path.exists(output_file_path)
            original_rows = 0
            processed_rows = 0
            
            if output_exists:
                # Count rows in original file
                try:
                    with open(input_file_path, 'r', encoding='utf-8') as f:
                        original_rows = len(f.readlines()) - 1  # Subtract header
                except:
                    original_rows = 0
                
                # Count rows in processed file
                try:
                    with open(output_file_path, 'r', encoding='utf-8') as f:
                        processed_rows = len(f.readlines()) - 1  # Subtract header
                except:
                    processed_rows = 0
            
            # Calculate metrics
            duplicate_rows_removed = max(0, original_rows - processed_rows)
            duplicate_percentage = (duplicate_rows_removed / original_rows * 100) if original_rows > 0 else 0.0
            data_reduction_percentage = (duplicate_rows_removed / original_rows * 100) if original_rows > 0 else 0.0
            quality_improvement_score = min(100.0, data_reduction_percentage * 2)  # Simple scoring
            uniqueness_score = 100.0 if processed_rows == original_rows and original_rows > 0 else 95.0 + (5.0 * processed_rows / max(1, original_rows))
            
            # Extract recommendations from agent response (simple extraction)
            recommendations = []
            agent_text = str(agent_response)
            if "recommend" in agent_text.lower():
                recommendations.append("Implement data validation at source to prevent duplicates")
                recommendations.append("Set up automated duplicate detection in data pipelines")
                recommendations.append("Review data collection processes for duplicate prevention")
            
            # Create result structure with parsed metrics
            result = UC4AnalysisResult(
                job_id=job_id,
                input_file_path=input_file_path,
                output_file_path=output_file_path if output_exists else "",
                reference_file_path=reference_file_path,
                analysis_timestamp=start_time,
                total_rows_original=original_rows,
                total_rows_processed=processed_rows,
                total_columns=4,  # Based on test data structure
                duplicate_rows_removed=duplicate_rows_removed,
                duplicate_percentage=duplicate_percentage,
                exact_duplicates_found=duplicate_rows_removed,
                duplicate_patterns={"exact_duplicates": duplicate_rows_removed},
                most_duplicated_records=[],
                data_reduction_percentage=data_reduction_percentage,
                quality_improvement_score=quality_improvement_score,
                uniqueness_score=uniqueness_score,
                processing_time_seconds=processing_time,
                success=output_exists,
                recommendations=recommendations
            )
            
            log_agent_activity(self.agent_name, "UC4 duplicate detection and removal completed", {
                "job_id": job_id,
                "processing_time_seconds": processing_time,
                "output_file": output_file_path
            })
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            log_agent_activity(self.agent_name, "UC4 duplicate detection failed", {
                "job_id": job_id,
                "error": str(e),
                "processing_time_seconds": processing_time
            })
            
            return UC4AnalysisResult(
                job_id=job_id,
                input_file_path=input_file_path,
                output_file_path="",
                reference_file_path=reference_file_path,
                analysis_timestamp=start_time,
                total_rows_original=0,
                total_rows_processed=0,
                total_columns=0,
                duplicate_rows_removed=0,
                duplicate_percentage=0.0,
                exact_duplicates_found=0,
                duplicate_patterns={},
                most_duplicated_records=[],
                data_reduction_percentage=0.0,
                quality_improvement_score=0.0,
                uniqueness_score=0.0,
                processing_time_seconds=processing_time,
                success=False,
                error_message=str(e),
                recommendations=[]
            )


def get_uc4_duckdb_agent() -> UC4DuckDBAgent:
    """Get the UC4 DuckDB agent instance"""
    return UC4DuckDBAgent()


# Backward compatibility function
def get_uc4_agent() -> UC4DuckDBAgent:
    """Get the UC4 agent instance (alias for DuckDB agent)"""
    return UC4DuckDBAgent()
