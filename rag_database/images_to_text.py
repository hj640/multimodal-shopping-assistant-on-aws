import boto3 
import json 
import re
import base64
from botocore.exceptions import ClientError 

SONNET30 = "anthropic.claude-3-sonnet-20240229-v1:0"

ASSIGN_ROLE_PROMPT = """
        You are an AI model designed to analyze and descrbie fashion items in images. 
        Your task is to identify and describe specific freatures of the clothing item in the image provided. 
        EXTREMELY IMPORTANT TO KEEP IN MIND: Always skip the preamble. Neer use ambiguous words like "Likely". Here is the image. 
    """

TASK_PROMPT = """
        Look through and identify the overall style of the dress. 
        You need to extract the following criteria nad store them in JSON format (the key should be camelCase):
        1. Product name in 3-5 words (string type)
        2. Gender (string type)
        3. Type of clothing (string type)
        4. Primary color (string type; this color should be backgorund color of the product)
        5. Secondary color (string type; extract any additional colors except primary color)
        6. Season (list type; if multiple seasons are fitted in)
        7. Pattern (string type; try to be specific for the pattern)
        8. Material (string type)
        9. Fit (string type)
        10. Length (string type)
        11. Notable feature (list type; for example, seams or overall shape of the product)
        12. Style (string type)
        13. Context it would be fitted into (list type)
        14. Trending fashion tags on Instagram and other social media platforms (list type; for example, Old Money, Geek Chick; if multiple fashion tags are applicable, extract as a list tyle) 
        15. Product image description (string type; it should contain actual product description and style of it; Never start with "The image displays")
        16. Additional details that users may like and not included in above criteria 
    """

def invoke_claude_model(image, image_path):

    # Create request body 
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "messages": [
            {
            "role": "user",
            "content": [
                {"type": "text", "text": ASSIGN_ROLE_PROMPT},
                {"type": "image",
                 "source": {
                     "type": "base64",
                     "media_type": "image/png",
                     "data": image
                 }},
                {"type": "text", "text": TASK_PROMPT}
            ]
        }
        ]
    }

    try: 
        # Invoke bedrock claude model and get response 
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
        response = bedrock_client.invoke_model(
            modelId=SONNET30,
            body=json.dumps(request_body)
        )
        response_body = json.loads(response.get('body').read())
        result = response_body['content'][0]['text']
        result = json.loads(result)
        result['imagePath'] = image_path
        print(result)
        return result 
    
    except ClientError as err: 
        message = err.response['Error']['Message']
        print(f"A client error occured: {message}")

def convert_file_name(file_name):
    # Split the input string to get the directory and filename 
    parts = file_name.split('/')
    directory = parts[0]
    filename = parts[1]

    # Extract the numeric part of the file name 
    file_base = re.findall(r'\d+', filename)[0]
    # Construct new directory name 
    new_directory = 'image-description-dataset'
    # Construct new file name with .json extension 
    new_filename = f'{file_base}.json'

    # Combine the new directory and new file name 
    converted_file_name = f'{new_directory}/{new_filename}'

    return converted_file_name

print(convert_file_name('image-dataset/0108775015.png'))

def image_to_text(BUCKET_NAME):

    # Initialize a session using Amazon S3 
    s3_client = boto3.client('s3', region_name='us-west-2')

    # Pagination 
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=BUCKET_NAME, Prefix='image-dataset/')

    # Iterate each object in image-dataset folder 
    for page in page_iterator: 
        if 'Contents' in page: 
            for obj in page['Contents']:
                try: 
                    # image key 
                    image_key = obj['Key']

                    ##### Prevent duplicate 
                    parts = image_key.split('/')
                    filename = parts[-1]
                    first_three_digits = int(filename[:3])
                    if first_three_digits < 68: 
                        continue 

                    # Retrieve and encode image 
                    s3_image_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=image_key)
                    image_bytes = s3_image_response['Body'].read() 
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

                    # Invoke claude model and get response 
                    output = invoke_claude_model(image_base64, image_key)
                    # Convert the JSON data to a string 
                    json_string = json.dumps(output) 

                    # Convert file name for json 
                    json_key = convert_file_name(image_key)

                    # Upload the JSON string to S3 
                    s3_client.put_object(Bucket=BUCKET_NAME, Key=json_key, Body=json_string, ContentType='application/json')

                except Exception as e:
                    print(f'Error {e} occured for file: {image_key}')