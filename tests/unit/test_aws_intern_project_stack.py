import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_stacks.s3_stack import AwsInternProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_intern_project/aws_intern_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsInternProjectStack(app, "aws-intern-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
