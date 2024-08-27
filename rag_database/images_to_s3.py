import boto3 
import os 

def create_s3_bucket(bucket_name): 
    # Create bucket in s3 
    s3_client = boto3.client('s3')
    list_objects = s3_client.create_bucket(Bucket=bucket_name,
                                           CreateBucketConfiguration={
                                               'LocationConstraint':'us-west-2'
                                           })
    print('Successfully created bucket.')

def uplaod_images_to_s3(bucket_name, local_folder): 
    # Create an S3 client 
    s3_client = boto3.client('s3')

    # Iterate through all files in the local folder
    for filename in os.listdir(local_folder): 
        if filename.endswith(('.png')): 
            local_file_path = os.path.join(local_folder, filename) 
            s3_file_key = f'image-dataset/{filename}'

            try: 
                # Upload the file 
                s3_client.upload_file(local_file_path, bucket_name, s3_file_key)
                print(f'Successfully uploaded {filename} to {bucket_name}/{s3_file_key}')
            except Exception as e: 
                print(f'Failed to upload {filename} to {bucket_name}/{s3_file_key}: {e}')


# BUCKET_NAME = 'haijin-project-bucket'
# LOCAL_FOLDER = '/Users/haijin/Documents/GitHub/aws-intern-project/dataset/image_dataset'
# uplaod_images_to_s3(BUCKET_NAME, LOCAL_FOLDER)