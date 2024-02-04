import os
from typing import Literal
from openai import OpenAI
import time
import json

# pull in .env
from dotenv import load_dotenv
from pydantic import BaseModel


from slnm import Slnm

load_dotenv()

OPEN_AI_API_KEY = os.environ["OPENAI_API_KEY"]
EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
SITE = os.environ["SITE"]

llm = OpenAI(api_key=OPEN_AI_API_KEY)

slnm = Slnm(SITE)

all_messages = [
    {
        'content': f'''
    You are helping a user naviagte a website. 
    Their ultimate goal is to submit a request on the jobs page.
    They will describe the state of the website, your job is to respond with the best action.

    Here is the job info for the form:
    job type: picc line
    facility: st davids
    room num: 345
    contact: 512-555-5555
    contact name: dom
    you can leave the nurse field blank


    It may force you to login first, if this is the case use the following credentials:
    email/username: {EMAIL}
    password: {PASSWORD}
    '''.strip(),
        'role': 'system'
    }
]


class LLMAction(BaseModel):
    action:  Literal["click", "navigate", "input"]
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

    if response.choices[0].message.content.strip() == 'done':
        break

    action = LLMAction.model_validate(
        json.loads(response.choices[0].message.content.strip()))

    print(action)

    if action.action == 'click':
        ctx = slnm.click_button(action.target)
    elif action.action == 'navigate':
        ctx = slnm.click_link(action.target)
    elif action.action == 'input':
        ctx = slnm.edit_input(action.target, action.value)


time.sleep(30)
