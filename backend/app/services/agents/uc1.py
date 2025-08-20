"""
UC1: Incomplete Data Detection Agent

This module contains the complete UC1 agent that:
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
from pydantic import BaseModel, Field

# Local application imports
from .base_config import AgentConfig, log_agent_activity


class UC1AnalysisResult(BaseModel):
    """Pydantic model for UC1 analysis results"""

    job_id: str = Field(description="Unique identifier for this analysis job")
    input_file_path: str = Field(description="Path to the input reference CSV file")
    output_file_path: str = Field(
        description="Path to the output CSV file with flag columns"
    )
    analysis_timestamp: datetime = Field(description="When the analysis was performed")

    # Analysis metrics
    total_rows: int = Field(description="Total number of rows in the dataset")
    total_columns: int = Field(description="Total number of columns in the dataset")
    incomplete_rows: int = Field(description="Number of rows flagged as incomplete")
    incomplete_percentage: float = Field(
        description="Percentage of rows that are incomplete"
    )

    # Column-level analysis
    columns_analyzed: list[str] = Field(description="List of all columns analyzed")
    sparse_columns: list[str] = Field(
        description="Columns with high missing value rates"
    )
    completeness_by_column: Dict[str, float] = Field(
        description="Completeness percentage for each column"
    )

    # Flags and recommendations
    overall_quality_score: float = Field(
        description="Overall data quality score (0-100)"
    )
    quality_assessment: str = Field(
        description="Overall quality assessment (EXCELLENT/GOOD/FAIR/POOR)"
    )
    recommendations: list[str] = Field(
        description="List of recommendations for data improvement"
    )

    # Processing details
    processing_time_seconds: float = Field(
        description="Time taken to complete the analysis"
    )
    success: bool = Field(description="Whether the analysis completed successfully")
    error_message: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )


class UC1Agent:
    """
    UC1 Agent that uses DuckDB tools to analyze CSV files for incomplete data
    and outputs a CSV with flag columns indicating data completeness issues.
    """

    def __init__(self):
        self.agent_name = "UC1_Agent"
        self.config = AgentConfig()

        # Get model configuration from settings
        from app.core.config import settings
        
        # Create agent with configurable model and DuckDB tools
        self.agent = Agent(
            name="UC1 Incomplete Data Detection Agent",
            model=self.config.get_azure_openai_model(temperature=settings.agent_temperature),
            tools=[DuckDbTools(inspect_queries=True, export_tables=True)],
            instructions=[
                "You are a DATA COMPLETENESS EXPERT using DuckDB for efficient data analysis.",
                "",
                "Your primary task is to analyze CSV files for incomplete/sparse data patterns and create output files with flag columns.",
                "",
                "IMPORTANT CONSTRAINTS:",
                f"- NEVER load more than {settings.max_prompt_rows} rows of raw data into your prompt/context",
                "- Always use DuckDB aggregations and summaries for analysis",
                "- Use LIMIT clauses when selecting sample data",
                "- Focus on statistical summaries rather than raw data inspection",
                "",
                "CORE RESPONSIBILITIES:",
                "1. Load CSV files into DuckDB for analysis",
                "2. Identify rows with missing or incomplete data using aggregated queries",
                "3. Calculate completeness metrics for each column using COUNT() and statistical functions",
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
                "ALWAYS use DuckDB for efficient data processing and export results as CSV.",
                "Focus on providing actionable insights about data completeness.",
            ],
            show_tool_calls=True,
            markdown=True,
            reasoning=True,
        )

    async def analyze_file_for_completeness(
        self, file_path: str, unique_filename: Optional[str] = None
    ) -> UC1AnalysisResult:
        """
        Analyze a CSV file for data completeness using DuckDB

        Args:
            file_path: Path to the CSV file to analyze
            unique_filename: Optional unique filename for output file

        Returns:
            UC1AnalysisResult: Analysis results including output file path
        """
        start_time = datetime.now()
        job_id = str(uuid.uuid4())

        try:
            log_agent_activity(
                self.agent_name,
                f"Starting UC1 analysis for {file_path}",
                {"job_id": job_id, "input_file": file_path},
            )

            # Validate input file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")

            # Generate output filename with original name preserved
            input_path = Path(file_path)
            if unique_filename:
                # Extract original filename from unique filename if it contains timestamp prefix
                if unique_filename.startswith(('UC1_', 'UC4_')):
                    # Remove UC prefix and timestamp to get original name
                    parts = unique_filename.split('_', 3)
                    if len(parts) >= 4:
                        # Use extracted original name
                        pass
                    else:
                        # Use unique filename as is
                        pass
                else:
                    # Use filename as is
                    pass
            
            # Use same filename as input
            original_filename = input_path.name

            # Output to the outputs directory
            from app.core.config import settings
            output_path = settings.outputs_dir / original_filename

            # Prepare analysis instructions
            analysis_prompt = f"""
            You are a data quality agent for UC1 (Completeness Analysis). 
            Analyze the CSV file at '{file_path}' for data completeness and quality issues.
            
            REQUIRED TASKS:
            1. Load the CSV file into DuckDB
            2. Analyze each column for missing/incomplete data
            3. Calculate completeness metrics
            4. Add quality indicator columns
            5. Export the enhanced dataset to '{output_path}'
            
            COMPLETENESS ANALYSIS:
            - Identify missing values: NULL, empty strings, 'N/A', 'null', whitespace-only
            - Calculate column-wise completeness percentages
            - Determine row-level completeness scores
            - Flag rows with significant missing data
            
            REQUIRED OUTPUT COLUMNS (add to original data):
            - is_incomplete: BOOLEAN - true if row has significant missing data
            - missing_value_count: INTEGER - count of missing values in the row
            - completeness_score: FLOAT - percentage of complete fields (0-100)
            - quality_flag: VARCHAR - 'HIGH', 'MEDIUM', 'LOW' based on completeness
            
            Use DuckDB to process and export the data. Ensure all original columns are preserved.
            """

            # Run the analysis
            _response = await self.agent.arun(analysis_prompt)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Verify output file was created
            if not output_path.exists():
                raise Exception("Output file was not created by the agent")

            # Parse the output CSV to extract actual metrics
            try:
                import pandas as pd
                df = pd.read_csv(output_path)
                
                total_rows = len(df)
                total_columns = len(df.columns)
                
                # Extract analysis columns if they exist
                incomplete_rows = 0
                if 'is_incomplete' in df.columns:
                    incomplete_rows = df['is_incomplete'].sum() if pd.api.types.is_numeric_dtype(df['is_incomplete']) else len(df[df['is_incomplete']])
                
                incomplete_percentage = (incomplete_rows / total_rows * 100) if total_rows > 0 else 0.0
                
                # Calculate completeness by column (original columns only)
                completeness_by_column = {}
                analysis_columns = {'is_incomplete', 'missing_value_count', 'completeness_score', 'quality_flag'}
                original_columns = [col for col in df.columns if col not in analysis_columns]
                
                for col in original_columns:
                    non_null_count = df[col].notna().sum()
                    completeness = (non_null_count / total_rows * 100) if total_rows > 0 else 0.0
                    completeness_by_column[col] = completeness
                
                # Calculate overall quality score
                if 'completeness_score' in df.columns:
                    overall_quality_score = df['completeness_score'].mean()
                else:
                    overall_quality_score = sum(completeness_by_column.values()) / len(completeness_by_column) if completeness_by_column else 0.0
                
                # Identify sparse columns (< 80% complete)
                sparse_columns = [col for col, completeness in completeness_by_column.items() if completeness < 80.0]
                
                # Generate quality assessment
                if overall_quality_score >= 90:
                    quality_assessment = "EXCELLENT"
                elif overall_quality_score >= 75:
                    quality_assessment = "GOOD"
                elif overall_quality_score >= 50:
                    quality_assessment = "FAIR"
                else:
                    quality_assessment = "POOR"
                
                # Generate recommendations
                recommendations = []
                if sparse_columns:
                    recommendations.append(f"Consider improving data collection for sparse columns: {', '.join(sparse_columns[:3])}")
                if incomplete_percentage > 20:
                    recommendations.append("High percentage of incomplete rows detected - review data quality processes")
                if overall_quality_score < 75:
                    recommendations.append("Overall data quality is below recommended threshold - implement data validation")
                
            except Exception as parse_error:
                print(f"Could not parse output CSV metrics: {parse_error}")
                # Fallback to basic file analysis
                total_rows = 0
                total_columns = 0
                incomplete_rows = 0
                incomplete_percentage = 0.0
                completeness_by_column = {}
                overall_quality_score = 0.0
                quality_assessment = "ANALYSIS_COMPLETED"
                sparse_columns = []
                recommendations = ["Analysis completed - review output file for detailed results"]

            result = UC1AnalysisResult(
                job_id=job_id,
                input_file_path=str(file_path),
                output_file_path=str(output_path),
                analysis_timestamp=start_time,
                total_rows=total_rows,
                total_columns=total_columns,
                incomplete_rows=incomplete_rows,
                incomplete_percentage=incomplete_percentage,
                columns_analyzed=list(completeness_by_column.keys()),
                sparse_columns=sparse_columns,
                completeness_by_column=completeness_by_column,
                overall_quality_score=overall_quality_score,
                quality_assessment=quality_assessment,
                recommendations=recommendations,
                processing_time_seconds=processing_time,
                success=True,
                error_message=None,
            )

            log_agent_activity(
                self.agent_name,
                "UC1 analysis completed successfully",
                {
                    "job_id": job_id,
                    "output_file": str(output_path),
                    "processing_time": processing_time,
                },
            )

            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            log_agent_activity(
                self.agent_name,
                f"UC1 analysis failed: {error_msg}",
                {"job_id": job_id, "error": error_msg},
                "error",
            )

            return UC1AnalysisResult(
                job_id=job_id,
                input_file_path=str(file_path),
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
                quality_assessment="FAILED",
                recommendations=[],
                processing_time_seconds=processing_time,
                success=False,
                error_message=error_msg,
            )


# Global instance
_uc1_agent = None


def get_uc1_agent() -> UC1Agent:
    """Get the global UC1 agent instance"""
    global _uc1_agent
    if _uc1_agent is None:
        _uc1_agent = UC1Agent()
    return _uc1_agent


async def run_uc1_analysis(
    file_path: str,
    reference_file_path: Optional[str] = None,
    unique_filename: Optional[str] = None,
) -> UC1AnalysisResult:
    """
    Run UC1 incomplete data analysis

    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison (now used as main input)
        unique_filename: Optional unique filename to use for output file

    Returns:
        UC1AnalysisResult: Analysis results and output file path
    """
    agent = get_uc1_agent()

    # Use reference_file_path as the primary input, fallback to file_path
    input_file = reference_file_path if reference_file_path else file_path

    return await agent.analyze_file_for_completeness(
        input_file, unique_filename=unique_filename
    )
