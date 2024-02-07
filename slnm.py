from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import StaleElementReferenceException
import time
import string
import os
import random
import json

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]

alphabet = string.ascii_lowercase + string.digits


class SlnmOptions:
    disable_href: bool = False

    def __init__(self, disable_href: bool = False):
        self.disable_href = disable_href


class Slnm:
    driver: webdriver.Chrome
    actions: list[str]
    options: SlnmOptions
    clickable_buttons: dict[str, WebElement] = {}

    def __init__(self, url: str, options: SlnmOptions = SlnmOptions()):
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()))
        self.driver.get(url)
        self.options = options
        self.driver.implicitly_wait(3)

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

    def check_for_form_errors(self) -> str | None:
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')
        selects = self.driver.find_elements(By.TAG_NAME, 'select')

        # filter disabled inputs
        inputs = [i for i in inputs if not i.get_attribute('disabled')]
        # filter empty selects
        selects = [s for s in selects if s.find_elements(
            By.TAG_NAME, 'option')]

        # check for errors
        for i in inputs:
            if i.get_attribute('errortext'):
                return f'input {i.get_attribute("name")} has an error: {i.get_attribute("errortext")}'

    def cleaned_page_body(self) -> str:
        print(self.driver.find_element(By.TAG_NAME, 'body').text.strip())
        return self.driver.find_element(By.TAG_NAME, 'body').text.strip()

    def current_path(self) -> str:
        return self.driver.current_url

    def format_option(self, option: WebElement) -> str:
        return json.dumps(self.remove_empty({
            "value": option.get_attribute('value'),
            "text": option.text
        }), separators=(',', ':'))
        # return f"value: {option.get_attribute('value')}, text: {option.text}"

    def remove_empty(self, d: dict) -> dict:
        return {k: v for k, v in d.items() if v}

    def format_input(self, input: WebElement) -> str:
        # check if interactable
        if not input.is_enabled():
            raise Exception('input is not interactable')
            # return None

        if not input.is_displayed():
            raise Exception('input is not displayed')
            # return None

        name = input.get_attribute('name')
        type = input.get_attribute('type')
        # autocomplete = input.get_attribute('autocomplete')

        autocomplete = input.get_attribute('autocomplete') if input.get_attribute(
            'autocomplete') != 'off' else None
        placeholder = input.get_attribute('placeholder')

        errors = input.get_attribute('errortext')
        value = input.get_attribute('value')

        tid = self.random_id()
        self.driver.execute_script(
            "arguments[0].setAttribute('name',arguments[1])", input, tid)

        return json.dumps(self.remove_empty({
            "target_id": tid,
            'name': name,
            "type": autocomplete if type == 'text' else type,
            "current_value": value,
            "errors": errors,
            "placeholder": placeholder
        }), separators=(',', ':'))
        # return f"target_id: {name}, type: {autocomplete if type == 'text' else type}, current_value: {value}{', errors: ' + errors if errors else ''}"

    def format_a_href(self, a: WebElement) -> str:
        href = a.get_attribute('href').split('?')[0]
        id = a.get_attribute('id')
        text = a.text
        # if niether id nor text omit them
        if not id and not text:
            None
        # omit empty id, text
        return json.dumps(self.remove_empty({
            "id": id,
            "text": text,
            "href": href
        }), separators=(',', ':'))

    def format_select_input(self, select: WebElement) -> str:
        name = select.get_attribute('name')
        type = select.get_attribute('type')
        current_value = select.get_attribute('value')
        options = select.find_elements(By.TAG_NAME, 'option')
        return json.dumps(self.remove_empty({
            "target_id": name,
            "type": type,
            "current_value": current_value,
            "options": [self.format_option(o) for o in options]
        }), separators=(',', ':'))
        # return f"target_id: {name}, type: {type}, current_value: {current_value}, options: {', '.join([self.format_option(o) for o in options])}"

    def get_inputs(self) -> list[str]:
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')

        # filter disabled inputs
        inputs = [i for i in inputs if not i.get_attribute(
            'disabled')]
        # filter empty selects
        selects = [s for s in selects if s.find_elements(
            By.TAG_NAME, 'option')]

        # filter not displayed inputs
        inputs = [i for i in inputs if i.is_displayed()]

        # filter by offsetWidth > 0
        inputs = [i for i in inputs if int(
            i.get_attribute('offsetWidth') or '0') > 0]

        # slcts_with_options = [
        #     f"target_id: \"{s.get_attribute('name')}\", type: {s.get_attribute('type')}, current_value: {s.get_attribute('value')}, options: {', '.join([self.format_option(o) for o in s.find_elements(By.TAG_NAME, 'option')])}" for s in selects]

        return [self.format_input(i) for i in inputs] + [self.format_select_input(s) for s in selects]

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
            buttons = [
                b for b in maybe_buttons if b.get_attribute('role') == 'button']

        # now give them all unique names (if they don't have one already)
        for b in buttons:
            if not b.get_attribute('name'):
                self.driver.execute_script(
                    "arguments[0].setAttribute('name',arguments[1])", b, self.random_id())

        # get name or inner text of button
        return [json.dumps(self.remove_empty({
            "target_id": b.get_attribute('name'),
            "text": b.text
        }), separators=(',', ':')) for b in buttons]
        # return [f"target_id: {b.get_attribute('name')}, text: {b.text}" for b in buttons]

    def click_link(self, path: str) -> str | None:
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        for l in links:
            if path in l.get_attribute('href'):
                l.click()
                return ''

        return f'link {path} not found'

    def click_button(self, button: str) -> str | None:
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            div_buttons = self.driver.find_elements(By.TAG_NAME, 'div')
            # filter by role
            div_buttons = [
                b for b in div_buttons if b.get_attribute('role') == 'button']
            buttons = buttons + div_buttons

            for b in buttons:
                if b.text.lower().strip() == button.lower().strip():
                    b.click()
                    return None
                if b.get_attribute('name') == button:
                    b.click()
                    return None

            return f'button {button} not found'
        except StaleElementReferenceException as e:
            return self.click_button(button)

    def edit_input(self, target_id: str, value: str) -> str | None:
        # check if input is a select
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        for s in selects:
            if s.get_attribute('name') == target_id:
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
            if i.get_attribute('name') == target_id:
                i.clear()
                i.send_keys(value)
                time.sleep(0.5)

                # print value
                print(f'---> Sending keys {i.get_attribute("value")}')

                # check if the value has been set
                while i.get_attribute('value') != value:
                    print('---> Sending enter')
                    i.send_keys(Keys.ENTER)
                    time.sleep(0.5)
                # press enter
                # i.send_keys(Keys.TAB)
                # unfocus
                # self.driver.find_element(By.TAG_NAME, 'body').click()
                # send right arrow key
                i.send_keys(Keys.ARROW_DOWN)
                i.send_keys(Keys.ENTER)
                self.driver.execute_script('arguments[0].blur()', i)
                input('Press enter to continue')
                return None

        return f'No input with name {target_id} found'

    def format_message_for_llm(self) -> str:
        time.sleep(1)

        links = []
        if not self.options.disable_href:
            links = self.get_links()

        content = f'''
The current path is: {self.current_path().split('?')[0]}
{'The available navigatable paths are: ' if links else ''}{', '.join(links)}
The available clickable buttons are: {', '.join(self.get_buttons())}
The available inputs are: {', '.join(self.get_inputs())}

You can do NOTHING except what is listed above.
'''.strip()

        print(content)

        return content
