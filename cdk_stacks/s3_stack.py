# from aws_cdk import (
#     Stack,
#     RemovalPolicy,
#     aws_s3 as s3,
#     aws_s3_deployment as s3_deployment 
# )
# from constructs import Construct

# class S3Stack(Stack):

#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)

#         ### FOR END-TO-END SOLUTION ### 
#         # Needs to be changed all the time
#         project_bucket_name = 'aws-intern-project-bucket'

#         # Create S3 bucket for project 
#         s3_bucket_for_fashion_image = s3.Bucket(self, 'ProjectBucket',
#                                                 bucket_name=project_bucket_name,
#                                                 block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
#                                                 removal_policy=RemovalPolicy.DESTROY,
#                                                 auto_delete_objects=True)
        

#         # Upload fashion image dataset to S3 Bucket 
#         s3_upload_fashion_dataset = s3_deployment.BucketDeployment(self, "UploadFashionImages",
#                                                         sources=[s3_deployment.Source.asset("dataset/sample_image_dataset")],
#                                                         destination_bucket=s3_bucket_for_fashion_image,
#                                                         destination_key_prefix='image-dataset')
        
        

        ### WILL USE EXISTING BUCKET FOR PRRODUCTION PURPOSE ### 
        # s3_bucket_for_fashion_image = s3.Bucket.from_bucket_arn(self, "FahsionImageBucket", "arn:aws:s3:::haijin-project-bucket/image-dataset/")
        # s3_bucket_for_fashion_image_description = s3.Bucket.from_bucket_arn(self, "FashionImageDescriptionBucket", "arn:aws:s3:::haijin-project-bucket/image-description-dataset/")

        