import boto3
import json
from botocore.exceptions import ClientError
import uuid

def check_iam_permissions():
    """Check specific IAM permissions for Bedrock Agent operations"""
    iam = boto3.client('iam')
    try:
        # Get current user/role
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"\nRunning as: {identity['Arn']}")
        
        # Simulate Bedrock Agent permissions with specific resources
        required_actions = [
            {
                "action": "bedrock:InvokeAgent",
                "resource": "arn:aws:bedrock:ap-southeast-2:831926595680:agent/HQK9MJB3ZA"
            },
            {
                "action": "bedrock:InvokeModel",
                "resource": "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-v2"
            },
            {
                "action": "bedrock:RetrieveAndGenerate",
                "resource": "arn:aws:bedrock:ap-southeast-2:831926595680:knowledge-base/PNHTCCOLZO"
            }
        ]
        
        print("\nChecking IAM permissions with specific resources...")
        for check in required_actions:
            try:
                response = iam.simulate_principal_policy(
                    PolicySourceArn=identity['Arn'],
                    ActionNames=[check['action']],
                    ResourceArns=[check['resource']]
                )
                result = response['EvaluationResults'][0]
                print(f"{check['action']} on {check['resource']}: "
                      f"{'✅ Allowed' if result['EvalDecision'] == 'allowed' else '❌ Denied'}")
                if result['EvalDecision'] != 'allowed':
                    print(f"Denial reason: {result.get('EvalDecisionDetails', 'No details available')}")
            except Exception as e:
                print(f"{check['action']}: ❌ Error checking permission - {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking permissions: {str(e)}")
        return False

def test_cli_permissions():
    try:
        # First check permissions
        if not check_iam_permissions():
            return
        
        # Create session and clients
        session = boto3.Session(region_name="ap-southeast-2")
        agent_runtime = session.client('bedrock-agent-runtime')
        
        # Test specific agent and knowledge base
        agent = {
            "id": "HQK9MJB3ZA",
            "alias": "7XTWPEBICD",
            "kb_id": "PNHTCCOLZO"
        }
        print(f"\nTesting agent access to knowledge base...")
        print(f"Agent ID: {agent['id']}")
        print(f"Alias ID: {agent['alias']}")
        print(f"Knowledge Base ID: {agent['kb_id']}")
        
        # Test agent invocation with knowledge base query
        print("\n1. Testing agent invocation...")
        response = agent_runtime.invoke_agent(
            agentId=agent['id'],
            agentAliasId=agent['alias'],
            sessionId=str(uuid.uuid4()),
            inputText=f"search knowledge base {agent['kb_id']} for: test query",
            enableTrace=True
        )
        print("✅ Agent invocation successful")
        
        # Process response stream
        print("\n2. Processing response stream...")
        for event in response.get("completion", []):
            try:
                event_type = list(event.keys())[0] if event else "unknown"
                print(f"\nEvent type: {event_type}")
                
                # Handle bytes objects in the event data
                event_data = event.get(event_type, {})
                if isinstance(event_data, bytes):
                    try:
                        event_data = event_data.decode('utf-8')
                        # Try to parse as JSON if possible
                        try:
                            event_data = json.loads(event_data)
                        except:
                            pass
                    except:
                        event_data = str(event_data)
                
                # Convert the event data to a string if it's not JSON serializable
                if not isinstance(event_data, (dict, list, str, int, float, bool, type(None))):
                    event_data = str(event_data)
                
                print(f"Event data: {json.dumps(event_data, indent=2)}")
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                print(f"Raw event: {str(event)}")
                    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', '')
        print(f"❌ Agent error: {error_code} - {error_message}")
        print(f"Error type: {type(e)}")
        if hasattr(e, 'response'):
            print(f"Error response: {json.dumps(e.response, indent=2)}")
            
        # Additional debugging for permission issues
        if error_code == 'AccessDeniedException' or '403' in str(e):
            print("\n🔍 Permission Issue Detected:")
            print("1. Verify that your IAM role/user has the AmazonBedrockFullAccess policy")
            print("2. Check if the agent and knowledge base are in the same AWS account")
            print("3. Verify that the agent is properly configured with the knowledge base")
            print("4. Ensure the agent is in an 'Active' state")
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    test_cli_permissions() 