import boto3
import json
from botocore.exceptions import ClientError

def check_and_setup_permissions():
    try:
        # Create IAM client
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get current identity
        identity = sts.get_caller_identity()
        print(f"\nRunning as: {identity['Arn']}")
        
        # Define required permissions
        required_permissions = {
            "bedrock": [
                "bedrock:GetAgent",
                "bedrock:ListAgents",
                "bedrock:ListAgentAliases",
                "bedrock:ListKnowledgeBases",
                "bedrock:GetKnowledgeBase",
                "bedrock:InvokeAgent",
                "bedrock:InvokeModel",
                "bedrock:RetrieveAndGenerate"
            ]
        }
        
        # Check permissions using policy simulation
        print("\nChecking permissions...")
        for service, actions in required_permissions.items():
            print(f"\n{service} permissions:")
            for action in actions:
                try:
                    response = iam.simulate_principal_policy(
                        PolicySourceArn=identity['Arn'],
                        ActionNames=[action]
                    )
                    decision = response['EvaluationResults'][0]['EvalDecision']
                    print(f"{action}: {'✅ Allowed' if decision == 'allowed' else '❌ Denied'}")
                except Exception as e:
                    print(f"{action}: ❌ Error - {str(e)}")
        
        # Create policy document
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "bedrock:*",
                    "Resource": "*"
                }
            ]
        }
        
        print("\nRequired policy document:")
        print(json.dumps(policy_document, indent=2))
        
        # Check if user has admin access to create policy
        try:
            admin_check = iam.simulate_principal_policy(
                PolicySourceArn=identity['Arn'],
                ActionNames=['iam:CreatePolicy']
            )
            can_create_policy = admin_check['EvaluationResults'][0]['EvalDecision'] == 'allowed'
            
            if can_create_policy:
                print("\nWould you like to create this policy? (y/n)")
                response = input().lower()
                if response == 'y':
                    policy_name = "BedrockFullAccessPolicy"
                    policy = iam.create_policy(
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(policy_document)
                    )
                    print(f"\n✅ Policy created: {policy['Policy']['Arn']}")
            else:
                print("\n❌ No permission to create IAM policies")
                print("Please provide this policy document to your AWS administrator")
        
        except Exception as e:
            print(f"\n❌ Error checking admin access: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    check_and_setup_permissions() 