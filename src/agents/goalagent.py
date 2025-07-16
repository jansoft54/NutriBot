from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError
from src.agents.agent import Agent
from src.agents.nutritionagent import NutritionAgent
from src.prompt_templates.templates import GOAL_EXTRACTION_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langgraph.types import interrupt, Command

import json


class GoalsAgent(Agent):
    EXTRACT_INFO_NODE = "extract"
    ASK_QUESTION_NODE = "ask_question"

    def __init__(self, llm):
        self.llm = llm
        self.conversation = []

    def ask_llm(self, input_vars):
        self.prompt = PromptTemplate(
            input_variables=input_vars.keys(),
            template=GOAL_EXTRACTION_PROMPT)
        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt)
        return self.llm_chain.run(input_vars)

    def build_graph(self, builder: StateGraph) -> StateGraph:
        builder.add_node(GoalsAgent.EXTRACT_INFO_NODE, self.extract_info)
        builder.add_node(GoalsAgent.ASK_QUESTION_NODE, self.ask_follow_up)
        builder.add_edge(START, GoalsAgent.EXTRACT_INFO_NODE)

        return builder

    def extract_info(self, state) -> dict:
        self.conversation.append(f"USER:{state["prompt"]}")
        raw = self.ask_llm(
            {"prompt": state["prompt"],
             "extracted_json": state["extracted"],
             "conversation": "\n".join(self.conversation)})
        try:
            result = self.parse_json(raw)
        except ValidationError as e:
            return {"additional_question": "", "extracted": state["extracted"]}

        if result["additional_question"]:
            goto = GoalsAgent.ASK_QUESTION_NODE
        else:
            goto = NutritionAgent.LLM_CALL_TOOL_NODE
        return Command(
            update={
                "extracted": result["extracted"],
                "additional_question": result["additional_question"],
                "last_node": GoalsAgent.EXTRACT_INFO_NODE,
            },
            goto=goto,
        )

    def ask_follow_up(self, state):
        print("ASK")
        self.conversation.append(f"ASSISTANT:{state["additional_question"]}")
        prompt = interrupt(
            {"additional_question": state["additional_question"],
             "last_node": GoalsAgent.ASK_QUESTION_NODE})

        return Command(
            update={"prompt": prompt,
                    "last_node": GoalsAgent.ASK_QUESTION_NODE, },
            goto=GoalsAgent.EXTRACT_INFO_NODE,
        )
