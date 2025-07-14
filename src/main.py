

import os
from dotenv import load_dotenv
import gradio as gr

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from src.agents.goalagent import GoalsAgent
from src.agents.nutritionagent import NutritionAgent
from src.agents.recipeagent import RecipeAgent
from typing_extensions import TypedDict
from typing import Any, Dict

# Load environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Bitte setze GEMINI_API_KEY in deiner .env-Datei")

# Define state structure


class State(TypedDict):
    prompt: str
    extracted: Dict[str, Any]
    additional_question: str
    messages: list
    nutrition: Dict
    final_result: list
    last_node: str
    nutrition_text: str


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
builder = StateGraph(State)
agents = [GoalsAgent(llm), NutritionAgent(llm), RecipeAgent(llm)]
for agent in agents:
    builder = agent.build_graph(builder)
graph = builder.compile(
    interrupt_after=[GoalsAgent.ASK_QUESTION_NODE]
)


def respond_fn(user_message, chat_history, state):
    if not state:
        state = {
            "prompt": user_message,
            "extracted": {},
            "additional_question": "",
            "messages": [],
            "nutrition": {},
            "final_result": [],
            "last_node": "",
            "nutrition_text": ""

        }
    else:
        state["prompt"] = user_message

    config = {"configurable": {"thread_id": "gradio_session"}}
    for new_state in graph.stream(
        state,
        config=config,
        stream_mode="values",
        interrupt_after=[GoalsAgent.ASK_QUESTION_NODE,
                         NutritionAgent.SHOW_TOOL_RESULTS_NODE,
                         RecipeAgent.SHOW_RESULTS]
    ):
        state = new_state

    if state.get("last_node") == GoalsAgent.ASK_QUESTION_NODE and state.get("additional_question"):
        bot_text = state["additional_question"]
    if state.get("last_node") == NutritionAgent.SHOW_TOOL_RESULTS_NODE:
        bot_text = state["nutrition_text"]
    if state.get("last_node") == RecipeAgent.SHOW_RESULTS:
        bot_text = state["nutrition_text"]

    if chat_history is None:
        chat_history = []
    chat_history.append((user_message, bot_text))
    return "", chat_history, state


def main():
    with gr.Blocks() as demo:
        gr.Markdown("## NutriBot")
        chatbot = gr.Chatbot(height="80vh")
        state = gr.State({})

        with gr.Row():
            inp = gr.Textbox(
                placeholder="Type your question...", show_label=False)
            btn = gr.Button("Send")

        btn.click(respond_fn, [inp, chatbot, state], [inp, chatbot, state])
        inp.submit(respond_fn, [inp, chatbot, state], [inp, chatbot, state])

    demo.launch()


if __name__ == "__main__":
    main()
