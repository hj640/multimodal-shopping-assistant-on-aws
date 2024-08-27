import os 
import json
import boto3 

table_name = os.environ["TABLE_NAME"]
dynamodb = boto3.resource('dynamodb')
cust_table = dynamodb.Table(table_name)

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']

def get_customer_info(event):
    
    # Extraction customer name 
    customer_name = get_named_parameter(event, 'CustomerName')
    try: 
        item = cust_table.get_item(
            Key={
                "customerName": customer_name
            }
        )
        
        cust_item = item['Item']
        
        cust_info = {
            "customerName": cust_item['customerName'],
            "gender": cust_item["gender"],
            "age": str(cust_item["age"]),
            "country": cust_item["country"]
        }
        return json.dumps(cust_info)
    except:
        return "No user name found."

def handler(event, context):
    
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    if api_path == '/customer/{CustomerName}/getInfo':
        result = get_customer_info(event)
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
