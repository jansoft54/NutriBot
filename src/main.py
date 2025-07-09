
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
from typing import Any, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END

from src.agents.goalagent import GoalsAgent
from src.agents.nutritionagent import NutritionAgent


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Bitte setze GEMINI_API_KEY in deiner .env-Datei")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY
)


class State(TypedDict):
    prompt: str
    extracted: Dict[str, Any]
    additional_question: str
    messages: list
    nutrition: Dict


builder = StateGraph(State)
agents = [GoalsAgent(llm), NutritionAgent(llm)]
for a in agents:
    builder = a.build_graph(builder)

graph = builder.compile()


def cli_loop():
    state: State = {
        "prompt": input("Prompt: "),
        "extracted": {

        },
        "additional_question": "",
        "nutrition": {}
    }
    result = graph.invoke(state, config={
        "configurable": {"thread_id": "x"},
        "recursion_limit": 50
    })
   # print(result)


if __name__ == "__main__":
    cli_loop()
