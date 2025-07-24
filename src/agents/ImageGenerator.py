from langgraph.types import Command
from langchain_core.messages import HumanMessage
import openai

class ImageGeneratorAgent:
    ASK_NODE = "ask_image_preference"
    PARSE_NODE = "parse_reply"
    GENERATE_NODE = "generate_image"
    SKIP_NODE = "skip_image"

    def __init__(self):
        pass  # No LLM needed here unless you want to generate the question dynamically

    def build_graph(self, builder):
        builder.add_node(self.ASK_NODE, self.ask_image_question)
        builder.add_node(self.PARSE_NODE, self.parse_reply)
        builder.add_node(self.GENERATE_NODE, self.generate_image)
        builder.add_node(self.SKIP_NODE, self.skip_image)

        # Flow: ask -> parse -> (generate | skip)
        builder.set_entry_point(self.ASK_NODE)
        builder.add_edge(self.ASK_NODE, self.PARSE_NODE)

        def route(state):
            answer = state.get("user_message", "").strip().lower()
            return self.GENERATE_NODE if answer.startswith("y") else self.SKIP_NODE

        builder.add_conditional_edges(
            self.PARSE_NODE,
            route,
            conditional_edge_mapping={
                self.GENERATE_NODE: self.GENERATE_NODE,
                self.SKIP_NODE: self.SKIP_NODE,
            }
        )

        builder.add_edge(self.GENERATE_NODE, "END")
        builder.add_edge(self.SKIP_NODE, "END")

        return builder

    def ask_image_question(self, state: dict) -> Command:
        message = HumanMessage(content="Would you like to see an image of this recipe?")
        return Command(update={"messages": [message]}, goto=self.PARSE_NODE)

    def parse_reply(self, state: dict) -> dict:
        # Just passes state forward. Assumes user reply is stored in state["user_message"]
        return state

    def generate_image(self, state: dict) -> dict:
        recipe = state.get("recipe")
        if not recipe:
            state["error"] = "Missing recipe"
            return state

        prompt = f"A photo of {recipe['name']} with {', '.join(recipe['ingredients'][:3])}"
        try:
            response = openai.Image.create(prompt=prompt, n=1, size="512x512")
            state["image_url"] = response["data"][0]["url"]
        except Exception as e:
            state["image_url"] = None
            state["error"] = f"Image generation failed: {str(e)}"

        return state

    def skip_image(self, state: dict) -> dict:
        state["image_url"] = None
        return state
