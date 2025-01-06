
import os
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from utils.langGraph import langGraph_function

load_dotenv()
app = Flask(__name__)

twilio_account_sid = os.environ["TWILIO_ACCOUNT_SID"]
twilio_auth_token = os.environ["TWILIO_AUTH_TOKEN"]


def handle_query(question):
    try:
        result = langGraph_function(question)
        print(f"Workflow Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def hello_world():
    
    return "✨ Hello, everyone the Life line Chat Bot is here ✨"


# Define a route to handle incoming requests
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").lower()
    print("WhatsApp Message: ", incoming_msg)

    # Generate the answer
    answer = handle_query(incoming_msg)
    print("BOT Answer: ", answer)

    # Create a Twilio response
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(answer)

    return str(resp)


# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
