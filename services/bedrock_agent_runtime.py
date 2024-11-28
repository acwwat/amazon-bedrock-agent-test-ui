import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

def invoke_agent(agent_id, agent_alias_id, session_id, prompt):
    try:
        # Load credentials from .env
        load_dotenv()
        
        # Create session with credentials from environment variables
        session = boto3.Session(
            region_name='ap-southeast-2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        client = session.client('bedrock-agent-runtime')
        
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            enableTrace=True,
            sessionId=session_id,
            inputText=prompt,
        )

        output_text = ""
        citations = []
        trace = {}

        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                output_text += chunk["bytes"].decode()
                
                if "attribution" in chunk:
                    citations.extend(chunk["attribution"]["citations"])

            if "trace" in event:
                trace_data = event["trace"]["trace"]
                for trace_type in trace_data:
                    if trace_type not in trace:
                        trace[trace_type] = []
                    trace[trace_type].append(trace_data[trace_type])

    except ClientError as e:
        raise

    return {
        "output_text": output_text,
        "citations": citations,
        "trace": trace
    }
