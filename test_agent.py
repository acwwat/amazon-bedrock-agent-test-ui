import os
from dotenv import load_dotenv
import boto3
from services import bedrock_agent_runtime
import uuid

# Load environment variables
load_dotenv()

# Get config from environment variables
agent_id = os.environ.get("BEDROCK_AGENT_ID")
agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")

# Configure AWS session with explicit region
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
session = boto3.Session(region_name='ap-southeast-2')

def test_agent():
    # Create a test session ID
    session_id = str(uuid.uuid4())
    
    # Test prompt
    test_prompt = "What products do you sell?"
    
    try:
        # Invoke agent
        response = bedrock_agent_runtime.invoke_agent(
            agent_id,
            agent_alias_id,
            session_id,
            test_prompt
        )
        
        print("\nTest Prompt:", test_prompt)
        print("\nAgent Response:", response["output_text"])
        print("\nCitations:", len(response["citations"]))
        
        return True
        
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Bedrock Agent...")
    success = test_agent()
    print("\nTest completed:", "Success" if success else "Failed") 