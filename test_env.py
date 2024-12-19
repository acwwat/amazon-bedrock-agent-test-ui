import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check environment variables
print("Checking environment variables...")
print(f"BEDROCK_AGENT_ID: {os.environ.get('BEDROCK_AGENT_ID')}")
print(f"BEDROCK_AGENT_ALIAS_ID: {os.environ.get('BEDROCK_AGENT_ALIAS_ID')}")
print(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION')}") 