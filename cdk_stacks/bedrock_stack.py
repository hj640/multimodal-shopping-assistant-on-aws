from distutils.log import Log 
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_bedrock as bedrock,
    aws_lambda as _lambda,
    aws_s3 as s3, 
    aws_logs as logs,
    Fn as Fn,
    custom_resources as cr,
)
from constructs import Construct 
import os 
import hashlib 

class BedrockStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None: 
        super().__init__(scope, id, **kwargs)

        bedrock_agent_role_arn = Fn.import_value("BedrockAgentRoleArn")

        # Create a bedrock agent 
        with open('assets/agent_instruction.txt', 'r') as file:
            agent_instruction = file.read() 

        # Add schema for the bedrock agent
        with open('assets/api_schema/enhacne_prompt_schema.json') as file:
            enhance_prompt_schema = file.read() 

        with open('assets/api_schema/get_customer_info.json') as file:
            get_cust_info_schema = file.read() 

        with open('assets/api_schema/retrieve_products.json') as file:
            retrieve_products_schema = file.read() 

        # Define advanced prompt - kb generation template - override kb generation template 
        with open('assets/agent_kb_generation.txt') as file: 
            kb_temp_def = file.read() 
        
        with open('assets/agent_orch_instruction.txt') as file: 
            orch_temp_def = file.read() 


        bedrock_agent = bedrock.CfnAgent(self, 'bedrock-agent',
                                         agent_name='bedrock-agent',
                                         auto_prepare=True,
                                         foundation_model='anthropic.claude-3-sonnet-20240229-v1:0',
                                         instruction=agent_instruction,
                                         agent_resource_role_arn=bedrock_agent_role_arn,
                                        #  prompt_override_configuration=bedrock.CfnAgent.PromptOverrideConfigurationProperty(
                                        #      prompt_configurations=[
                                        #          bedrock.CfnAgent.PromptConfigurationProperty(
                                        #              base_prompt_template=kb_temp_def,
                                        #              prompt_type="KNOWLEDGE_BASE_RESPONSE_GENERATION",
                                        #              prompt_state="ENABLED",
                                        #              prompt_creation_mode="OVERRIDDEN",
                                        #              inference_configuration=bedrock.CfnAgent.InferenceConfigurationProperty(
                                        #                  maximum_length=2048,
                                        #                  stop_sequences=["⏎⏎Human:"],
                                        #                  temperature=0,
                                        #                  top_k=250,
                                        #                  top_p=1
                                        #              )),
                                        #         bedrock.CfnAgent.PromptConfigurationProperty(
                                        #              base_prompt_template=orch_temp_def,
                                        #              prompt_type="ORCHESTRATION",
                                        #              prompt_state="ENABLED",
                                        #              prompt_creation_mode="OVERRIDDEN",
                                        #              inference_configuration=bedrock.CfnAgent.InferenceConfigurationProperty(
                                        #                  maximum_length=2048,
                                        #                  stop_sequences=["</error>","</answer>","</invoke>"],
                                        #                  temperature=0,
                                        #                  top_k=250,
                                        #                  top_p=1
                                        #              ))
                                        #      ]
                                        #  ),
                                         action_groups=[
                                            #  bedrock.CfnAgent.AgentActionGroupProperty(
                                            #      action_group_name="EnhancePromptFunction",
                                            #      description="A function that enhances user's prompt by invoking HAIKU model.",
                                            #      action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                                            #          lambda_=Fn.import_value("EnhancePromptLambdaArn")
                                            #      ),
                                            #      api_schema=bedrock.CfnAgent.APISchemaProperty(
                                            #          payload=enhance_prompt_schema
                                            #      )
                                            #  ),
                                             bedrock.CfnAgent.AgentActionGroupProperty(
                                                 action_group_name="GetCustomerInfo",
                                                 description="A function that gets customer's info based on customer user name.",
                                                 action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                                                     lambda_=Fn.import_value("GetCustInfoLambdaArn")
                                                 ),
                                                 api_schema=bedrock.CfnAgent.APISchemaProperty(
                                                     payload=get_cust_info_schema
                                                 )
                                             ),
                                             bedrock.CfnAgent.AgentActionGroupProperty(
                                                 action_group_name="RetrieveProductsFunction",
                                                 description="A function that retrieves products from knowledgebase.",
                                                 action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                                                     lambda_=Fn.import_value("RetrieveProductsLambdaArn")
                                                 ),
                                                 api_schema=bedrock.CfnAgent.APISchemaProperty(
                                                     payload=retrieve_products_schema
                                                 )
                                             ),
                                         ])
        
        agentParmas = {"agentId": bedrock_agent.ref}

        prepare_agent_cr = cr.AwsCustomResource(self, "Agnet",
                                        on_create=cr.AwsSdkCall(
                                            service="bedrock-agent",
                                            action="prepareAgent",
                                            parameters=agentParmas,
                                            physical_resource_id=cr.PhysicalResourceId.of("Parameter.ARN")
                                        ),policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                                                        resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                                        ))
        
        prepare_agent_cr.grant_principal.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:prepareAgent", "iam:CreateServiceLinkedRole", "iam:PassRole", "lambda:*"],
            resources=["*"],
            )
        ) 

        agent_alias = bedrock.CfnAgentAlias(self, "AgnetAlias",
                                            agent_alias_name="bedrock-agent-alias",
                                            agent_id=bedrock_agent.ref)
        
        CfnOutput(self, "BedrockAgentAlias",
                  value=agent_alias.ref,
                  export_name="BedrockAgentAlias"
                )
        
        # Only trigger agent alias after agent preparation 
        agent_alias.node.add_dependency(prepare_agent_cr)

        CfnOutput(self, "BedrockAgentID",
                  value=bedrock_agent.ref,
                  export_name="BedrockAgentID")
        
        CfnOutput(self, "BedrockAgentModelName",
            value=bedrock_agent.foundation_model,
            export_name="BedrockAgentModelName"
        )  

        self.agent_arn = bedrock_agent.ref 


