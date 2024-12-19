import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def check_knowledge_base():
    try:
        # Create Bedrock clients
        bedrock_agent = boto3.client('bedrock-agent')
        agent_runtime = boto3.client('bedrock-agent-runtime')
        iam = boto3.client('iam')
        
        print("\nChecking knowledge base access...")
        kb_id = "PNHTCCOLZO"
        agent_id = "HQK9MJB3ZA"
        
        try:
            # Get current identity
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"\nRunning as: {identity['Arn']}")
            
            # Try to get agent details first
            print("\nAttempting to get agent details...")
            try:
                agent_response = bedrock_agent.get_agent(
                    agentId=agent_id
                )
                print("\nAgent Details:")
                print(f"Status: {agent_response.get('status', 'Unknown')}")
                print(f"Created: {agent_response.get('creationDateTime', 'Unknown')}")
                print(f"Last Updated: {agent_response.get('lastUpdatedDateTime', 'Unknown')}")
                print(f"Role ARN: {agent_response.get('agentResourceRoleArn', 'Unknown')}")
                
                # If we have a role ARN, check its permissions
                role_arn = agent_response.get('agentResourceRoleArn')
                if role_arn:
                    print(f"\nChecking agent role permissions for: {role_arn}")
                    try:
                        role_name = role_arn.split('/')[-1]
                        role_response = iam.get_role(RoleName=role_name)
                        print(f"Role exists: {role_response['Role']['RoleName']}")
                        
                        # Get role policies
                        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
                        print("\nAttached Policies:")
                        for policy in attached_policies['AttachedPolicies']:
                            print(f"- {policy['PolicyName']}")
                            
                    except ClientError as e:
                        print(f"❌ Error checking role: {str(e)}")
                
            except ClientError as e:
                print(f"❌ Error getting agent details: {str(e)}")
            
            # Try to list agent aliases
            print("\nChecking agent aliases...")
            try:
                aliases_response = bedrock_agent.list_agent_aliases(
                    agentId=agent_id
                )
                print("Agent Aliases:")
                for alias in aliases_response.get('agentAliases', []):
                    print(f"\nAlias ID: {alias.get('agentAliasId')}")
                    print(f"Status: {alias.get('status', 'Unknown')}")
                    print(f"Created: {alias.get('creationDateTime')}")
            except ClientError as e:
                print(f"❌ Error listing aliases: {str(e)}")
            
            # Try to list knowledge bases
            print("\nAttempting to list knowledge bases...")
            try:
                kb_response = bedrock_agent.list_knowledge_bases()
                for kb in kb_response.get('knowledgeBases', []):
                    print(f"\nKnowledge Base: {kb.get('knowledgeBaseId')}")
                    print(f"Status: {kb.get('status', 'Unknown')}")
                    if kb.get('knowledgeBaseId') == kb_id:
                        print("🔍 Found target knowledge base!")
            except ClientError as e:
                print(f"❌ Error listing knowledge bases: {str(e)}")
            
        except ClientError as e:
            print(f"\n❌ Error accessing services: {str(e)}")
            if hasattr(e, 'response'):
                error_details = json.dumps(e.response, indent=2, cls=DateTimeEncoder)
                print(f"Error details: {error_details}")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    check_knowledge_base() 