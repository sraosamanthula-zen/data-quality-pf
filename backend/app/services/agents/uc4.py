"""
UC4: Duplicate Records Detection and Removal Agent

This module contains the complete UC4 agent that:
1. Takes an input CSV file as dataset and optional reference file
2. Detects and removes exact duplicates using DuckDB
3. Outputs a new CSV file with '_processed' suffix containing the deduplicated data
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


class UC4AnalysisResult(BaseModel):
    """Pydantic model for UC4 duplicate detection and removal results"""

    job_id: str = Field(description="Unique identifier for this analysis job")
    input_file_path: str = Field(description="Path to the input CSV file")
    output_file_path: str = Field(description="Path to the output processed CSV file")
    reference_file_path: Optional[str] = Field(
        default=None, description="Path to reference file if provided"
    )
    analysis_timestamp: datetime = Field(description="When the analysis was performed")

    # Analysis metrics
    total_rows_original: int = Field(
        description="Total number of rows in the original dataset"
    )
    total_rows_processed: int = Field(
        description="Total number of rows after deduplication"
    )
    total_columns: int = Field(description="Total number of columns in the dataset")
    duplicate_rows_removed: int = Field(description="Number of duplicate rows removed")
    duplicate_percentage: float = Field(
        description="Percentage of duplicate rows in original data"
    )

    # Duplicate analysis details
    exact_duplicates_found: int = Field(
        description="Number of exact duplicate groups found"
    )
    duplicate_patterns: Dict[str, int] = Field(
        description="Breakdown of duplicate patterns by type"
    )
    most_duplicated_records: list[Dict] = Field(
        description="Information about most frequently duplicated records"
    )

    # Data quality impact
    data_reduction_percentage: float = Field(
        description="Percentage of data size reduction after deduplication"
    )
    quality_improvement_score: float = Field(
        description="Data quality improvement score (0-100)"
    )
    uniqueness_score: float = Field(
        description="Final dataset uniqueness score (0-100)"
    )

    # Processing details
    processing_time_seconds: float = Field(
        description="Time taken to complete the analysis"
    )
    success: bool = Field(description="Whether the analysis completed successfully")
    error_message: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )
    recommendations: list[str] = Field(
        description="List of recommendations for preventing future duplicates"
    )


class UC4Agent:
    """
    UC4 Agent that uses DuckDB tools to detect and remove exact duplicates from CSV files
    and outputs a processed CSV with duplicates removed.
    """

    def __init__(self):
        self.agent_name = "UC4_Agent"
        self.config = AgentConfig()

        # Get model configuration from settings
        from app.core.config import settings

        # Create agent with configurable model and DuckDB tools
        self.agent = Agent(
            name="UC4 Duplicate Detection and Removal Agent",
            model=self.config.get_azure_openai_model(temperature=settings.agent_temperature),
            tools=[FileTools(), DuckDbTools(), ReasoningTools()],
            instructions=[
                "You are a DATA DEDUPLICATION EXPERT using DuckDB for efficient data processing.",
                "",
                "Your primary task is to detect and remove exact duplicate rows from CSV files.",
                "",
                "IMPORTANT CONSTRAINTS:",
                f"- NEVER load more than {settings.max_prompt_rows} rows of raw data into your prompt/context",
                "- Always use DuckDB aggregations and summaries for analysis",
                "- Use GROUP BY and COUNT() to identify duplicates efficiently",
                "- Focus on statistical summaries rather than raw data inspection",
                "",
                "CORE RESPONSIBILITIES:",
                "1. Load CSV files into DuckDB for efficient processing",
                "2. Identify exact duplicate rows using DuckDB GROUP BY queries",
                "3. Remove duplicates while preserving data integrity",
                "4. Generate cleaned CSV files with statistics",
                "5. Provide comprehensive duplicate analysis reports",
                "",
                "DUCKDB USAGE PATTERNS:",
                "- Create table from CSV: CREATE TABLE data AS SELECT * FROM 'file.csv'",
                "- Find duplicates: SELECT *, COUNT(*) as count FROM data GROUP BY ALL HAVING count > 1",
                "- Remove duplicates: SELECT DISTINCT * FROM data",
                "- Get stats: SELECT COUNT(*) as total, COUNT(DISTINCT *) as unique FROM data",
                "",
                "OUTPUT REQUIREMENTS:",
                "- Save cleaned data to new CSV file",
                "- Report duplicate statistics",
                "- Provide quality improvement metrics",
                "- Include processing recommendations",
            ],
            show_tool_calls=True,
            markdown=True,
        )

    async def detect_and_remove_duplicates(
        self,
        input_file_path: str,
        reference_file_path: Optional[str] = None,
        unique_filename: Optional[str] = None,
    ) -> UC4AnalysisResult:
        """
        Detect and remove duplicates from a CSV file using DuckDB

        Args:
            input_file_path: Path to the CSV file to process
            reference_file_path: Optional reference file for comparison
            unique_filename: Optional unique filename for output file

        Returns:
            UC4AnalysisResult: Analysis results including output file path
        """
        start_time = datetime.now()
        job_id = str(uuid.uuid4())

        try:
            log_agent_activity(
                self.agent_name,
                f"Starting UC4 duplicate detection for {input_file_path}",
                {
                    "job_id": job_id,
                    "input_file": input_file_path,
                    "reference_file": reference_file_path,
                },
            )

            # Validate input file
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Input file not found: {input_file_path}")

            # Generate output filename with original name preserved
            input_path = Path(input_file_path)
            original_stem = input_path.stem
            if unique_filename:
                # Extract original filename from unique filename if it contains timestamp prefix
                if unique_filename.startswith(('UC1_', 'UC4_')):
                    # Remove UC prefix and timestamp to get original name
                    parts = unique_filename.split('_', 3)
                    if len(parts) >= 4:
                        original_stem = parts[3].replace('.csv', '')
                    else:
                        original_stem = unique_filename.replace('.csv', '')
                else:
                    original_stem = unique_filename.replace('.csv', '')
            
            # Format: original_name_job_X_uc4_processed.csv
            job_short_id = job_id[:8]  # Use first 8 characters of UUID
            output_filename = f"{original_stem}_job_{job_short_id}_uc4_processed.csv"

            output_path = input_path.parent / output_filename

            # Prepare analysis instructions
            analysis_prompt = f"""
            Analyze and remove duplicates from the CSV file at '{input_file_path}'.
            
            DEDUPLICATION REQUIREMENTS:
            1. Load the CSV into DuckDB
            2. Identify exact duplicate rows (identical across all columns)
            3. Remove all duplicates, keeping only the first occurrence of each unique record
            4. Calculate comprehensive duplicate statistics
            5. Export the deduplicated dataset to '{output_path}'
            
            DUPLICATE DETECTION STRATEGY:
            - Use SQL with ROW_NUMBER() OVER (PARTITION BY all_columns ORDER BY rowid) to identify duplicates
            - Keep rows where ROW_NUMBER = 1 (first occurrence)
            - Calculate before/after statistics
            
            ANALYSIS REQUIREMENTS:
            - Count total rows before and after
            - Identify duplicate patterns and most frequent duplicates
            - Calculate data reduction percentage
            - Provide quality improvement metrics
            
            OUTPUT FORMAT:
            - Export only unique rows (deduplicated data) to the specified output path
            - Preserve all original columns and data types
            - Maintain original column order
            
            Provide detailed analysis results including:
            - Total duplicate rows removed
            - Percentage of duplicates in original data
            - Data quality improvement metrics
            - Recommendations for preventing future duplicates
            """

            # Add reference file context if provided
            if reference_file_path and os.path.exists(reference_file_path):
                analysis_prompt += f"""
                
                REFERENCE FILE CONTEXT:
                - Reference file provided: '{reference_file_path}'
                - Use reference file to understand expected data patterns
                - Compare duplicate rates between input and reference data
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
            result = UC4AnalysisResult(
                job_id=job_id,
                input_file_path=str(input_file_path),
                output_file_path=str(output_path),
                reference_file_path=reference_file_path,
                analysis_timestamp=start_time,
                total_rows_original=0,  # Would be parsed from agent response
                total_rows_processed=0,  # Would be parsed from agent response
                total_columns=0,  # Would be parsed from agent response
                duplicate_rows_removed=0,  # Would be parsed from agent response
                duplicate_percentage=0.0,  # Would be parsed from agent response
                exact_duplicates_found=0,  # Would be parsed from agent response
                duplicate_patterns={},  # Would be parsed from agent response
                most_duplicated_records=[],  # Would be parsed from agent response
                data_reduction_percentage=0.0,  # Would be parsed from agent response
                quality_improvement_score=0.0,  # Would be parsed from agent response
                uniqueness_score=0.0,  # Would be parsed from agent response
                processing_time_seconds=processing_time,
                success=True,
                error_message=None,
                recommendations=[],  # Would be parsed from agent response
            )

            log_agent_activity(
                self.agent_name,
                "UC4 duplicate detection completed successfully",
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
                f"UC4 duplicate detection failed: {error_msg}",
                {"job_id": job_id, "error": error_msg},
                "error",
            )

            return UC4AnalysisResult(
                job_id=job_id,
                input_file_path=str(input_file_path),
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
                error_message=error_msg,
                recommendations=[],
            )


# Global instance
_uc4_agent = None


def get_uc4_agent() -> UC4Agent:
    """Get the global UC4 agent instance"""
    global _uc4_agent
    if _uc4_agent is None:
        _uc4_agent = UC4Agent()
    return _uc4_agent


async def run_uc4_analysis(
    file_path: str, reference_file_path: Optional[str] = None, unique_filename: Optional[str] = None
) -> UC4AnalysisResult:
    """
    Run UC4 duplicate detection analysis

    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison
        unique_filename: Optional unique filename to use for output file

    Returns:
        UC4AnalysisResult: Analysis results and output file path
    """
    agent = get_uc4_agent()

    # Use file_path as the primary input for UC4
    return await agent.detect_and_remove_duplicates(
        input_file_path=file_path,
        reference_file_path=reference_file_path,
        unique_filename=unique_filename,
    )
