# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from flask import Flask, jsonify, request, render_template
import boto3
import os
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


#Home Page
@app.route('/')
def home():
  return render_template('index.html')


# POST /api/whatsapp
@app.route('/api/whatsapp', methods=['POST'])
def whatsapp_reply():
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

  resp = MessagingResponse()

  app.logger.error(f"phone={phone}, received_message={received_message}")

  if phone is not None and received_message is not None:
    # Create a message to send based on combination of message received and the count of interactions
    message_to_send = f'Hi there, you sent the message "{received_message}"'

    # Incorporate message into response
    resp.message(message_to_send)

  else:
    name = ""
    if phone is None and received_message is not None:
      message_to_send = 'Phone not parsed successfully'
    elif phone is not None and received_message is None:
      message_to_send = 'Body not parsed successfully'
    else:
      message_to_send = 'Phone and body not parsed successfully'

    resp.message(message_to_send)

  # Write record to dynamodb
  interactions.add_interaction(phone, timestamp, name, received_message, message_to_send)


  return str(resp)


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
