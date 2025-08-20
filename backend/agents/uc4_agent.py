"""
Simplified UC4 analysis function for route integration
Updated to use DuckDB-based agent for improved performance and duplicate removal
"""

from .uc4_duckdb_agent import get_uc4_duckdb_agent, UC4AnalysisResult


async def run_uc4_analysis(file_path: str, reference_file_path: str = None, unique_filename: str = None) -> UC4AnalysisResult:
    """
    Run UC4 duplicate detection analysis using DuckDB
    
    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison
        unique_filename: Optional unique filename to use for output file
        
    Returns:
        UC4AnalysisResult: Pydantic model with analysis results and output file path
    """
    agent = get_uc4_duckdb_agent()
    
    # Use file_path as the primary input for UC4
    input_file = file_path
    
    return await agent.detect_and_remove_duplicates(
        input_file_path=input_file,
        reference_file_path=reference_file_path,
        unique_filename=unique_filename
    )