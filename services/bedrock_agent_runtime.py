import boto3
import json
import os
from dotenv import load_dotenv

class BedrockAgentRuntime:
    def __init__(self):
        load_dotenv()
        
        # Debug prints
        print("Environment variables:")
        print(f"BEDROCK_AGENT_ID: {os.getenv('BEDROCK_AGENT_ID')}")
        print(f"BEDROCK_AGENT_ALIAS_ID: {os.getenv('BEDROCK_AGENT_ALIAS_ID')}")
        print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")
        
        # Get required environment variables
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        if not self.agent_id:
            raise ValueError("BEDROCK_AGENT_ID environment variable is not set")
            
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        if not self.agent_alias_id:
            raise ValueError("BEDROCK_AGENT_ALIAS_ID environment variable is not set")
            
        # Initialize AWS session
        self.session = boto3.Session(
            region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2')
        )
        
        self.bedrock_agent_runtime = self.session.client(
            service_name='bedrock-agent-runtime'
        )

    def invoke_agent(self, prompt):
        try:
            print(f"\nSending prompt: {prompt}")
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId='test-session-01',
                inputText=prompt
            )
            
            print("\nRaw response:", response)
            
            # Get the completion event stream
            event_stream = response.get('completion')
            if not event_stream:
                return "No completion stream in response"
            
            # Handle EventStream response
            full_response = ""
            for event in event_stream:
                print("\nStream event:", event)  # Debug
                
                # Check if we have completion data
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode()
                        print("Decoded chunk:", text)  # Debug
                        full_response += text
                    
                # Check for citations
                if 'citations' in event:
                    citations = event['citations']
                    print("Citations:", citations)  # Debug
                    full_response += "\n\nSources:\n"
                    for citation in citations:
                        full_response += f"- {citation}\n"
            
            print("\nFinal response:", full_response)  # Debug
            return full_response if full_response else "No response content received"
            
        except Exception as e:
            print(f"\nError invoking agent: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return f"Sorry, I encountered an error: {str(e)}"
