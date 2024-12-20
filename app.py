# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from flask import Flask, jsonify, request, render_template
import boto3
import os
from interactions import Interactions
from twilio.rest import Client
from datetime import datetime, timezone
import time

app = Flask(__name__)

dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_REGION'])
table = os.environ['DDB_TABLE']
interactions = Interactions(dynamodb, logger=app.logger)

if not interactions.exists(table):
  interactions.create_table(table)

# Your Account SID and Auth Token from console.twilio.com
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token  = os.environ["TWILIO_AUTH_TOKEN"]

twilio_client = Client(account_sid, auth_token)

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

  if phone is not None and received_message is not None:
    previous_interaction_records = interactions.query_interactions(phone)
    previous_interaction_count = len(previous_interaction_records) 
    app.logger.error(f"previous interaction records = {previous_interaction_records}")
    # Create a message to send based on combination of message received and the count of interactions
    message_to_send = f"Hi there, you sent the message {received_message} The previous interaction count = {previous_interaction_count}"

    # Send whatsapp return message in chunks
    i = 0
    chunk_sz = int(os.environ["CHUNK_SZ"])
    message_failure_flag = False
    while i < len(message_to_send):
      # Increment by chunk sz and search for nearest end of a sentence
      j = min(i + chunk_sz, len(message_to_send))
      if j < len(message_to_send):
        while message_to_send[j] not in [".", "?", "!"]:
            j += 1
        j += 1

      # Define the chunk as section from i to j
      chunk = message_to_send[i:j]

      # Redefine i
      i = j

      # Send the message
      twilio_message = twilio_client.messages.create(
        to=phone,
        from_=os.environ["SERVER_PHONE"],
        body=chunk
      )

      # Await for a little time until some sort of delivery
      sid = twilio_message.sid
      ct = 0
      while ct < 15 and twilio_message.status not in ["delivery_unknown", "delivered", "undelivered", "failed", "read"]:
          time.sleep(ct)
          twilio_message = twilio_client.messages(sid).fetch()
          ct += 1

      # If message was not successfully sent, delivered, or read; then return error
      if twilio_message.status not in ["sent", "delivered", "read"]:
        server_msg = f"devliery of response message sid={sid} failed for {timestamp} incoming message from {phone}"
        message_failure_flag = True
        break
      

    if not message_failure_flag:
      server_msg = "success"
      # Write record to dynamodb
      interactions.add_interaction(phone, timestamp, name, received_message, message_to_send)


  else:
    name = ""
    if phone is None and received_message is not None:
      server_msg = 'Phone not parsed successfully'
    elif phone is not None and received_message is None:
      server_msg = 'Body not parsed successfully'
    else:
      server_msg = 'Phone and body not parsed successfully'


  return {"msg": server_msg}


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
