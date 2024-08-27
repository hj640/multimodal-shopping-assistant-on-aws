import json
import boto3 
from datetime import datetime

def get_today_month():
    return datetime.now().month

def enhance_prompt(event):
    # Create request body 
    HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    
    prompt = event['requestBody']['content']['application/json']['properties'][0]['value']
    cust_info = event['requestBody']['content']['application/json']['properties'][1]['value']
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "messages": [
            {
            "role": "user",
            "content": [
                {"type": "text", 
                "text": f"You are a fashion recommender. You should prioritize customer's gender. Based on the prompt: {prompt} and {cust_info}, please do the followings: \
                    1. If the prompt contains people's name, place, or occasion, please extract them. \
                    Describe a fashion style related to the extracted items. Remember to incorporate weather if there is any. \
                    2. Always incorporate customer's gender in enhanced prompt."},
            ]
        }
        ]
    }
    
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
    response = bedrock_client.invoke_model(
        modelId=HAIKU,
        body=json.dumps(request_body)
    )
    response_body = json.loads(response.get('body').read())
    result = response_body['content'][0]['text']
    return {"prompt": result} 

def handler(event, context):

    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    if api_path == '/enhancePrompt':
        result = enhance_prompt(event)
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

