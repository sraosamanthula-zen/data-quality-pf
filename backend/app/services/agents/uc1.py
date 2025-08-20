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
from agno.tools.file import FileTools
from agno.tools.reasoning import ReasoningTools
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

        # Create agent with Azure OpenAI and DuckDB tools
        self.agent = Agent(
            name="UC1 Incomplete Data Detection Agent",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[FileTools(), DuckDbTools(), ReasoningTools()],
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
                "ALWAYS use DuckDB for efficient data processing and export results as CSV.",
                "Focus on providing actionable insights about data completeness.",
            ],
            show_tool_calls=True,
            markdown=True,
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

            # Generate output filename
            input_path = Path(file_path)
            if unique_filename:
                output_filename = f"{unique_filename}_uc1_completeness.csv"
            else:
                output_filename = f"{input_path.stem}_uc1_completeness.csv"

            output_path = input_path.parent / output_filename

            # Prepare analysis instructions
            analysis_prompt = f"""
            Analyze the CSV file at '{file_path}' for data completeness issues.
            
            ANALYSIS REQUIREMENTS:
            1. Load the CSV into DuckDB
            2. Identify missing values, null values, and empty strings
            3. Calculate completeness metrics for each column
            4. Add the required flag columns to indicate data quality
            5. Export the enhanced dataset to '{output_path}'
            
            COMPLETENESS CRITERIA:
            - Missing values: NULL, empty strings, 'N/A', 'null', whitespace-only
            - Critical columns: Identify key columns that shouldn't have missing values
            - Row completeness: Calculate percentage of non-missing values per row
            
            OUTPUT FORMAT:
            - All original columns preserved
            - Added columns: is_incomplete, missing_value_count, completeness_score, quality_flag
            - Export as CSV to the specified output path
            
            Provide detailed analysis results including:
            - Total rows and columns
            - Completeness statistics by column
            - Overall quality assessment
            - Recommendations for data improvement
            """

            # Run the analysis
            _response = await self.agent.arun(analysis_prompt)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Verify output file was created
            if not output_path.exists():
                raise Exception("Output file was not created by the agent")

            # TODO: Parse the agent response to extract actual metrics
            # For now, return a basic result structure
            result = UC1AnalysisResult(
                job_id=job_id,
                input_file_path=str(file_path),
                output_file_path=str(output_path),
                analysis_timestamp=start_time,
                total_rows=0,  # Would be parsed from agent response
                total_columns=0,  # Would be parsed from agent response
                incomplete_rows=0,  # Would be parsed from agent response
                incomplete_percentage=0.0,  # Would be parsed from agent response
                columns_analyzed=[],  # Would be parsed from agent response
                sparse_columns=[],  # Would be parsed from agent response
                completeness_by_column={},  # Would be parsed from agent response
                overall_quality_score=0.0,  # Would be parsed from agent response
                quality_assessment="ANALYSIS_COMPLETED",  # Would be parsed from agent response
                recommendations=[],  # Would be parsed from agent response
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
