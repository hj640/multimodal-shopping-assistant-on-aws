from aws_cdk import (
    Stack,
    CfnOutput,
    aws_bedrock as bedrock,
    custom_resources as cr,
    aws_s3 as s3, 
    Fn as Fn,
    aws_iam as iam 
)
from constructs import Construct 
import hashlib 

class KnowledgeBaseStack(Stack): 

    def __init__(self, scope: Construct, id: str, **kwargs) -> None: 
        super().__init__(scope, id, **kwargs)

        
        bedrock_role_arn = Fn.import_value("BedrockAgentRoleArn")

        # 1. Retrieve s3 bucket for fashion image description that was processed from image dataset 
        s3_kb_bucket = s3.Bucket.from_bucket_arn(self, "FashionImageDescriptionBucket", "arn:aws:s3:::haijin-project-bucket")
        s3_kb_bucket.grant_read_write(iam.ServicePrincipal("bedrock.amazonaws.com"))
        
        # 2. Create bedrock knowledgebase for the agent
        kb_bucket_name = Fn.import_value("KnowledgebaseBucketName")
        index_name = "kb-index"

        # Create the bedrock knowledgebase with the role arn that is referenced in the opensearch data access policy
        bedrock_knowledge_base = bedrock.CfnKnowledgeBase(self, "kb-project-description",
            name="project-bedrock-kb",
            role_arn=bedrock_role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=Fn.import_value("OpenSearchCollectionArn"),
                    vector_index_name=index_name,
                    field_mapping = bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        metadata_field="metadataField",
                        text_field="textField",
                        vector_field="vectorField"
                        )
                    ),
                ),
        )

        CfnOutput(self, "BedrockKbName",
            value=bedrock_knowledge_base.name,
            export_name="BedrockKbName"
        )   

        # Create the data source for the bedrock knowledge base.
        kb_data_source = bedrock.CfnDataSource(self, "KbDataSource",
            name="KbDataSource",
            knowledge_base_id=bedrock_knowledge_base.ref,
            description="The S3 data source definition for the bedrock knowledge base",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=s3_kb_bucket.bucket_arn,
                    inclusion_prefixes=["image-description-dataset/"]
                ),
                type="S3"
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="NONE"
                )
            )
        )

        CfnOutput(self, "BedrockKbDataSourceName",
            value=kb_data_source.name,
            export_name="BedrockKbDataSourceName"
        )

        # Only trigger the custom resoruce when the kb is completed 
        kb_data_source.node.add_dependency(bedrock_knowledge_base)

        # 3. Start ingestion job for the knowledge base data source
        dataSourceIngestionParams = {
            "dataSourceId": kb_data_source.attr_data_source_id,
            "knowledgeBaseId": bedrock_knowledge_base.attr_knowledge_base_id,
        }

        # Define a custom resource to make an AwsSdk startIngestionJob call     
        ingestion_job_cr = cr.AwsCustomResource(self, "IngestionCustomResource",
            on_create=cr.AwsSdkCall(
                service="bedrock-agent",
                action="startIngestionJob",
                parameters=dataSourceIngestionParams,
                physical_resource_id=cr.PhysicalResourceId.of("Parameter.ARN")
                ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                )
            )
     
        # Define IAM permission policy for the custom resource    
        ingestion_job_cr.grant_principal.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:*", "iam:CreateServiceLinkedRole", "iam:PassRole"],
            resources=["*"],
            )
        )  

        # Only trigger the custom resource when the kb data source is created    
        ingestion_job_cr.node.add_dependency(kb_data_source)

        CfnOutput(self, "KnowledgebaseID",
                  value=bedrock_knowledge_base.attr_knowledge_base_id,
                  export_name="KnowledgebaseID")

        # 4. Associate the knowledgebase with the agent 
        # bedrock_agent_id = Fn.import_value("BedrockAgentID")

        # KbAssociateParams = {
        #     "agentId": bedrock_agent_id, 
        #     "agentVersion": "DRAFT",
        #     "description": "This knowledgebase contains product information.",
        #     "knowledgeBaseId": bedrock_knowledge_base.attr_knowledge_base_id,
        #     "knowledgeBaseState": "ENABLED"
        # }

        # agent_kb_association = cr.AwsCustomResource(self, "KbAssociatedAgent",
        #                                             on_create=cr.AwsSdkCall(
        #                                                 service="bedrock-agent",
        #                                                 action="AssociateAgentKnowledgeBase",
        #                                                 parameters=KbAssociateParams,
        #                                                 physical_resource_id=cr.PhysicalResourceId.of("Parameter.ARN")
        #                                             ),
        #                                             policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
        #                                                 resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
        #                                             ))
        
        # # Define IAM permission policy for kb association 
        # agent_kb_association.grant_principal.add_to_principal_policy(iam.PolicyStatement(
        #     effect=iam.Effect.ALLOW, 
        #     actions=[
        #         "bedrock:AssociateAgentKnowledgebase",
        #         "iam:CreateServiceLinkedRole",
        #         "iam:PassRole",
        #         "lambda:invoke"
        #     ],
        #     resources=["*"]
        # ))

        # # Only trigger association after knowedgebase is created 
        # agent_kb_association.node.add_dependency(kb_data_source)

        # 5. Prepare bedrock agent
        # bedrock_agent_id = Fn.import_value("BedrockAgentID")
        # agentParmas = {"agentId": bedrock_agent_id}

        # prepare_agent_cr = cr.AwsCustomResource(self, "Agnet",
        #                                 on_create=cr.AwsSdkCall(
        #                                     service="bedrock-agent",
        #                                     action="prepareAgent",
        #                                     parameters=agentParmas,
        #                                     physical_resource_id=cr.PhysicalResourceId.of("Parameter.ARN")
        #                                 ),policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
        #                                                 resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
        #                                 ))
        
        # prepare_agent_cr.grant_principal.add_to_principal_policy(iam.PolicyStatement(
        #     effect=iam.Effect.ALLOW,
        #     actions=["bedrock:prepareAgent", "iam:CreateServiceLinkedRole", "iam:PassRole", "lambda:*"],
        #     resources=["*"],
        #     )
        # ) 

        # # Only trigger prepare agent customeization after bedrock agent is associated with knowledgebase 
        # prepare_agent_cr.node.add_dependency(agent_kb_association)

        # # 6. Create Bedrock Agent Alias 
        # agent_alias = bedrock.CfnAgentAlias(self, "AgnetAlias",
        #                                     agent_alias_name="bedrock-agent-alias",
        #                                     agent_id=bedrock_agent_id)
        
        # CfnOutput(self, "BedrockAgentAlias",
        #           value=agent_alias.ref,
        #           export_name="BedrockAgentAlias"
        #         )
        
        # # Only trigger agent alias after agent preparation 
        # agent_alias.node.add_dependency(prepare_agent_cr)







        




