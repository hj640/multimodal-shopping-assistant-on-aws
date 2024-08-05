#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks.s3_stack import S3Stack


app = cdk.App()
s3_stack = S3Stack(app, "Project-S3Stack")

app.synth()
