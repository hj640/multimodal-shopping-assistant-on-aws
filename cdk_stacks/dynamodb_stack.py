from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_iam as iam,
    custom_resources as cr,
    CfnOutput
)
import json
from constructs import Construct

class DynamodbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a dynamodb table 
        customer_table = dynamodb.CfnTable(self, "CustomerTable",
                                           key_schema=[
                                               dynamodb.CfnTable.KeySchemaProperty(
                                               attribute_name="customerName",
                                               key_type="HASH"),
                                           ],
                                           attribute_definitions=[
                                               dynamodb.CfnTable.AttributeDefinitionProperty(
                                                  attribute_name="customerName",
                                                  attribute_type="S" 
                                               )
                                           ],
                                           billing_mode="PAY_PER_REQUEST",
                                           table_name="CustomerTable"
                                           )
        
        # 2. Ingest sample customer data into dynamodb
        with open('assets/customer_data/customer_data.json') as file:
                customer_data = json.load(file)
        
        for i, customer in enumerate(customer_data):
            item = {}
            for key, value in customer.items():
                if value: 
                    if isinstance(value, list):
                        item[key] = {'SS': value}
                    elif isinstance(value, str):
                        item[key] = {'S': value}
                    elif isinstance(value, int):
                        item[key] = {'N': str(value)}
                
            put_item = cr.AwsCustomResource(
                self, f"DBPutItem-{i}",
                on_create=cr.AwsSdkCall(
                action = "putItem",
                service = "DynamoDB",
                parameters = {
                    "TableName": customer_table.table_name,
                    "Item": item
                },
                physical_resource_id = cr.PhysicalResourceId.of(customer_table.table_name + '_initialization')),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                    resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                )
            )

        CfnOutput(self, "CustomerTableName",
                  value=customer_table.table_name,
                  description="GarmentFinder Customer Table Name",
                  export_name="CustomerTableName")
        
        
        CfnOutput(self, "CustomerTableRef", 
                  value=customer_table.ref,
                  description="GarmentFinder Cusotmer Table Ref",
                  export_name="CustomerTableRef")
        


        