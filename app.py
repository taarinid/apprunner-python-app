# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from flask import Flask, jsonify, request, render_template
import boto3
import os
from interactions import Interactions
from twilio.rest import Client
from datetime import datetime, timezone
import time
import openai
import random
from chatapp import ChatApp

app = Flask(__name__)

dynamodb = boto3.resource("dynamodb",region_name=os.environ["AWS_REGION"])
table = os.environ["DDB_TABLE"]
interactions = Interactions(dynamodb, logger=app.logger)

if not interactions.exists(table):
  interactions.create_table(table)

# Make twilio client
twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

#Home Page
@app.route("/")
def home():
  return render_template("index.html")


# POST /api/whatsapp
@app.route("/api/whatsapp", methods=["POST"])
def whatsapp_reply():
  #timestamap
  timestamp = datetime.strftime(datetime.now(timezone.utc), "%m-%d-%y %H:%M:%S UTC")

  # Attempt to extract the phone number
  try:
    phone = request.values.get("From", None)
  except:
    phone = None

  # Attempt to extract the message body
  try:
    received_message = request.values.get("Body", None)
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

    # Get mentor type
    if previous_interaction_count == 0:
      mentor_type = random.choice(["local", "refugee", "AI"])
    else:
      mentor_type = previous_interaction_records[0]["mentor_type"]

    # Send either a simple greeting, main advice, or followup advice depending on the previous_interaction_count
    if previous_interaction_count == 0:
      message_to_send = "Hello there, please tell me your business idea, and I will provide adivce"
    else:
      chatapp = ChatApp(mentor_type)
      for record in previous_interaction_records:
        chatapp.messages.append({"role":"user", "content": record["received_message"]})
        chatapp.messages.append({"role":"assistant", "content": record['sent_message']})

      # Generate response
      if previous_interaction_count == 1:
        if mentor_type == 'local':
          received_message = (f"Understand and answer the question given by '{received_message}'. You are a highly integrated local entrepreneur mentor based in Kampala. \n" 
          "You have successfully started and managed businesses in this area for many years. \n"
          "You are well-connected, deeply understand the local market, and focus on practical solutions. \n"
          "You believe in step-by-step approaches to entrepreneurship. Now, you are providing solutions to the question raised.\n"
          "You guide entrepreneurs to build sustainable businesses by leveraging local resources, customer insights, and efficient planning.\n"
          "You are continuing a detailed mentoring conversation with the user. \n"
          "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n")
        elif mentor_type == 'refugee':
          received_message = (f"Understand and answer the question given by '{received_message}'. You are a refugee entrepreneur mentor who overcame significant challenges to build a thriving business in Kampala. \n"
          "You understand the difficulties faced by refugees, including limited resources, unfamiliar markets, and social barriers, \n"
          "but you firmly believe in their potential. \n"
          "Your advice is empathetic, motivational, and aimed at fostering creativity, resilience, and ambition. "
          "You encourage entrepreneurs to embrace bold, innovative approaches while finding ways to overcome constraints.\n\n"
          "You are continuing a detailed mentoring conversation with the user. \n"
          "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n")
        else:
          received_message = (f"Understand and answer the question given by '{received_message}'."
          "You are continuing a detailed mentoring conversation with the user. \n"
          "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n")
        
        #get response from the chatbot
        message_to_send = chatapp.chat(received_message)
      
      if previous_interaction_count == 1: 
        message_to_send += "Please feel free to ask one more follow up question."
      else:
        message_to_send += "Please feel free to ask more questions. Just make sure to re-state your business idea."
      app.logger.error(f"message_to_send={message_to_send}")

    # Send whatsapp return message in chunks
    i = 0
    chunk_sz = int(os.environ["CHUNK_SZ"])
    message_failure_flag = False
    while i < len(message_to_send):
      # Increment by chunk sz and search for nearest end of a sentence
      j = min(i + chunk_sz, len(message_to_send))
      if j < len(message_to_send):
        while message_to_send[j] not in [".", "?", "!"] and j < len(message_to_send):
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
      k = 1
      while k <= int(os.environ["K_MAX"]) and twilio_message.status not in ["delivery_unknown", "delivered", "undelivered", "failed", "read"]:
          time.sleep(k)
          twilio_message = twilio_client.messages(sid).fetch()
          k += 1

      # If message was not successfully sent, delivered, or read; then return error
      if twilio_message.status not in ["sent", "delivered", "read"]:
        server_msg = f"devliery of response message sid={sid} failed for {timestamp} incoming message from {phone}"
        message_failure_flag = True
        break
      

    if not message_failure_flag:
      server_msg = "success"
      # Write record to dynamodb
      interactions.add_interaction(phone, timestamp, received_message, message_to_send, mentor_type, name)

  else:
    name = ""
    if phone is None and received_message is not None:
      server_msg = "Phone not parsed successfully"
    elif phone is not None and received_message is None:
      server_msg = "Body not parsed successfully"
    else:
      server_msg = "Phone and body not parsed successfully"


  return {"msg": server_msg}


if __name__ == "__main__":
   app.run(host="0.0.0.0", port=8080)