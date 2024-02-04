import ollama

class Message:
    content: str
    role: str

    def __init__(self, content: str, role: str) -> None:
        self.content = content
        self.role = role

        print(content, role)

class Choice:
    message: Message
    def __init__(self, m: Message) -> None:
        self.message = m

class OAIResponse:
    choices: list[Choice]

    def __init__(self, raw_message: dict) -> None:
        self.choices = [Choice(Message(raw_message['content'], raw_message['role']))]

class Completions:
    def __init__(self) -> None:
        pass

    def create(self, model: str, messages: list, response_format: dict):
        response = ollama.chat('llama2', messages, stream=False, format='json' if 'json' in response_format['type'] else '')

        return OAIResponse(response['message'])

class Chat:
    def __init__(self) -> None:
        self.completions = Completions()

class Ollama:
    def __init__(self) -> None:
        self.chat = Chat()

