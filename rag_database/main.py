from images_to_s3 import * 
from images_to_text import * 
from dotenv import load_dotenv

load_dotenv() 
s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

LOCAL_FOLDER = 'dataset/image_dataset'

def main(): 

    # Code to create s3 bucket if you need. You can use exisitng S3 bucket. 
    create_s3_bucket(BUCKET_NAME)

    # Uplaod Images to S3 
    uplaod_images_to_s3(BUCKET_NAME, LOCAL_FOLDER)

    # Convert Image to Text using Bedrock Claude Model 
    image_to_text(BUCKET_NAME)

    print("Images processed successfully.")

if __name__=="__main__":
    main() 