"""
Test script for the new UC1 DuckDB agent
"""
import asyncio
import os
import sys

# Add the backend directory to Python path
sys.path.append('/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend')

from agents.uc1_duckdb_agent import run_uc1_duckdb_analysis


async def test_uc1_duckdb_agent():
    """Test the new UC1 DuckDB agent with a sample CSV file"""
    
    # Use one of the existing CSV files as test input
    test_file = "/home/sraosamanthula/ZENLABS/RCL_Files/Quality_Sugar_Daily_Article_Data-133565508097027794.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🧪 Testing UC1 DuckDB Agent with file: {os.path.basename(test_file)}")
    print("="*60)
    
    try:
        # Run the analysis
        result = await run_uc1_duckdb_analysis(test_file)
        
        print("✅ UC1 Analysis Completed Successfully!")
        print("📊 Results:")
        print(f"   Job ID: {result.job_id}")
        print(f"   Input File: {result.input_file_path}")
        print(f"   Output File: {result.output_file_path}")
        print(f"   Processing Time: {result.processing_time_seconds:.2f} seconds")
        print(f"   Success: {result.success}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Show some metrics (when they're populated by actual analysis)
        print(f"   Total Rows: {result.total_rows}")
        print(f"   Total Columns: {result.total_columns}")
        print(f"   Incomplete Rows: {result.incomplete_rows}")
        print(f"   Quality Score: {result.overall_quality_score}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up basic environment variables for testing
    os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"
    
    # Run the test
    asyncio.run(test_uc1_duckdb_agent())
