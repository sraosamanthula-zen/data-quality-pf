"""
Simplified UC4 analysis function for route integration
"""

from .uc4_duplicate_agent import get_uc4_agent


async def run_uc4_analysis(file_path: str, reference_file_path: str = None):
    """
    Run UC4 duplicate detection analysis
    
    Args:
        file_path: Path to file to analyze
        reference_file_path: Optional reference file for comparison
        
    Returns:
        Analysis results dictionary
    """
    agent = get_uc4_agent()
    
    if reference_file_path:
        return await agent.analyze_duplicates_with_reference(file_path, reference_file_path)
    else:
        return await agent.detect_duplicates(file_path)
