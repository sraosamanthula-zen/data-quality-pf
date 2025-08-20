"""
UC1: Incomplete Data Detection Agent using DuckDB

This module contains an agent that:
1. Takes a reference CSV file as input
2. Analyzes the data for incomplete/sparse patterns using DuckDB
3. Outputs a CSV file with an added flag column indicating incomplete data
4. Returns results in Pydantic model format
"""

# Standard library imports
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Third-party imports
from agno.agent import Agent
from agno.tools.duckdb import DuckDbTools
from agno.tools.file import FileTools
from agno.tools.reasoning import ReasoningTools
from pydantic import BaseModel, Field

# Local application imports
from .base_config import AgentConfig, log_agent_activity


class UC1AnalysisResult(BaseModel):
    """Pydantic model for UC1 analysis results"""
    job_id: str = Field(description="Unique identifier for this analysis job")
    input_file_path: str = Field(description="Path to the input reference CSV file")
    output_file_path: str = Field(description="Path to the output CSV file with flag columns")
    analysis_timestamp: datetime = Field(description="When the analysis was performed")
    
    # Analysis metrics
    total_rows: int = Field(description="Total number of rows in the dataset")
    total_columns: int = Field(description="Total number of columns in the dataset")
    incomplete_rows: int = Field(description="Number of rows flagged as incomplete")
    incomplete_percentage: float = Field(description="Percentage of rows that are incomplete")
    
    # Column-level analysis
    columns_analyzed: list[str] = Field(description="List of all columns analyzed")
    sparse_columns: list[str] = Field(description="Columns with high missing value rates")
    completeness_by_column: Dict[str, float] = Field(description="Completeness percentage for each column")
    
    # Flags and recommendations
    overall_quality_score: float = Field(description="Overall data quality score (0-100)")
    quality_assessment: str = Field(description="Overall quality assessment (EXCELLENT/GOOD/FAIR/POOR)")
    recommendations: list[str] = Field(description="List of recommendations for data improvement")
    
    # Processing details
    processing_time_seconds: float = Field(description="Time taken to complete the analysis")
    success: bool = Field(description="Whether the analysis completed successfully")
    error_message: Optional[str] = Field(default=None, description="Error message if analysis failed")


