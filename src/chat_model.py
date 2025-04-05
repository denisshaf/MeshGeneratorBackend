class ChatAssistant:
    def __init__(self, llm):
        self.llm = llm
        self.chat_history = []
        self.temperature = 0.7

    def add_user_message(self, message):
        self.chat_history.append({'role': 'user', 'content': message})

    def add_assistant_message(self, message):
        self.chat_history.append({'role': 'assistant', 'content': message})

    def get_response(self, stream=False):
        response = self.llm.create_chat_completion(
            messages=self.chat_history,
            temperature=self.temperature,
            stream=stream
        )
        return response