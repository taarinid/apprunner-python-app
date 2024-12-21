import os
import boto3
from interactions import Interactions

dynamodb = boto3.resource("dynamodb",region_name=os.environ["AWS_REGION"])
table = os.environ["DDB_TABLE"]
interactions = Interactions(dynamodb)

interactions.delete_table()
interactions.create_table(table)