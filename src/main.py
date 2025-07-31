

import os

from langgraph.types import Command
from dotenv import load_dotenv
import gradio as gr

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph import StateGraph
from src.agents.goalagent import GoalsAgent
from src.agents.imageagent import ImageAgent
from src.agents.nutritionagent import NutritionAgent
from src.agents.recipeagent import RecipeAgent
from typing_extensions import TypedDict
from typing import Any, Dict
from langgraph.checkpoint.sqlite import SqliteSaver

# Load environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Bitte setze GEMINI_API_KEY in deiner .env-Datei")

# Define state structure


class State(TypedDict):
    prompt: str
    memory_extracted: Dict[str, Any]
    extracted: Dict[str, Any]
    additional_question: str
    messages: list
    nutrition: Dict
    final_result: list
    last_node: str
    nutrition_text: str
    recipe_final: str
    image_name: str


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
builder = StateGraph(State)
agents = [GoalsAgent(llm), NutritionAgent(
    llm), RecipeAgent(llm), ImageAgent(llm)]
for agent in agents:
    builder = agent.build_graph(builder)
saver_cm = SqliteSaver.from_conn_string("chat_memory.db")
sqlite_saver = saver_cm.__enter__()

graph = builder.compile(checkpointer=sqlite_saver,
                        )
config = {"configurable": {"thread_id": "gradio_session"}}
latest_snapshot = graph.get_state(config)
saved_state = latest_snapshot.values

memory_extracted = saved_state.get("extracted", {})
resume = False


def respond_fn(user_message, chat_history, state):
    global resume

    if resume:
        print("RESUME")
        cmd = Command(resume={"prompt": user_message})
        interrupt_obj = graph.invoke(cmd, config)
        interrupt_obj = interrupt_obj["__interrupt__"][0].value
    else:
        start_state = {
            "prompt": user_message,
            "memory_extracted": memory_extracted,
            "extracted": {},
            "additional_question": "",
            "messages": [],
            "nutrition": {},
            "final_result": [],
            "last_node": None,
            "nutrition_text": "",
            "image_name": "",
            "recipe_final": ""

        }
        state = graph.invoke(start_state, config)
        interrupt_obj = state["__interrupt__"][0].value

    # 2) Inspect result.next to see which node just ran
    node = interrupt_obj["last_node"]
    # 3) Pick your bot_text based on node
    if node == NutritionAgent.DECIDE_CONTINUE_NODE:
        bot_text = interrupt_obj["nutrition_text"]
    if node == GoalsAgent.ASK_QUESTION_NODE:
        bot_text = interrupt_obj["additional_question"]
    if node == RecipeAgent.DECIDE_CONTINUE_NODE:
        if "image_name" in interrupt_obj.keys():
            bot_text = gr.Image(
                value=interrupt_obj["image_name"], type="filepath")
        else:
            bot_text = interrupt_obj["llm_msg"]

    resume = True
    # 4) Return
    chat_history = (chat_history or []) + [(user_message, bot_text)]
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
