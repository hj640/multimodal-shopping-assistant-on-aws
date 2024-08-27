import json 
import boto3 
import requests 
from PIL import Image
import io
import os 
import re
from dotenv import load_dotenv
import streamlit as st 

###### QUERY FUNCTION ###### 
ssm = boto3.client('ssm', region_name='us-west-2')

def get_params(key, enc=False):
    if enc:
        WithDecryption = True 
    else:
        WithDecryption = False 
    response = ssm.get_parameters(
        Names=[key,],
        WithDecryption=WithDecryption
    )
    return response['Parameters'][0]['Value']

API_GW_URL = get_params(key="APIGatewayUrl", enc=False)

def query(prompt, session_id):
    api_url = API_GW_URL + 'BedrockAgent'
    response = requests.post(
        api_url,
        headers={
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "session_id": session_id
        }
    )
    if response.status_code == 200:
        response_data = response.json()
        print(response_data)
        # Extract the body content 
        body_content = str(response_data.get("body", ""))
        body_content = body_content.replace('\\n', '\n')

        if "<query>" in body_content:
            return False, single_answer(body_content)
        elif is_meta_data(body_content):
            return True, multi_answer(body_content)
        else:
            return False, body_content

    else:
        error_message = f"API request failed: {response.status_code}"
        return {"error": error_message}
    

##### PARSE ANSWER FOR MULTI-MODALITY ###### 

load_dotenv() 
s3 = boto3.client('s3')
bucket_name = os.getenv('S3_BUCKET_NAME')

def parse_query(response): 
     # Extract text within the <query> tags
    start_tag = "<query>"
    end_tag = "</query>"
    start_index = response.find(start_tag) + len(start_tag)
    end_index = response.find(end_tag)

    # Extract the relevant message 
    if start_index != -1 and end_index != -1:
        extracted_text = response[start_index:end_index].strip() 
    else: 
        extracted_text = "Extracted text not found."
        print("Extracted text not found.")
    
    return extracted_text

def resize_image(image, max_width=150): 
    aspect_ratio = image.height / image.width 
    new_width = min(max_width, image.width)
    new_height = int(aspect_ratio * new_width)
    resized_image = image.resize((new_width, new_height))
    return resized_image

def parse_image(bucket_name, image_path):
    # Generate a presigned URL for the image 
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': image_path
        }
    )
    print("URL: ", url)
    response = s3.get_object(Bucket=bucket_name, Key=image_path)
    img_data = response['Body'].read()
    img = Image.open(io.BytesIO(img_data))
    img = resize_image(img)
    return img 

def parse_meta_data(bucket_name, json_key):
    json_key = json_key.replace(f"s3://{bucket_name}/", "")
    response = s3.get_object(Bucket=bucket_name, Key=json_key)
    json_data = json.loads(response['Body'].read().decode('utf-8'))
    return json_data

def is_meta_data(response):

    # Regular expressions to extract S3 paths 
    image_pattern = re.compile(r"image-dataset\/.*?\.png")
    json_pattern = re.compile(r"s3:\/\/.*?\.json")

    # Extract the paths 
    image_paths = image_pattern.findall(response)
    json_paths = json_pattern.findall(response)

    if image_paths or json_paths:
        return True

    return False


def get_image_and_product_details(response):

    # Regular expressions to extract S3 paths 
    image_pattern = re.compile(r"image-dataset\/.*?\.png")
    json_pattern = re.compile(r"s3:\/\/.*?\.json")

    # Extract the paths 
    image_paths = image_pattern.findall(response)
    json_paths = json_pattern.findall(response)

    return image_paths, json_paths

def single_answer(response):
    return parse_query(response)

def multi_answer(response):
    image_paths, json_paths = get_image_and_product_details(response)
    images = []
    descriptions = []
    for image_path, json_path in zip(image_paths, json_paths):
        img = parse_image(bucket_name, image_path)
        json_data = parse_meta_data(bucket_name, json_path)
        images.append(img)
        descriptions.append(json_data['productImageDescription'])
    print(images, descriptions)
    return list(zip(images, descriptions))