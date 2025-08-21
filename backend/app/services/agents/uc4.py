"""
UC4: Duplicate Records Detection and Removal Agent

This module contains the complete UC4 agent that:
1. Takes an input CSV file as dataset and optional reference file
2. Detects and rem            # Use same filename as input
            original_filename = input_path.name

            # Output to the outputs directory
            from app.core.config import settings
            output_path = settings.outputs_dir / original_filenameact duplicates using DuckDB
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
from pydantic import BaseModel, Field

# Local application imports
from .base_config import AgentConfig, log_agent_activity
from ..new_agents import uc4_agent


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
            tools=[DuckDbTools(inspect_queries=True, export_tables=True)],
            instructions=[
                "You are a DATA DEDUPLICATION EXPERT using DuckDB for efficient data processing.",
                "",
                "Your primary task is to detect and remove exact duplicate rows from CSV files.",
                "",
                "DATA WORKFLOW STRUCTURE:",
                "- INPUT FILES: Located in inputs/job_X/ subdirectories (read from these locations)",
                "- TEMP FILES: Write intermediate results to temp/job_X/uc_UC4/ subdirectories",
                "- OUTPUT FILES: Final results will be copied to outputs/job_X/ by the system",
                "",
                "FOLDER PROCESSING RULES:",
                "- ALWAYS read input CSV from the exact path provided in the prompt",
                "- ALWAYS write output CSV to the exact temp folder path provided in the prompt", 
                "- DO NOT write directly to any outputs/ folder - use temp/ folder only",
                "- The system will handle final copying from temp to outputs",
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
                "- Save cleaned data to new CSV file in specified temp folder",
                "- Report duplicate statistics",
                "- Provide quality improvement metrics",
                "- Include processing recommendations",
            ],
            show_tool_calls=True,
            markdown=True,
            reasoning=True,
            debug_mode=True,
        )

    async def detect_and_remove_duplicates(
        self,
        input_file_path: str,
        temp_folder: Path,
        reference_file_path: Optional[str] = None,
        unique_filename: Optional[str] = None,
    ) -> UC4AnalysisResult:
        """
        Detect and remove duplicates from a CSV file using DuckDB

        Args:
            input_file_path: Path to the CSV file to process (should be in inputs folder)
            temp_folder: Path to temp folder where outputs should be written
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
                    "temp_folder": str(temp_folder),
                },
            )

            # Validate input file
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Input file not found: {input_file_path}")

            # Ensure temp folder exists
            temp_folder.mkdir(parents=True, exist_ok=True)

            # Generate output filename - write to temp folder, not outputs
            input_path = Path(input_file_path)
            if unique_filename:
                output_filename = f"{unique_filename}.csv"
            else:
                # Use original filename with UC4 suffix
                output_filename = f"uc4_processed_{input_path.stem}.csv"
            
            # Output to the temp directory (NOT outputs directory)
            output_path = temp_folder / output_filename
            output_path.mkdir(parents=True, exist_ok=True)

            # Prepare analysis instructions
            analysis_prompt = f"""
            You are a data quality agent for UC4 (Duplicate Detection and Resolution).
            Analyze the CSV file at '{input_file_path}' for duplicate records and data quality issues.
            
            IMPORTANT: Read from the inputs folder, write to the temp folder.
            INPUT: '{input_path.parent}' (from inputs directory)
            OUTPUT: '{output_path.parent}' (to temp directory for intermediate processing)
            
            REQUIRED TASKS:
            1. Load the CSV file into DuckDB from: '{input_file_path}'
            2. Identify duplicate records using multiple detection methods
            3. Calculate duplicate statistics and metrics
            4. Add duplicate indicator columns
            5. Export the enhanced dataset to: '{output_path}'
            
            DUPLICATE DETECTION:
            - Exact duplicates: Rows with identical values across all columns
            - Partial duplicates: Rows with matching key fields but different values
            - Similar records: Rows with high similarity scores
            - Calculate duplicate percentages and counts
            
            REQUIRED OUTPUT COLUMNS (add to original data):
            - is_duplicate: BOOLEAN - true if row is a duplicate
            - duplicate_group_id: INTEGER - group ID for related duplicates
            - duplicate_count: INTEGER - number of duplicates in the group
            - similarity_score: FLOAT - similarity score (0-100)
            - duplicate_type: VARCHAR - 'EXACT', 'PARTIAL', 'SIMILAR', 'UNIQUE'
            
            Use DuckDB to process and export the data. Ensure all original columns are preserved.
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

            # Parse the input and output files to extract actual metrics
            try:
                import pandas as pd
                
                # Read original file for baseline metrics
                df_original = pd.read_csv(input_file_path)
                total_rows_original = len(df_original)
                total_columns = len(df_original.columns)
                
                # Read processed file for comparison
                df_processed = pd.read_csv(output_path)
                total_rows_processed = len(df_processed)
                
                # Calculate duplicate metrics
                duplicate_rows_removed = total_rows_original - total_rows_processed
                duplicate_percentage = (duplicate_rows_removed / total_rows_original * 100) if total_rows_original > 0 else 0.0
                data_reduction_percentage = duplicate_percentage
                
                # Calculate uniqueness and quality scores
                uniqueness_score = (total_rows_processed / total_rows_original * 100) if total_rows_original > 0 else 100.0
                quality_improvement_score = duplicate_percentage  # Higher is better for UC4
                
                # Generate recommendations
                recommendations = []
                if duplicate_percentage > 20:
                    recommendations.append("High duplicate rate detected - consider improving data collection processes")
                elif duplicate_percentage > 10:
                    recommendations.append("Moderate duplicate rate - implement duplicate prevention measures")
                elif duplicate_percentage > 0:
                    recommendations.append("Low duplicate rate detected - data quality is good")
                else:
                    recommendations.append("No duplicates found - excellent data quality")
                
                if data_reduction_percentage > 0:
                    recommendations.append(f"File size reduced by {data_reduction_percentage:.1f}% after deduplication")
                
            except Exception as parse_error:
                print(f"Could not parse output CSV metrics: {parse_error}")
                # Fallback to basic file analysis
                total_rows_original = 0
                total_rows_processed = 0
                total_columns = 0
                duplicate_rows_removed = 0
                duplicate_percentage = 0.0
                data_reduction_percentage = 0.0
                quality_improvement_score = 0.0
                uniqueness_score = 100.0
                recommendations = ["Analysis completed - review output file for detailed results"]

            result = UC4AnalysisResult(
                job_id=job_id,
                input_file_path=str(input_file_path),
                output_file_path=str(output_path),
                reference_file_path=reference_file_path,
                analysis_timestamp=start_time,
                total_rows_original=total_rows_original,
                total_rows_processed=total_rows_processed,
                total_columns=total_columns,
                duplicate_rows_removed=duplicate_rows_removed,
                duplicate_percentage=duplicate_percentage,
                exact_duplicates_found=duplicate_rows_removed,
                duplicate_patterns={},  # Could be enhanced with pattern analysis
                most_duplicated_records=[],  # Could be enhanced with specific record analysis
                data_reduction_percentage=data_reduction_percentage,
                quality_improvement_score=quality_improvement_score,
                uniqueness_score=uniqueness_score,
                processing_time_seconds=processing_time,
                success=True,
                error_message=None,
                recommendations=recommendations,
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
    file_path: str, 
    temp_folder: Path,
    reference_file_path: Optional[str] = None, 
    unique_filename: Optional[str] = None,
    input_file_: Path = None,
    output_dir_: Path = None,
) -> UC4AnalysisResult:
    """
    Run UC4 duplicate detection analysis

    Args:
        file_path: Path to file to analyze (in inputs folder)
        temp_folder: Path to temp folder for intermediate outputs
        reference_file_path: Optional reference file for comparison
        unique_filename: Optional unique filename to use for output file

    Returns:
        UC4AnalysisResult: Analysis results and output file path
    """
    agent = get_uc4_agent()

    await uc4_agent.arun(f"Process the input file path at {input_file_} and output directory path at {output_dir_}")


    # Use file_path as the primary input for UC4
    return await agent.detect_and_remove_duplicates(
        input_file_path=file_path,
        temp_folder=temp_folder,
        reference_file_path=reference_file_path,
        unique_filename=unique_filename,
    )
