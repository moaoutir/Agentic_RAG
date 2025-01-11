from utils.langGraph import langGraph_function
from utils.macro_calculator_utils import macro_nutrition
from utils.sql_alchemy_utils import insert_user_data, get_user_data, initialize_database
import chainlit as cl
import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv
import logging
from chainlit.input_widget import Select, Slider,TextInput

load_dotenv()
path_users_macro_nutrition = "./databases/users/users_macro_nutrition.db"

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
        print("OAuth successful. User data:", raw_user_data.get("name"))
        return cl.User(identifier=raw_user_data.get("id"), display_name=raw_user_data.get("name"))    

@cl.on_chat_start
async def start():
    initialize_database()
    id = cl.user_session.get("user").identifier
    user_data = get_user_data(id)
    print(user_data)
    if user_data is None:
        print("User data is None")
        user_data = (0, 0, 0, 0, 1, 1, 'm')
    settings = await cl.ChatSettings(
        [
            Select(
                id="gender",
                label="Gender",
                items={  
                    "Male": "m",
                    "Female": "f"
                },
                initial_value=user_data[-1],
            ),
            TextInput(id="age", label="Age", initial=str(user_data[3])),                
            TextInput(id="height", label="Height", placeholder="cm", initial=str(user_data[2])),            
            TextInput(id="weight", label="Weight", placeholder="kg", initial=str(user_data[1])), 
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
                initial_value=str(user_data[-3]),
            ),
            Select(
                id="goal",
                label="Your Goal",
                items={  
                    "Maintain weigh": "1",
                    "Weight loss 0.5 kg per week": "2",
                    "Mild weight gain of 0.5 kg per week": "3",
                },
                initial_value=str(user_data[-2]),
            ),
        ]
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    insert_user_data(cl.user_session.get("user").identifier, 
                     int(settings['weight']), 
                     int(settings['height']), 
                     int(settings['age']), 
                     int(settings['activity']), 
                     int(settings['goal']), 
                         settings['gender'])



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
