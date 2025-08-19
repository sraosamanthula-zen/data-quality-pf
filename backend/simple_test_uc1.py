"""
Simple test for UC1 DuckDB agent
"""
import asyncio
import os

# Set up environment variables
os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"

from agents.uc1_duckdb_agent import UC1DuckDBAgent

async def simple_test():
    print("🧪 Testing UC1 DuckDB Agent initialization...")
    
    try:
        agent = UC1DuckDBAgent()
        print("✅ Agent created successfully")
        print(f"   Agent name: {agent.agent_name}")
        
        # Test with a sample file path (don't actually run analysis yet)
        test_file = "/home/sraosamanthula/ZENLABS/RCL_Files/Quality_Sugar_Daily_Article_Data-133565508097027794.csv"
        
        if os.path.exists(test_file):
            print(f"✅ Test file found: {os.path.basename(test_file)}")
            print("📝 Agent ready for analysis (not running actual analysis in this test)")
        else:
            print("ℹ️  Test file not found, but agent initialization successful")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
