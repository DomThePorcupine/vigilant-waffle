from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import string
import os
import random

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]

alphabet = string.ascii_lowercase + string.digits


class Slnm:
    driver: webdriver.Chrome
    actions: list[str]

    clickable_buttons: dict[str, WebElement] = {}

    def __init__(self, url: str):
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()))
        self.driver.get(url)

        self.driver.implicitly_wait(5)

        # uncomment to speed up
        # login
        # self.driver.find_element(By.NAME, 'email').send_keys(EMAIL)
        # self.driver.find_element(By.NAME, 'password').send_keys(PASSWORD)
        # self.driver.find_element(By.TAG_NAME, 'button').click()
        # # navigate to jobs
        # self.driver.find_element(By.XPATH, "//a[text()='Jobs']").click()
        # time.sleep(2)

    def random_id(self):
        return ''.join(random.choices(alphabet, k=8))

    def current_path(self) -> str:
        return self.driver.current_url

    def format_option(self, option: WebElement) -> str:
        return f"value: {option.get_attribute('value')}, text: {option.text}"

    def format_input(self, input: WebElement) -> str:
        name = input.get_attribute('name')
        type = input.get_attribute('type')
        autocomplete = input.get_attribute('autocomplete')
        value = input.get_attribute('value')
        return f"name: {name}, type: {autocomplete if type == 'text' else type}, current_value: {value}"

    def format_a_href(self, a: WebElement) -> str:
        href = a.get_attribute('href').split('?')[0]
        id = a.get_attribute('id')
        text = a.text
        # if niether id nor text omit them
        if not id and not text:
            None
        # omit empty id, text
        if not id:
            return f"href: {href}, text: {text}"
        if not text:
            return f"href: {href}, id: {id}"

        return f"href: {href}, id: {id}, text: {text}"

    def get_inputs(self) -> list[str]:
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')

        # filter disabled inputs
        inputs = [i for i in inputs if not i.get_attribute('disabled')]
        # filter empty selects
        selects = [s for s in selects if s.find_elements(
            By.TAG_NAME, 'option')]

        slcts_with_options = [
            f"name: \"{s.get_attribute('name')}\", type: {s.get_attribute('type')}, current_value: {s.get_attribute('value')}, options: {', '.join([self.format_option(o) for o in s.find_elements(By.TAG_NAME, 'option')])}" for s in selects]
        print('get_inputs', slcts_with_options)
        return [self.format_input(i) for i in inputs] + slcts_with_options

    def get_links(self) -> list[str]:
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        return [self.format_a_href(l) for l in links]

    def get_buttons(self) -> list[str]:
        buttons = self.driver.find_elements(By.TAG_NAME, 'button')
        # filter empty
        buttons = [b for b in buttons if b.get_attribute('name') or b.text]

        if len(buttons) == 0:
            # try looking for divs with role=button
            maybe_buttons = self.driver.find_elements(By.TAG_NAME, 'div')
            maybe_buttons = [
                b for b in maybe_buttons if b.get_attribute('role') == 'button']
            # now give them all unique names
            for b in maybe_buttons:
                self.driver.execute_script(
                    "arguments[0].setAttribute('name',arguments[1])", b, self.random_id())

            return [f"name: {b.get_attribute('name')} text: {b.text}" for b in maybe_buttons]

        # get name or inner text of button
        return [f"name: {b.get_attribute('name')}, text: {b.text}" for b in buttons]

    def click_link(self, path: str) -> str | None:
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        for l in links:
            if path in l.get_attribute('href'):
                l.click()
                return ''

        return f'link {path} not found'

    def click_button(self, button: str) -> str | None:
        buttons = self.driver.find_elements(By.TAG_NAME, 'button')
        for b in buttons:
            if b.text.lower().strip() == button.lower().strip():
                b.click()
                return None

        for b in self.driver.find_elements(By.TAG_NAME, 'div'):
            if b.get_attribute('name') == button:
                b.click()
                return None
        return f'button {button} not found'

    def edit_input(self, name: str, value: str) -> str | None:
        print(name, value)
        # check if input is a select
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        for s in selects:
            if s.get_attribute('name') == name:
                # try to find the option
                # o = s.find_element(By.XPATH, f"//option[text()='{value}']")
                options = s.find_elements(By.TAG_NAME, 'option')
                o = None

                for option in options:
                    if option.get_attribute('value') == value:
                        o = option
                        break

                # if not found, tell the user
                if not o:
                    return f"option {value} not found, options are: {', '.join([self.format_option(o) for o in s.find_elements(By.TAG_NAME, 'option')])}"
                # select the option
                o.click()
                return None

        all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')

        for i in all_inputs:
            if i.get_attribute('name') == name:
                i.send_keys(value)
                return None

        return f'No input with name {name} found'

    def format_message_for_llm(self) -> str:
        time.sleep(2)
        content = f'''
The current path is: {self.current_path()}
The available navigatable paths are: {', '.join(self.get_links())}
The available clickable buttons are: {', '.join(self.get_buttons())}
The available inputs are: {', '.join(self.get_inputs())}

You can do NOTHING except what is listed above.

Format your response as JSON in the following format:
{{
    "action": "click" | "navigate" | "input",
    "target": "element name" | "path",
    "value": "input value" // optional
}}

If you are done, simply respond with "done"
'''.strip()

        print(content)

        return content
