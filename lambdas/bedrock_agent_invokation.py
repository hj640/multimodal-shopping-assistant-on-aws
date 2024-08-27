import boto3 
from botocore.exceptions import ClientError
import os 
import logging
import json 
import uuid 

agentId = os.environ["BEDROCK_AGENT_ID"]
agentAliasId = os.environ["BEDROCK_AGENT_ALIAS"]
agentAliasId = agentAliasId.split("|")[-1]
region = os.environ["AWS_REGION"]


def call_bedrock_agent(prompt, session_id):
    try:
        bedrock_agent_client = boto3.client(service_name="bedrock-agent-runtime", region_name=region) 
        response = bedrock_agent_client.invoke_agent(
            agentId=agentId,
            agentAliasId=agentAliasId,
            sessionId=session_id,
            inputText=prompt
        )

        completion = ""
        
        for event in response.get("completion"):
            chunk = event["chunk"]
            completion = completion + chunk["bytes"].decode()


    except ClientError as e: 
        logging.error(f"Couldn't invoke agent. {e}")

    return completion 


def handler(event, context):

    prompt = event["prompt"]
    session_id = event["session_id"]
    # session_id = event["sessionId"]
    
    try: 
        response = call_bedrock_agent(prompt, session_id)
        return {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    
    except Exception as e:
        return {
            "statusCode": 400,
            "body": {"error": str(e)},
            "headers": {
                "Content-Type": "application/json"
            }
        }