class UC1DuckDBAgent:
    """
    UC1 Agent that uses DuckDB tools to analyze CSV files for incomplete data
    and outputs a CSV with flag columns indicating data completeness issues.
    """
    
    def __init__(self):
        self.agent_name = "UC1_DuckDB_Agent"
        self.config = AgentConfig()
        
        # Create agent with Azure OpenAI and DuckDB tools
        self.agent = Agent(
            name="UC1 Incomplete Data Detection Agent",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                DuckDbTools(),
                ReasoningTools()
            ],
            instructions=[
                "You are a DATA COMPLETENESS EXPERT using DuckDB for efficient data analysis.",
                "",
                "Your primary task is to analyze CSV files for incomplete/sparse data patterns and create output files with flag columns.",
                "",
                "CORE RESPONSIBILITIES:",
                "1. Load CSV files into DuckDB for analysis",
                "2. Identify rows with missing or incomplete data",
                "3. Calculate completeness metrics for each column",
                "4. Add flag columns to indicate data quality issues",
                "5. Export results as a new CSV file",
                "",
                "DATA COMPLETENESS ANALYSIS CRITERIA:",
                "- A row is considered INCOMPLETE if it has missing values in critical columns",
                "- A column is considered SPARSE if >30% of values are missing",
                "- Use statistical analysis to identify patterns in missing data",
                "",
                "REQUIRED OUTPUT COLUMNS TO ADD:",
                "- 'is_incomplete': Boolean flag (TRUE/FALSE) indicating if row has missing critical data",
                "- 'missing_value_count': Number of missing values in the row",
                "- 'completeness_score': Row-level completeness percentage (0-100)",
                "- 'quality_flag': Text flag ('COMPLETE', 'PARTIAL', 'INCOMPLETE')",
                "",
                "DUCKDB BEST PRACTICES:",
                "- Use efficient SQL queries for analysis",
                "- Leverage DuckDB's CSV reading capabilities",
                "- Use window functions for advanced analytics",
                "- Optimize queries for large datasets",
                "",
                "ALWAYS use DuckDB tools for all data operations - NO pandas or other libraries.",
                "Return detailed analysis results including file paths and metrics."
            ],
            show_tool_calls=True
        )
    
    async def analyze_file_for_completeness(
        self, 
        reference_file_path: str,
        output_directory: str = None,
        missing_threshold: float = 0.3,
        unique_filename: str = None
    ) -> UC1AnalysisResult:
        """
        Analyze a CSV file for incomplete data and output results with flag columns.
        
        Args:
            reference_file_path: Path to the input CSV file to analyze
            output_directory: Directory to save the output CSV file (optional)
            missing_threshold: Threshold for considering a column sparse (default 30%)
            
        Returns:
            UC1AnalysisResult: Pydantic model with analysis results and file paths
        """
        start_time = datetime.now()
        job_id = str(uuid.uuid4())
        
        log_agent_activity(self.agent_name, "Starting UC1 completeness analysis", {
            "input_file": reference_file_path,
            "job_id": job_id,
            "missing_threshold": missing_threshold
        })
        
        try:
            # Validate input file
            if not os.path.exists(reference_file_path):
                raise FileNotFoundError(f"Reference file not found: {reference_file_path}")
            
            # Set up output directory and file path using environment variables
            if output_directory is None:
                # Use OUTPUT_DIRECTORY environment variable
                output_directory = os.getenv("OUTPUT_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files/output_data")
                
                # Ensure output directory exists
                os.makedirs(output_directory, exist_ok=True)
            
            # Use unique filename if provided, otherwise generate simple name from input
            if unique_filename:
                # Remove any existing extension and add _processed.csv
                base_name = unique_filename.split('.')[0] if '.' in unique_filename else unique_filename
                output_filename = f"{base_name}_processed.csv"
            else:
                # Use simple naming: original_filename_processed.csv
                input_filename = Path(reference_file_path).stem
                output_filename = f"{input_filename}_processed.csv"
            
            output_file_path = os.path.join(output_directory, output_filename)
            
            # Create analysis prompt for the agent
            analysis_prompt = f"""
            PERFORM UC1 INCOMPLETE DATA ANALYSIS using DuckDB:
            
            Input file: {reference_file_path}
            Output file: {output_file_path}
            Missing threshold: {missing_threshold} (30% = sparse column)
            Job ID: {job_id}
            
            STEP 1: LOAD AND EXPLORE DATA
            - Use DuckDB to read the CSV file
            - Get basic statistics (row count, column count, data types)
            - Identify all columns and their data types
            
            STEP 2: ANALYZE MISSING DATA PATTERNS
            - Calculate missing value counts for each column
            - Identify columns that exceed the missing threshold
            - Calculate row-level missing value counts
            - Determine completeness percentages
            
            STEP 3: CREATE FLAG COLUMNS
            Add these new columns to the dataset:
            - 'is_incomplete': TRUE if row has any missing critical values, FALSE otherwise
            - 'missing_value_count': Count of missing values in each row
            - 'completeness_score': Percentage of non-missing values in each row (0-100)
            - 'quality_flag': 'COMPLETE' (100%), 'PARTIAL' (50-99%), 'INCOMPLETE' (<50%)
            
            STEP 4: CALCULATE OVERALL METRICS
            - Total and percentage of incomplete rows
            - Quality score for the entire dataset
            - List of sparse columns (>30% missing)
            - Column-wise completeness percentages
            
            STEP 5: EXPORT RESULTS
            - Save the enhanced dataset with flag columns to: {output_file_path}
            - Ensure all original data is preserved
            - Add the new flag columns as the last columns
            
            STEP 6: GENERATE RECOMMENDATIONS
            Based on your analysis, provide specific recommendations for:
            - Which columns need attention
            - Data collection improvements
            - Data quality enhancement strategies
            
            Use ONLY DuckDB tools for all operations. Provide detailed results including:
            - File paths (input and output)
            - All calculated metrics and statistics
            - Clear recommendations for data improvement
            """
            
            # Execute the analysis using the agent
            agent_response = await self.agent.arun(analysis_prompt)
            
            # TODO: Parse agent_response to extract actual metrics from DuckDB analysis
            # The agent_response contains the detailed analysis results that need to be parsed
            # to populate the result metrics. For now, using placeholder values.
            _ = agent_response  # Acknowledge that response will be used for parsing metrics
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result object
            result = UC1AnalysisResult(
                job_id=job_id,
                input_file_path=reference_file_path,
                output_file_path=output_file_path,
                analysis_timestamp=start_time,
                total_rows=0,  # Will be filled by actual DuckDB analysis
                total_columns=0,  # Will be filled by actual DuckDB analysis
                incomplete_rows=0,  # Will be filled by actual DuckDB analysis
                incomplete_percentage=0.0,  # Will be filled by actual DuckDB analysis
                columns_analyzed=[],  # Will be filled by actual DuckDB analysis
                sparse_columns=[],  # Will be filled by actual DuckDB analysis
                completeness_by_column={},  # Will be filled by actual DuckDB analysis
                overall_quality_score=0.0,  # Will be filled by actual DuckDB analysis
                quality_assessment="PENDING",  # Will be filled by actual DuckDB analysis
                recommendations=[],  # Will be filled by actual DuckDB analysis
                processing_time_seconds=processing_time,
                success=True,
                error_message=None
            )
            
            log_agent_activity(self.agent_name, "UC1 analysis completed successfully", {
                "job_id": job_id,
                "output_file": output_file_path,
                "processing_time": processing_time
            })
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            log_agent_activity(self.agent_name, "UC1 analysis failed", {
                "job_id": job_id,
                "error": error_msg,
                "processing_time": processing_time
            })
            
            # Return error result
            return UC1AnalysisResult(
                job_id=job_id,
                input_file_path=reference_file_path,
                output_file_path="",
                analysis_timestamp=start_time,
                total_rows=0,
                total_columns=0,
                incomplete_rows=0,
                incomplete_percentage=0.0,
                columns_analyzed=[],
                sparse_columns=[],
                completeness_by_column={},
                overall_quality_score=0.0,
                quality_assessment="ERROR",
                recommendations=[f"Analysis failed: {error_msg}"],
                processing_time_seconds=processing_time,
                success=False,
                error_message=error_msg
            )


def get_uc1_duckdb_agent() -> UC1DuckDBAgent:
    """Factory function to create UC1 DuckDB agent instance"""
    return UC1DuckDBAgent()


# Example usage function
async def run_uc1_duckdb_analysis(
    reference_file_path: str, 
    output_directory: str = None,
    missing_threshold: float = 0.3
) -> UC1AnalysisResult:
    """
    Convenience function to run UC1 analysis with DuckDB
    
    Args:
        reference_file_path: Path to the CSV file to analyze
        output_directory: Directory to save results (optional)
        missing_threshold: Threshold for sparse column detection
        
    Returns:
        UC1AnalysisResult: Complete analysis results
    """
    agent = get_uc1_duckdb_agent()
    return await agent.analyze_file_for_completeness(
        reference_file_path, 
        output_directory, 
        missing_threshold
    )
