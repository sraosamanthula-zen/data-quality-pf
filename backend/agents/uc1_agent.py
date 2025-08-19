"""
Simplified UC1 analysis function for route integration
"""

from .uc1_sparse_data_agent import get_uc1_agent


async def run_uc1_analysis(file_path: str, reference_file_path: str = None):
    """
    Run UC1 sparse data analysis
    
    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison
        
    Returns:
        Analysis results dictionary
    """
    agent = get_uc1_agent()
    
    if reference_file_path:
        return await agent.analyze_file_with_reference(file_path, reference_file_path)
    else:
        return await agent.run_complete_uc1_analysis(file_path)
