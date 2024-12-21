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

app = Flask(__name__)

dynamodb = boto3.resource("dynamodb",region_name=os.environ["AWS_REGION"])
table = os.environ["DDB_TABLE"]
interactions = Interactions(dynamodb, logger=app.logger)

if not interactions.exists(table):
  interactions.create_table(table)

# Make twilio client
twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])


def generate_prompt(mentor_type, message, previous_interaction_count):
  if previous_interaction_count not in [1, 2]:
    raise ValueError(f"Invalid previous_interaction_count={previous_interaction_count} to call generate_prompt")

  if mentor_type == "local_mentor":
    if previous_interaction_count == 1:
      prompt = (
        "System Message (Local Mentor Persona):\n"
        "You are a highly integrated local entrepreneur mentor based in Kampala. "
        "You have successfully started and managed businesses in this area for many years. "
        "You are well-connected, deeply understand the local market, and focus on practical solutions. "
        "You believe in step-by-step approaches to entrepreneurship. "
        "You guide entrepreneurs to build sustainable businesses by leveraging local resources, customer insights, and efficient planning.\n\n"
        f"Analyze the business idea: '{message}'.\n"
        "Provide:\n"
        "1. **Feasibility Judgment**: Evaluate the idea's viability in Kampala, identifying its strengths and weaknesses. Suggest improvements where necessary.\n"
        "2. **Detailed Execution Plan**: Provide a clear, step-by-step plan tailored to the Kampala market, ensuring practicality and alignment with local conditions. Give examples of local Kampala laws that need to be addressed, how to differentiate the product from other Kampala competitors with ideas, and more.\n"
        "3. **Market Insights**: Offer specific insights into customer preferences, competition, and pricing strategies in Kampala.\n"
        "4. **Local Resources and Partnerships**: Recommend local suppliers, partnerships, or cost-effective solutions to optimize resources.\n"
        "5. **Enhancements and Alternatives**: Suggest specific ways to refine the idea and propose two specific alternative business ideas that align with local trends and needs.\n\n"
        "6. Give specific detailed examples on how to differentiate this product from others in the market. Be very very specific on how to differentiate the product.\n"
        "Your response must be specific, detailed, actionable, and practical, ensuring a sustainable path to success in the local market."
      )
    else:
      prompt = (
        f"Understand and answer the question given by '{message}'. You are a highly integrated local entrepreneur mentor based in Kampala. \n" 
        "You have successfully started and managed businesses in this area for many years. \n"
        "You are well-connected, deeply understand the local market, and focus on practical solutions. \n"
        "You believe in step-by-step approaches to entrepreneurship. Now, you are providing solutions to the question raised.\n"
        "You guide entrepreneurs to build sustainable businesses by leveraging local resources, customer insights, and efficient planning.\n"
      "You are continuing a detailed mentoring conversation with the user. \n"
      "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n"
      )

  elif mentor_type == "refugee mentor":
    if previous_interaction_count == 1:
      prompt = (
        "System Message (Refugee Mentor Persona):\n"
        "You are a refugee entrepreneur mentor who overcame significant challenges to build a thriving business in Kampala. "
        "You understand the difficulties faced by refugees, including limited resources, unfamiliar markets, and social barriers, "
        "but you firmly believe in their potential. "
        "Your advice is empathetic, motivational, and aimed at fostering creativity, resilience, and ambition. "
        "You encourage entrepreneurs to embrace bold, innovative approaches while finding ways to overcome constraints.\n\n"
        f"Analyze the business idea: '{message}'.\n"
        "Provide:\n"
        "1. **Feasibility Judgment**: Assess whether the idea is practical and achievable given the challenges of limited resources and unfamiliar markets. Suggest improvements where needed.\n"
        "2. **Actionable and Bold Plan**: Inspire creativity by offering a step-by-step plan that addresses resource constraints and leverages innovation. Give examples of local Kampala laws that need to be addressed, how to differentiate the product from other Kampala competitors with ideas, and more.\n"
        "3. **Resource Optimization**: Identify specifically tailored strategies to make the most of limited resources, including leveraging community support and unconventional methods.\n"
        "4. **Resilience and Adaptability**: Suggest ways to navigate setbacks and turn challenges into opportunities.\n"
        "5. **Community and Support Networks**: Highlight how to engage with local and refugee communities for collaboration and growth.\n"
        "6. **Alternative Ideas and Enhancements**: If the idea needs improvement, suggest specific changes and propose two alternative, impactful ideas that are bold yet achievable. Be specific about the alternative ideas and give examples.\n\n"
        "7. Give specific detailed examples on how to differentiate this product from others in the market. Be very very specific on how to differentiate the product.\n"
        "Your response must be highly motivational, empathetic, specific, detailed, and focused on leveraging creativity and resilience to succeed."
        )
    else:
      prompt = (
      f"Understand and answer the question given by '{message}'. You are a refugee entrepreneur mentor who overcame significant challenges to build a thriving business in Kampala. \n"
        "You understand the difficulties faced by refugees, including limited resources, unfamiliar markets, and social barriers, \n"
        "but you firmly believe in their potential. \n"
        "Your advice is empathetic, motivational, and aimed at fostering creativity, resilience, and ambition. "
        "You encourage entrepreneurs to embrace bold, innovative approaches while finding ways to overcome constraints.\n\n"
      "You are continuing a detailed mentoring conversation with the user. \n"
      "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n"
      )
  else:
    if previous_interaction_count == 1:
      prompt = (
        "System Message (General Mentor Persona):\n"
        "You are a general AI mentor providing intelligent, tailored business advice for entrepreneurs in Kampala. "
        "Your goal is to evaluate business ideas critically and offer specific, actionable guidance to enhance their feasibility and implementation.\n\n"
        f"Analyze the business idea: '{message}'.\n"
        "Provide:\n"
        "1. **Feasibility Analysis**: Determine whether the idea is viable and highlight areas for improvement.\n"
        "2. **Actionable Steps**: Suggest practical steps for implementing and growing the business idea effectively. Give examples of local Kampala laws that need to be addressed, how to differentiate the product from other Kampala competitors with ideas, and more.\n"
        "3. **Local Market Advice**: Offer insights into the Kampala market, including customer needs, competitive landscape, and pricing. Be specific about what marketing channels and how to do sales/marketing for this product. Give examples.\n"
        "4. **Improvements and Alternatives**: Provide suggestions to refine the idea and propose two alternative ideas better suited for Kampala's market.\n\n"
        "5. Give specific detailed examples on how to differentiate this product from others in the market. Be very very specific on how to differentiate the product.\n"
        "Your response should deliver clear, concise, and practical, specific, detailed advice to support entrepreneurial success."
        )
    else:
      prompt = (
        f"Understand and answer the question given by '{message}'."
      "You are continuing a detailed mentoring conversation with the user. \n"
      "Your goal is to answer the question by providing specific, actionable, relevant advice to the questions/concerns pointed out. \n"
      )

  return prompt

