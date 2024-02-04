import os
from typing import Literal
from openai import OpenAI
import time
import json

# pull in .env
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from olma import Ollama
from slnm import Slnm

load_dotenv()

OPEN_AI_API_KEY = os.environ["OPENAI_API_KEY"]
EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
SITE = os.environ["SITE"]

llm = Ollama()
# llm = OpenAI(api_key=OPEN_AI_API_KEY)

slnm = Slnm(SITE)

all_messages = [
    {
        'content': f'''
    You are helping a user naviagte a website. 
    Their ultimate goal is to submit a new post to the website.
    They will describe the state of the website, your job is to respond with the best action.

    Here is the info for the form:
    the content of the post is: "Initial commit"


    It may force you to login first, if this is the case use the following credentials:
    email/username: {EMAIL}
    password: {PASSWORD}
    '''.strip(),
        'role': 'system'
    }
]


class LLMAction(BaseModel):
    action:  Literal["click", "navigate", "input", "done"]
    target: str
    value: str | None = None


ctx = None

while True:
    all_messages.append({
        'content': ctx or slnm.format_message_for_llm(),
        'role': 'user'
    })

    ctx = None

    response = llm.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=all_messages,
        response_format={"type": "json_object"}
    )

    all_messages.append({
        'content': response.choices[0].message.content,
        'role': 'assistant'
    })

    try:
        action = LLMAction.model_validate(
            json.loads(response.choices[0].message.content.strip()))
    except ValidationError as e:
        ctx = str(e)
        continue
    if action.action == 'done':
        break

    print(action)
    # cont = input('Press enter to continue')

    if action.action == 'click':
        ctx = slnm.click_button(action.target)
    elif action.action == 'navigate':
        ctx = slnm.click_link(action.target)
    elif action.action == 'input':
        if not action.value:
            raise ValueError('input action must have a value')
        ctx = slnm.edit_input(action.target, action.value)


time.sleep(30)
