"""
Simplified UC1 analysis function for route integration
Updated to use DuckDB-based agent for improved performance
"""

from .uc1_duckdb_agent import get_uc1_duckdb_agent, UC1AnalysisResult


async def run_uc1_analysis(file_path: str, reference_file_path: str = None) -> UC1AnalysisResult:
    """
    Run UC1 incomplete data analysis using DuckDB
    
    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison (now used as main input)
        
    Returns:
        UC1AnalysisResult: Pydantic model with analysis results and output file path
    """
    agent = get_uc1_duckdb_agent()
    
    # Use reference_file_path as the primary input, fallback to file_path
    input_file = reference_file_path if reference_file_path else file_path
    
    return await agent.analyze_file_for_completeness(input_file)
