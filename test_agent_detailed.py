import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def test_agent_detailed():
    print("Testing Bedrock Agent in detail...")
    
    # Load environment variables
    load_dotenv()
    agent_id = os.environ.get("BEDROCK_AGENT_ID")
    agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID")
    
    try:
        # Create Bedrock client
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')
        
        # Test invocation
        test_prompt = "What products do you sell?"
        print(f"\nSending test prompt: {test_prompt}")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId="test-session",
            inputText=test_prompt
        )
        
        print("\nResponse:")
        print(json.dumps(response, indent=2, cls=DateTimeEncoder))
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_agent_detailed() 