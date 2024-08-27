from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    Fn as Fn,
    CfnOutput
)
from constructs import Construct 

class ApiStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None: 
        super().__init__(scope, id, **kwargs)

        # 1. Create bedrock agent invokation lambda 

        # Create lmabda funtion that invoke bedrock knowledgebase integrated agent 
        bedrock_agent_invokation_lambda = _lambda.Function(
            self, "agent-invocation-lambda",
            runtime=_lambda.Runtime.PYTHON_3_12, 
            code=_lambda.Code.from_asset("lambdas"),
            handler='bedrock_agent_invokation.handler',
            timeout=Duration.seconds(180),
            environment={
                "BEDROCK_AGENT_ID": Fn.import_value("BedrockAgentID"),
                "BEDROCK_AGENT_ALIAS": Fn.import_value("BedrockAgentAlias"),
                "REGION": self.region
            }
        )

        # Create a lambda layer that contains necessary libraries 
        layer = _lambda.LayerVersion(
            self, 'py-lib-layer',
            code=_lambda.Code.from_asset('assets/lambda-layer.zip'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12]
        )

        # Add the layer for lambda function
        bedrock_agent_invokation_lambda.add_layers(layer)

        # Assign bedrock InvokeAgent policy to lambda 
        bedrock_agent_invokation_lambda.role.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeAgent",
                "bedrock:InvokeModel",
                "bedrock:Retrieve"],
            resources=["*"]
        ))
        
        # Export the lambda arn 
        CfnOutput(self, "AgentInvokationLambdaArn",
                  value=bedrock_agent_invokation_lambda.function_arn,
                  export_name="AgentInvokationLambdaArn")
        
        # 2. Create API gateway 
        apigw_endpoint = apigw.RestApi(self, "BedrockAgentAPI",
                                       rest_api_name="BedrockAgentAPI",
                                       default_cors_preflight_options={
                                            "allow_origins": apigw.Cors.ALL_ORIGINS,
                                            "allow_methods": apigw.Cors.ALL_METHODS,
                                            "allow_headers": apigw.Cors.DEFAULT_HEADERS,
                                        },
                                        endpoint_types=[apigw.EndpointType.REGIONAL]
        )  

        # CORS permission setting 
        integration_response = {
            "proxy": False,
            "integration_responses": [
                {
                    "statusCode": "200",
                    "response_parameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                    },
                    "response_templates": {
                        "application/json": ""
                    },
                },
            ],
        }

        method_response = {
            "method_responses": [
                {
                    "statusCode": "200",
                    "response_parameters": {
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                    "response_models": {
                        "application/json": apigw.Model.EMPTY_MODEL,
                    },
                },
            ],
        }

        # Integrate Lmabda function to API Gateway using POST method 
        bedrock_agent_invokation_lambda_integration = apigw.LambdaIntegration(bedrock_agent_invokation_lambda, **integration_response)
        apigw_endpoint.root.add_resource("BedrockAgent").add_method("POST", 
                                                                    bedrock_agent_invokation_lambda_integration, 
                                                                    method_responses=method_response["method_responses"])
        
        ssm.StringParameter(self, "APIGatewayUrl",
                            parameter_name="APIGatewayUrl",
                            string_value=apigw_endpoint.url)
        
        CfnOutput(self, "ApiGatewayUrl",
                  value=apigw_endpoint.url,
                  export_name="ApiGatewayUrl")


        
