from utils.langGraph import langGraph_function
from utils.macro_calculator_utils import macro_nutrition
import chainlit as cl
import os
from typing import Dict, Optional
from dotenv import load_dotenv
import logging
from chainlit.input_widget import Select, Slider,TextInput

load_dotenv()
user_data={}
logging.basicConfig(level=logging.DEBUG)

def handle_query(question):
    try:
        result = langGraph_function(question)
        logging.info(f"Workflow Result: {result}")
        return result
    except Exception as e:
        logging.error(f"Error: {e}")
        return f"An error occurred: {e}"

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    user_data = raw_user_data
    print("OAuth successful. User data:", raw_user_data)

    # Return a user object for the Chainlit session
    return cl.User(identifier=raw_user_data.get("name"))    



@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            Select(
                id="gender",
                label="Gender",
                items={  
                    "Male": "m",
                    "Female": "f"
                },
                initial_value='m',
            ),
            TextInput(id="age", label="Age"),                
            TextInput(id="height", label="Height", placeholder="cm"),            
            TextInput(id="weight", label="Weight", placeholder="kg"), 
            Select(
                id="activity",
                label="Activity",
                items={  
                    "sedentary": "1",
                    "lightly active": "2",
                    "moderately active": "3",
                    "very active": "4",
                    "super active": "5",
                },
                initial_value='1',
            ),
            Select(
                id="your_goal",
                label="Your Goal",
                items={  
                    "Maintain weigh": "1",
                    "Weight loss 0.5 kg per week": "2",
                    "Mild weight gain of 0.5 kg per week": "3",
                },
                initial_value='1',
            ),
        ]
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    print("---", user_data)
    print("on_settings_update", settings)
    print(macro_nutrition(int(settings['weight']), int(settings['height']), int(settings['age']), settings['gender'], int(settings['activity']), int(settings['your_goal'])))

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages."""
    try:
        user_message = message.content
        response = handle_query(user_message)
        await cl.Message(content=response).send()
    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()


logging.info("Running the bot...")
