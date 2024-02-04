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

# llm = Ollama()
llm = OpenAI(api_key=OPEN_AI_API_KEY)

slnm = Slnm(SITE)

all_messages = [
    {
        'content': f'''
You are helping a user naviagte a website. 
Their ultimate goal is to create a new region on the website.
They will describe the state of the website, your job is to respond with the best action.

Here is the info for the form:
the name of the region should be "Test Region 34"

Format your responses as JSON in the format:
{{
    "action": "click" | "navigate" | "input" | "done" | "read_page",
    "target": "target_id" | "path_to_navigate_to", // optional ONLY for done and read_page
    "value": "input value" // optional
}}

Example: To click the "Foo" button in: {{ "target_id": "twmzk30b", "text": "Foo" }} respond with:
{{
    "action": "click",
    "target": "twmzk30b"
}}

If you are done, simply respond with {{ "action": "done" }}

It may force you to login first, if this is the case use the following credentials:
email/username: {EMAIL}
password: {PASSWORD}
    '''.strip(),
        'role': 'system'
    }
]


class LLMAction(BaseModel):
    action:  Literal["click", "navigate", "input", "done", "read_page"]
    target: str | None = None
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

    # overwrite to json file
    with open('chat_log.json', 'w') as f:
        json.dump(all_messages, f, indent=2)

    try:
        action = LLMAction.model_validate(
            json.loads(response.choices[0].message.content.strip()))
    except ValidationError as e:
        print(f'err: {response.choices[0].message.content.strip()}')
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
    elif action.action == 'read_page':
        ctx = slnm.cleaned_page_body()
    elif action.action == 'input':
        if not action.value:
            ctx = 'input action requires a value'
            continue
        ctx = slnm.edit_input(action.target, action.value)


time.sleep(30)
