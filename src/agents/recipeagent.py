from langgraph.types import Command
from src.agents.agent import Agent
from langgraph.graph import StateGraph, START, END
from src.prompt_templates.templates import DECISION_TEMPLATE_PROMPT, RECIPE_AGENT_API_CALL_PROMPT, RECIPE_AGENT_SHOW_RESULTS
from src.tools.get_recipes import complex_search_recipes, filter_recipes_after_info, find_recipe_nutrient_match, get_recipe_info
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.messages.ai import AIMessage
from langgraph.types import interrupt, Command
import gradio as gr


class RecipeAgent(Agent):
    SHOW_RESULTS = "RecipeAgent_SHOW_RESULTS"
    CALL_LLM_AND_API = "RecipeAgent_CALL_LLM_AND_API"
    DECIDE_CONTINUE_NODE = "RecipeAgent_DECIDE_CONTINUE_NODE"
    JUST_CHATTING = "RecipeAgent_JUST_CHATTING"

    def __init__(self, llm):
        self.llm = llm
        self.conversation = []
        tools = [complex_search_recipes]
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm = self.llm.bind_tools(tools)
        self.just_chatting_conv = []

    def build_graph(self, builder: StateGraph) -> StateGraph:
        builder.add_node(RecipeAgent.SHOW_RESULTS,
                         self.show_results)
        builder.add_node(RecipeAgent.CALL_LLM_AND_API, self.llm_call_recipe)
        builder.add_node(RecipeAgent.JUST_CHATTING, self.just_chatting)

        builder.add_node(RecipeAgent.DECIDE_CONTINUE_NODE,
                         self.decide_continue)
     #   builder.add_edge(START, RecipeAgent.DECIDE_CONTINUE_NODE)

        return builder

    def just_chatting(self, state: dict):

        if len(self.just_chatting_conv) == 0:
            system = f"{state["extracted"]}" + \
                f"{state["nutrition_text"]}" + f"{state["recipe_final"]}"
            self.just_chatting_conv = [SystemMessage(content=system)]
        self.just_chatting_conv.append(HumanMessage(content=state["prompt"]))

        res = self.llm.invoke(
            self.just_chatting_conv
        )
        print(self.just_chatting_conv)
        print(res.content)
        self.just_chatting_conv.append(AIMessage(content=res.content))

        return Command(
            update={
                "messages": [res.content],
                "last_node": RecipeAgent.JUST_CHATTING,
            },
            goto=RecipeAgent.DECIDE_CONTINUE_NODE)

    def decide_continue(self, state: dict):
        from src.agents.imageagent import ImageAgent
        interrupt_obj = {"last_node": None}
        if state['last_node'] == RecipeAgent.SHOW_RESULTS:
            interrupt_obj = {"llm_msg": state["recipe_final"],
                             "last_node": RecipeAgent.DECIDE_CONTINUE_NODE}
        elif state['last_node'] == RecipeAgent.JUST_CHATTING:
            interrupt_obj = {"llm_msg": state["messages"][-1],
                             "last_node": RecipeAgent.DECIDE_CONTINUE_NODE}
        elif state['last_node'] == ImageAgent.SHOW_TOOL_RESULTS_NODE:
            interrupt_obj = {"image_name": state["image_name"],
                             "last_node": RecipeAgent.DECIDE_CONTINUE_NODE}

        user_prompt = interrupt(
            interrupt_obj
        )
        nodes = [
            {f"{ImageAgent.LLM_CALL_TOOL_NODE}": "If the user wants to see an image of a recipe"},
            {f"{RecipeAgent.JUST_CHATTING}": "If the user wants anything else"}]

        while True:
            res = self.llm.invoke(
                [
                    SystemMessage(
                        content=DECISION_TEMPLATE_PROMPT.format(
                            context=state["recipe_final"], nodes=nodes)
                    ),
                    HumanMessage(
                        content=user_prompt["prompt"]
                    )
                ]
            )
            try:
                answer = self.parse_json(res.content)
                break
            except:
                continue
        print(answer)
        return Command(
            update={
                "prompt": user_prompt["prompt"],
                "last_node": RecipeAgent.DECIDE_CONTINUE_NODE,
            },
            goto=answer["next"]
        )

    def show_results(self, state):
        print(state.keys())

        results = []
        for r in state["final_result"]:
            total = {}
            recipe, serving_size = r
            res = {}
            res["title"] = recipe["title"]
            res["whole_meal_servings"] = recipe["servings"]
            res["pricePerServing"] = recipe["pricePerServing"]
            res["pricePerRecipe"] = recipe["pricePerServing"] * recipe["servings"]
            res["instructions"] = recipe["instructions"]
            res["diets"] = recipe["diets"]
            res["dishTypes"] = recipe["dishTypes"]
            res["extendedIngredients"] = recipe["extendedIngredients"]
            res["summary"] = recipe["summary"]
            res["nutrition"] = recipe["nutrition"]['nutrients']

            for o in res["nutrition"]:
                total[o["name"]] = o["amount"] * serving_size + \
                    (0 if o["name"] not in total.keys() else total[o["name"]])

            res["personal_serving_size"] = serving_size
            res["TOTAL"] = total
            results.append(res)
        res = self.llm.invoke(
            [
                HumanMessage(
                    content=RECIPE_AGENT_SHOW_RESULTS.format(
                        recipe_list=results)
                )
            ]
        )
        return Command(

            update={
                "recipe_final":  res.content,
                "last_node": RecipeAgent.SHOW_RESULTS,

            },
            goto=RecipeAgent.DECIDE_CONTINUE_NODE,
        )

    def llm_call_recipe(self, state):
        print("NOW CALL API")
        print(state["extracted"])
        assert state["nutrition"] != None
        results = []
        for meal in state["nutrition"]:

            res = self.llm.invoke(
                [

                    HumanMessage(
                        content=RECIPE_AGENT_API_CALL_PROMPT.format(
                            nutrition_json=meal, user_json=state["extracted"])
                    )
                ]

            )
            print("CALL API")
            for tool_call in res.tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                print(observation["results"])
                results.append(observation["results"])

        print("*************************************************************************")
        import json
        """with open("results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        with open("recipes.json", "r", encoding="utf-8") as f:
            recipe_infos = json.load(f)"""
        from itertools import chain
        results = list(chain.from_iterable(results))
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        recipe_infos = get_recipe_info(recipes=results)
        with open('recipes.json', 'w', encoding='utf-8') as f:
            json.dump(recipe_infos, f, indent=4)

       # print(list(filter_recipes_after_info(state["extracted"], results, a)))

        filtered_recipes = filter_recipes_after_info(
            state["extracted"], results, recipe_infos)
        results = find_recipe_nutrient_match(
            filtered_recipes, state["nutrition"])

        print(len(results))
        return Command(

            update={
                "final_result":  results,
                "last_node": RecipeAgent.CALL_LLM_AND_API,

            },
            goto=RecipeAgent.SHOW_RESULTS,
        )
