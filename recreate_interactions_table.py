from interactions import Interactions
import os
import boto3
import logging

dynamodb = boto3.resource("dynamodb",region_name=os.environ["AWS_REGION"])
table = os.environ["DDB_TABLE"]
logger = logging.getLogger(__name__)
interactions = Interactions(dynamodb, logger=logger)

if interactions.exists(table):
	interactions.delete_table()
interactions.create_table(table)