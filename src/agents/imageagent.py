from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError
from src.agents.agent import Agent

from src.agents.recipeagent import RecipeAgent
from src.prompt_templates.templates import DECISION_TEMPLATE_PROMPT, GOAL_EXTRACTION_PROMPT, IMAGE_AGENT_INFO_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from src.tools.gen_image import generate_image
from src.tools.macrotool import calc_makros
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.prompt_templates.templates import NUTRITION_AGENT_SYSTEM_PROMPT, NUTRITION_AGENT_INFO_PROMPT, NUTRITION_AGENT_ASK_APPROVAL
from langgraph.types import interrupt, Command

import json


class ImageAgent(Agent):
    LLM_CALL_TOOL_NODE = "ImageAgent_llm_call"
    TOOL_CALL_NODE = "ImageAgent_tool_call"
    SHOW_TOOL_RESULTS_NODE = "ImageAgent_results_node"

    def __init__(self, llm):
        self.llm = llm
        self.conversation = []
        tools = [generate_image]
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm = self.llm.bind_tools(tools)

    def build_graph(self, builder: StateGraph) -> StateGraph:
        builder.add_node(ImageAgent.LLM_CALL_TOOL_NODE, self.llm_call)
        builder.add_node(ImageAgent.TOOL_CALL_NODE, self.tool_node)

        builder.add_node(ImageAgent.SHOW_TOOL_RESULTS_NODE,
                         self.show_response)
      #  builder.add_edge(START, ImageAgent.LLM_CALL_TOOL_NODE)

        return builder

    def tool_node(self, state: dict):
        result = []
        assert len(state["messages"][-1].tool_calls) > 0

        for tool_call in state["messages"][-1].tool_calls:
            tool = self.tools_by_name[tool_call["name"]]

            observation = tool.invoke(tool_call["args"])
            print("TOTAL ", observation)
            result.append(observation)

        return Command(
            update={"messages":  result,
                    "last_node": ImageAgent.TOOL_CALL_NODE,
                    },
            goto=ImageAgent.SHOW_TOOL_RESULTS_NODE,
        )

    def show_response(self, state):
        file_name = state["messages"][-1]

        return Command(
            update={
                "image_name": file_name,
                "last_node": ImageAgent.SHOW_TOOL_RESULTS_NODE,
            },
            goto=RecipeAgent.DECIDE_CONTINUE_NODE
        )

    def llm_call(self, state):
        res = self.llm.invoke(
            [

                HumanMessage(
                    content=IMAGE_AGENT_INFO_PROMPT.format(
                        recipes=state["recipe_final"], request=state["prompt"])
                )
            ]

        )
        return Command(
            update={
                "messages":  [res]
            },
            goto=ImageAgent.TOOL_CALL_NODE,
        )
