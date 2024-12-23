from interactions import Interactions
import os
import boto3
import logging
import time

dynamodb = boto3.resource("dynamodb",region_name=os.environ["AWS_REGION"])
table = os.environ["DDB_TABLE"]
logger = logging.getLogger(__name__)
interactions = Interactions(dynamodb, logger=logger)

if interactions.exists(table):
	interactions.delete_table()
	time.sleep(10)
interactions.create_table(table)