def get_chat_response(prompt: str, message: str) -> str:
    """
    Get a chat response from OpenAI's API based on the concatenated string message.
    :param prompt: System-level prompt for setting the conversation context.
    :param message: The concatenated string of all previous interactions.
    :return: AI-generated response as a string.
    """
    try:
        # Concatenate prompt and message into a single user message
        full_message = f"{prompt}\n{message}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": full_message},
            ],
            max_tokens=1000,
            api_key=os.environ["OPENAI_API_KEY"],
        )
        print("Response received successfully.")
        return response.choices[0].message["content"].strip()

    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")
        return "There was an error with your request. Please check your input and try again."
    except openai.error.AuthenticationError:
        print("Authentication Error: Check your API key.")
        return "There was an authentication error. Please verify your API key."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred. Please try again later."

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

    if previous_interaction_count < 3:
      # Get mentor type
      if previous_interaction_count == 0:
        mentor_type = random.choice(["local mentor", "refugee mentor", "AI Mentor"])
      else:
        mentor_type = previous_interaction_records[0]["mentor_type"]

      # Send either a simple greeting, main advice, or followup advice depending on the previous_interaction_count
      if previous_interaction_count == 0:
        message_to_send = "Hello there, please tell me your business idea, and I will provide adivce"
      else:
        # Define prompt
        prompt = generate_prompt(mentor_type, received_message, previous_interaction_count)
        app.logger.error(f"prompt={prompt}")

        # Generate response
        message_to_send = get_chat_response(prompt, received_message)
        if previous_interaction_count == 1: 
          message_to_send += "Please feel free to ask one more follow up question."
        else:
          message_to_send += "Thank you for using this chatbot service! Our interaction is now complete."
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
      server_msg = "exceeded maximum number of interactions"

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