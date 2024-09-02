#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_stacks.dynamodb_stack import DynamodbStack
from cdk_stacks.agent_lambda_stack import AgentLambdasStack
from cdk_stacks.bedrock_stack import BedrockStack
from cdk_stacks.aoss_stack import AossStack
from cdk_stacks.knowledgebase_stack import KnowledgeBaseStack
from cdk_stacks.api_stack import ApiStack

app = cdk.App()

ACCOUNT_NUMBER="637423569624"
REGION="us-west-2"

env_for_demo = cdk.Environment(account=ACCOUNT_NUMBER, region=REGION)

dynamodb_stack = DynamodbStack(app, "DynamodbStack", env=env_for_demo)

aoss_stack = AossStack(app, "AossStack", env=env_for_demo)

kb_stack = KnowledgeBaseStack(app, "KnowledgebaseStack", env=env_for_demo)

agent_lambda_stack = AgentLambdasStack(app, "AgentLambdaStack", env=env_for_demo)

bedrock_stack = BedrockStack(app, "BedrockStack", env=env_for_demo)

apigw_stack = ApiStack(app, "ApiStack", env=env_for_demo)

aoss_stack.add_dependency(dynamodb_stack)
kb_stack.add_dependency(aoss_stack)
agent_lambda_stack.add_dependency(kb_stack)
bedrock_stack.add_dependency(agent_lambda_stack)
apigw_stack.add_dependency(bedrock_stack)

app.synth()
