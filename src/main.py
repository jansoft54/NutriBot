from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
from typing import Any, Dict, List
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from src.agents.goalagent import GoalsAgent
from src.agents.nutritionagent import NutritionAgent

# The State class definition was missing. It's back now.
class State(TypedDict):
    prompt: str
    extracted: Dict[str, Any]
    additional_question: str
    messages: List
    nutrition: Dict


def cli_loop(graph):
    """The main interactive loop for the user."""
    thread_id = input("Enter a session ID to continue a session or create a new one: ")
    config = {"configurable": {"thread_id": thread_id}}

    current_state_snapshot = graph.get_state(config)

    # Initialize with default values to avoid KeyError for missing keys on new sessions
    starting_state = {
        "prompt": "",
        "extracted": {},
        "additional_question": "",
        "messages": [],
        "nutrition": {},
    }

    if current_state_snapshot and current_state_snapshot.values.get("extracted"):
        print("\nFound a previous session with the following extracted data:")
        extracted_data = current_state_snapshot.values["extracted"]
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        
        restore = input("Do you want to restore *only* this extracted data and start a new chat? (yes/no): ").lower()
        
        if restore == 'yes':
            print("Restoring extracted data and clearing previous conversation history.")
            starting_state = {
                "prompt": "",
                "extracted": extracted_data,
                "additional_question": "",
                "messages": [],
                "nutrition": {}
            }
            graph.update_state(config, starting_state)
        else:
            print("Starting a completely new session.")
            graph.update_state(config, {})

    initial_prompt = input("Prompt: ")
    starting_state["prompt"] = initial_prompt
    
    result = graph.invoke(starting_state, config=config)

    print("\n--- Final State ---")
    final_state = result.copy()
    if 'messages' in final_state:
        del final_state['messages']
    print(json.dumps(final_state, indent=2, ensure_ascii=False))


def main():
    """Main function to set up and run the application."""
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise RuntimeError("Bitte setze GEMINI_API_KEY in deiner .env-Datei")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=API_KEY
    )

    with SqliteSaver.from_conn_string("checkpointer.sqlite") as memory:
        
        builder = StateGraph(State)
        agents = [GoalsAgent(llm), NutritionAgent(llm)]
        for a in agents:
            builder = a.build_graph(builder)

        graph = builder.compile(checkpointer=memory)

        cli_loop(graph)


if __name__ == "__main__":
    main()