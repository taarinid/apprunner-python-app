# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from flask import Flask, jsonify, request, render_template
import boto3
import os
from interactions import Interactions
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timezone

app = Flask(__name__)

dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_REGION'])
table = os.environ['DDB_TABLE']
interactions = Interactions(dynamodb, logger=app.logger)

if not interactions.exists(table):
  interactions.create_table(table)

#Home Page
@app.route('/')
def home():
  return render_template('index.html')


# POST /api/whatsapp
@app.route('/api/whatsapp', methods=['POST'])
def whatsapp_reply():
  #timestamap
  timestamp = datetime.strftime(datetime.now(timezone.utc), '%m-%d-%y %H:%M:%S UTC')

  # Attempt to extract the phone number
  try:
    phone = request.values.get('From', None)
  except:
    phone = None

  # Attempt to extract the message body
  try:
    received_message = request.values.get('Body', None)
  except:
    received_message = None
  
  #attempting to extract the username
  try:
    name = request.values.get("ProfileName", None)
  except:
    name = None

  if name is None:
    app.logger.error(f"name could not be parsed for {phone} at {timestamp}")

  resp = MessagingResponse()


  if phone is not None and received_message is not None:
    previous_interaction_records = interactions.query_interactions(phone)
    previous_interaction_count = len(previous_interaction_records) 
    app.logger.error(f"previous interaction records = {previous_interaction_records}")
    # Create a message to send based on combination of message received and the count of interactions
    message_to_send = f"Hi there, you sent the message {received_message} The previous interaction count = {previous_interaction_count}"
    # Incorporate message into response
    resp.message(message_to_send)
    mentor_type = ''
    interactions.add_interaction(phone, timestamp, received_message, message_to_send, mentor_type, name)
  
  else:
    name = ""
    if phone is None and received_message is not None:
      message_to_send = 'Phone not parsed successfully'
    elif phone is not None and received_message is None:
      message_to_send = 'Body not parsed successfully'
    else:
      message_to_send = 'Phone and body not parsed successfully'

    resp.message(message_to_send)


  return str(resp)


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
