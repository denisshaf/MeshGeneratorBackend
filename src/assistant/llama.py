import time


class LlamaMock:
    message = {"role": "assistant", "content": "Hello! How can I help you today?"}

    def __init__(self, model_path, n_ctx, n_threads):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads

    def create_chat_completion(self, messages, temperature, stream=False):
        if not stream:
            return [
                {"choices": [{"delta": {"role": "assistant"}}]},
                {
                    "choices": [
                        {"delta": {"content": "Hello! How can I help you today?"}}
                    ]
                },
            ]

        yield {"choices": [{"delta": {"role": self.message["role"]}}]}
        content = self.message["content"]
        for word in content.split():
            yield {"choices": [{"delta": {"content": word + " "}}]}
            time.sleep(1)
