import json 
import os 
import boto3 

region = os.environ["AWS_REGION"]
knowledgebase_id = os.environ["KNOWLEDGEBASE_ID"]

def retrieve_products(event): 
    bedrock_agent_client = boto3.client(service_name="bedrock-agent-runtime", region_name=region)
    prompt = event['requestBody']['content']['application/json']['properties'][0]['value']
    response = bedrock_agent_client.retrieve(
        retrievalQuery = {
            'text': prompt
        },
        knowledgeBaseId=knowledgebase_id,
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5
            }
        }
    )
    return response 

def handler(event, context):

    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    if api_path == '/retrieveProducts':
        result = retrieve_products(event)
    else:
        response_code = 404
        result = f"Unrecognized api path: {action_group}::{api_path}"

    response_body = {
        'application/json': {
            'body': result
        }
    }

    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': response_code,
        'responseBody': response_body
    }

    api_response = {'messageVersion': '1.0', 'response': action_response}
    return api_response

