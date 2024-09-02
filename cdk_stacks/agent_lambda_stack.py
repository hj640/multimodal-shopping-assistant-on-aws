from aws_cdk import (
    Stack, 
    Duration,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_lambda as _lambda, 
    Fn as Fn,
    CfnOutput 
)
from constructs import Construct 


class AgentLambdasStack(Stack): 

    def __init__(self, scope: Construct, id: str, **kwargs) -> None: 
        super().__init__(scope, id, **kwargs)

        # 1. Create enhance prompt lambda function 

        # Create a lambda layer that contains necessary libraries 
        lambda_layer = _lambda.LayerVersion(
            self, 'py-lib-layer',
            code=_lambda.Code.from_asset('assets/lambda-layer.zip'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12]
        )

        # enhance_prompt_lambda = _lambda.Function(
        #     self, "enhance-prompt-lambda",
        #     runtime=_lambda.Runtime.PYTHON_3_12,
        #     code=_lambda.Code.from_asset("lambdas"),
        #     handler='enhance_prompt.handler',
        #     timeout=Duration.seconds(120),
        #     layers=[lambda_layer]
        # )
        
        # # Assign bedrock invoke moel policy to lambda
        # enhance_prompt_lambda.role.add_to_principal_policy(iam.PolicyStatement(
        #     effect=iam.Effect.ALLOW,
        #     actions=["bedrock:InvokeModel"],
        #     resources=["*"]
        # ))

        # # Add permissions to Lambda function resource policy. 
        # add_lambda_resource_policy = enhance_prompt_lambda.add_permission(
        #     "AllowBedrock",
        #     principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
        #     action="lambda:InvokeFunction",
        #     source_arn=f"arn:aws:bedrock:{self.region}:{self.account}:agent/*"
        # )

        # # Export the lambda arn 
        # CfnOutput(self, "EnhancePromptLambdaArn",
        #           value=enhance_prompt_lambda.function_arn,
        #           export_name="EnhancePromptLambdaArn")
        
        # 2. Create get customer informtaion labmda function

        get_cust_info_lambda = _lambda.Function(
            self, "get-customer-info-lambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambdas"),
            handler='get_customer_info.handler',
            timeout=Duration.seconds(120),
            layers=[lambda_layer],
            memory_size=1024,
            environment={
                "TABLE_NAME": Fn.import_value("CustomerTableName")
            }
        )

        # Assign dynamodb get item policy to lambda 
        get_cust_info_lambda.role.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["dynamodb:GetItem"],
            resources=["*"]
        ))

        # Add lambda execution role permissions for the services lambda will interact with 
        get_cust_info_lambda.add_permission(
            "AllowDynamoDB",
            principal=iam.ServicePrincipal("dynamodb.amazonaws.com"),
            action="lambda:GetItem",
            source_arn=f"arn:aws:dynamodb:{self.region}:{self.account}:table/*"
        ) 

        # Add permissions to Lambda function resource policy 
        get_cust_info_lambda.add_permission(
            "AllowBedrock",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:bedrock:{self.region}:{self.account}:agent/*"
        )

        # Add iam managed policies to the Lambda execution role 
        get_cust_info_lambda.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
        )

        # Export the lambda arn 
        CfnOutput(self, "GetCustInfoLambdaArn",
                  value=get_cust_info_lambda.function_arn,
                  export_name="GetCustInfoLambdaArn")
        
        # 3. Create retrieve products lambda function 

        retrieve_products_lambda = _lambda.Function(
            self, "retrieve-products-lambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambdas"),
            handler='retrieve_products.handler',
            timeout=Duration.seconds(120),
            layers=[lambda_layer],
            memory_size=1024,
            environment={
                "KNOWLEDGEBASE_ID": Fn.import_value("KnowledgebaseID")
            }
        )

        # Assign bedrock invoke moel policy to lambda
        retrieve_products_lambda.role.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:Retrieve"
                ],
            resources=["*"]
        ))

        # Add permissions to Lambda function resource policy. 
        retrieve_products_lambda.add_permission(
            "AllowBedrock",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:bedrock:{self.region}:{self.account}:agent/*"
        )

        # Export the lambda arn 
        CfnOutput(self, "RetrieveProductsLambdaArn",
                  value=retrieve_products_lambda.function_arn,
                  export_name="RetrieveProductsLambdaArn")
        


        
