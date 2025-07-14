from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError
from src.agents.agent import Agent
from src.agents.recipeagent import RecipeAgent
from src.prompt_templates.templates import GOAL_EXTRACTION_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from src.tools.macrotool import calc_makros
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.prompt_templates.templates import NUTRITION_AGENT_SYSTEM_PROMPT, NUTRITION_AGENT_INFO_PROMPT, NUTRITION_AGENT_ASK_APPROVAL
from langgraph.types import Command

import json


class NutritionAgent(Agent):
    LLM_CALL_TOOL_NODE = "llm_call"
    TOOL_CALL_NODE = "tool_call"
    SHOW_TOOL_RESULTS_NODE = "results_node"

    def __init__(self, llm):
        self.llm = llm
        self.conversation = []
        tools = [calc_makros]
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm = self.llm.bind_tools(tools)

    def build_graph(self, builder: StateGraph) -> StateGraph:
        builder.add_node(NutritionAgent.LLM_CALL_TOOL_NODE, self.llm_call)
        builder.add_node(NutritionAgent.TOOL_CALL_NODE, self.tool_node)
        builder.add_node(NutritionAgent.SHOW_TOOL_RESULTS_NODE,
                         self.show_response)
#
        return builder

    def tool_node(self, state: dict):
      #  raise Exception()
        result = []
        assert len(state["messages"][-1].tool_calls) > 0

        for tool_call in state["messages"][-1].tool_calls:
            tool = self.tools_by_name[tool_call["name"]]

            observation = tool.invoke(tool_call["args"])
            print("TOTAL ", observation)
            result.append(ToolMessage(content=observation,
                          tool_call_id=tool_call["id"]))

       # print("####", result)
        return Command(
            update={"messages":  result,
                    "last_node": NutritionAgent.TOOL_CALL_NODE,
                    },
            goto=NutritionAgent.SHOW_TOOL_RESULTS_NODE,
        )

    def show_response(self, state):
        new_messages = [HumanMessage(content=str(state["extracted"]))] + state["messages"] + [HumanMessage(
            content=NUTRITION_AGENT_ASK_APPROVAL
        )]
        msg = HumanMessage(content="\n".join(
            [m.content for m in new_messages]))
        # print(msg)
        res = self.llm.invoke(
            [msg]
        )
       # print("---", msg)
       # print("---", res.content)
       # print(res.content)
        answer = self.parse_json(res.content)

        # print("\n🤖", answer["conversation_answer"])
        print("\n🤖", answer["nutrition_values"])
        return Command(
            update={
                "nutrition":  answer["nutrition_values"],
                "nutrition_text": answer["conversation_answer"],
                "last_node": NutritionAgent.SHOW_TOOL_RESULTS_NODE,
            },
            goto=RecipeAgent.CALL_LLM_AND_API,
        )

    def llm_call(self, state):
        res = self.llm.invoke(
            [
                SystemMessage(
                    content=NUTRITION_AGENT_SYSTEM_PROMPT
                ),
                HumanMessage(
                    content=NUTRITION_AGENT_INFO_PROMPT.format(
                        extracted_json=state["extracted"])
                )
            ]

        )
        return Command(
            update={
                "messages":  [res]
            },
            goto=NutritionAgent.TOOL_CALL_NODE,
        )
