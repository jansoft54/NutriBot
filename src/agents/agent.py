import json


class Agent():
    def parse_json(self, text):
        text = text.replace("```", "")
        text = text.replace("json", "")
        return json.loads(text)
