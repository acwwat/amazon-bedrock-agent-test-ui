import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime
import uuid

def test_permission(client, sts_client, action, resource, message, output_file):
    try:
        response = client.simulate_principal_policy(
            PolicySourceArn=sts_client.get_caller_identity()['Arn'],
            ActionNames=[action],
            ResourceArns=[resource] if resource else None
        )
        is_allowed = all(decision['EvalDecision'] == 'allowed' for decision in response['EvaluationResults'])
        result = f"{message}: {'[ALLOWED]' if is_allowed else '[DENIED]'}"
        print(result)
        output_file.write(result + "\n")
        return is_allowed
    except Exception as e:
        error_msg = f"{message}: [ERROR] - {str(e)}"
        print(error_msg)
        output_file.write(error_msg + "\n")
        return False

def test_specific_permission(client, sts_client, action, resource, output_file):
    try:
        response = client.simulate_principal_policy(
            PolicySourceArn=sts_client.get_caller_identity()['Arn'],
            ActionNames=[action],
            ResourceArns=[resource],
            ContextEntries=[
                {
                    'ContextKeyName': 'aws:ResourceTag/Owner',
                    'ContextKeyValues': ['bedrock'],
                    'ContextKeyType': 'string'
                }
            ]
        )
        result = response['EvaluationResults'][0]
        decision = result['EvalDecision']
        matched = result.get('MatchedStatements', [])
        
        output = [
            f"\n{action} on {resource}:",
            f"Decision: {decision}",
            f"Matched statements: {len(matched)}",
            "Evaluation details:"
        ]
        
        if matched:
            for stmt in matched:
                output.extend([
                    f"- Policy: {stmt.get('SourcePolicyId')}",
                    f"  Effect: {stmt.get('SourcePolicyType')}",
                    f"  Statement: {json.dumps(stmt.get('PolicyStatement', {}), indent=2)}"
                ])
        else:
            output.append("No matching policy statements found")
            
        if 'EvalDecisionDetails' in result:
            output.append("Decision details:")
            for key, value in result['EvalDecisionDetails'].items():
                output.append(f"  {key}: {value}")
        
        print("\n".join(output))
        output_file.write("\n".join(output) + "\n")
        
        return decision == 'allowed'
    except Exception as e:
        error_msg = f"Error testing {action} on {resource}: {str(e)}"
        print(error_msg)
        output_file.write(error_msg + "\n")
        return False

def test_bedrock_permissions():
    session = boto3.Session(region_name="ap-southeast-2")
    agent_client = session.client('bedrock-agent-runtime')
    runtime_client = session.client('bedrock-runtime')
    
    try:
        print("\nTesting permissions...")
        
        # Test agent invocation
        response = agent_client.invoke_agent(
            agentId="HQK9MJB3ZA",
            agentAliasId="7XTWPEBICD",
            sessionId=str(uuid.uuid4()),
            inputText="test query",
            enableTrace=True
        )
        print("✅ Agent invocation successful")
        
        # Try to process the response
        try:
            print("\nProcessing response stream...")
            for event in response.get("completion", []):
                event_type = list(event.keys())[0] if event else "unknown"
                print(f"\nReceived event type: {event_type}")
                
                if "chunk" in event:
                    chunk = event["chunk"]
                    print("✅ Response chunk received")
                    if "bytes" in chunk:
                        print(f"Text: {chunk['bytes'].decode()}")
                    if "attribution" in chunk:
                        print("✅ Attribution information received")
                        
                if "trace" in event:
                    print("✅ Trace information received")
                    trace_data = event["trace"]["trace"]
                    print(f"Trace types: {list(trace_data.keys())}")
                    
        except Exception as e:
            print(f"❌ Error processing response: {str(e)}")
            print(f"Error type: {type(e)}")
            if hasattr(e, 'response'):
                print(f"Error response: {e.response}")
            
    except client.exceptions.ValidationException as e:
        print(f"❌ Validation error: {str(e)}")
    except client.exceptions.AccessDeniedException as e:
        print(f"❌ Access denied: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_bedrock_permissions() 