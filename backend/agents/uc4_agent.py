"""
Simplified UC4 analysis function for route integration
Updated to use DuckDB-based agent for improved performance and duplicate removal
"""

from .uc4_duckdb_agent import get_uc4_duckdb_agent, UC4AnalysisResult


async def run_uc4_analysis(file_path: str, reference_file_path: str = None, output_directory: str = None):
    """
    Run UC4 duplicate detection and removal analysis using DuckDB
    
    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison
        output_directory: Optional output directory (uses UC4_OUTPUT_DIRECTORY env var if not provided)
        
    Returns:
        UC4AnalysisResult: Pydantic model with analysis results
    """
    agent = get_uc4_duckdb_agent()
    
    # Run duplicate detection and removal
    return await agent.detect_and_remove_duplicates(
        input_file_path=file_path,
        reference_file_path=reference_file_path,
        output_directory=output_directory
    )