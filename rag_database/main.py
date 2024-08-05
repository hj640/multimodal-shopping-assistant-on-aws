from images_to_s3 import * 
from images_to_text import * 

BUCKET_NAME = 'haijin-project-bucket'
LOCAL_FOLDER = '/Users/haijin/Documents/GitHub/aws-intern-project/dataset/image_dataset'

def main(): 
    # create s3 bucket 
    create_s3_bucket(BUCKET_NAME)

    # uplaod images to s3 
    uplaod_images_to_s3(BUCKET_NAME, LOCAL_FOLDER)

    # convert image to text using Bedrock claude model 
    image_to_text(BUCKET_NAME)

    print("Images processed successfully.")

if __name__=="__main__":
    main() 