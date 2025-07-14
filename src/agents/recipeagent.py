from langgraph.types import Command
from src.agents.agent import Agent
from langgraph.graph import StateGraph, START, END
from src.prompt_templates.templates import RECIPE_AGENT_API_CALL_PROMPT, RECIPE_AGENT_SHOW_RESULTS, TEST_RECIPES
from src.tools.get_recipes import complex_search_recipes, filter_recipes_after_info, find_recipe_nutrient_match, get_recipe_info
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage


class RecipeAgent(Agent):
    SHOW_RESULTS = "RecipeAgent_SHOW_RESULTS"
    CALL_LLM_AND_API = "RecipeAgent_CALL_LLM_AND_API"

    def __init__(self, llm):
        self.llm = llm
        self.conversation = []
        tools = [complex_search_recipes]
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm = self.llm.bind_tools(tools)

    def build_graph(self, builder: StateGraph) -> StateGraph:
        builder.add_node(RecipeAgent.SHOW_RESULTS,
                         self.show_results)
        builder.add_node(RecipeAgent.CALL_LLM_AND_API, self.llm_call_recipe)
       # builder.add_edge(START, RecipeAgent.CALL_LLM_AND_API)

        return builder

    def show_results(self, state):
        print(state.keys())
        assert len(state["final_result"]
                   ) == state["extracted"]["meals_per_day"]
        results = []
        for r in state["final_result"]:
            total = {}
            recipe, serving_size = r
            res = {}
            res["title"] = recipe["title"]
            res["servings"] = recipe["servings"]
            res["pricePerServing"] = recipe["pricePerServing"]
            res["instructions"] = recipe["instructions"]
            res["diets"] = recipe["diets"]
            res["diets"] = recipe["diets"]
            res["dishTypes"] = recipe["dishTypes"]
            res["extendedIngredients"] = recipe["extendedIngredients"]
            res["summary"] = recipe["summary"]
            res["nutrition"] = recipe["nutrition"]['nutrients']

            for o in res["nutrition"]:
                total[o["name"]] = o["amount"] * serving_size + \
                    (0 if o["name"] not in total.keys() else total[o["name"]])

            res["serving_size"] = serving_size
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
        print(res)

    def llm_call_recipe(self, state):

        assert state["nutrition"] != None
        results = TEST_RECIPES
        """for meal in state["nutrition"]:
            res = self.llm.invoke(
                [

                    HumanMessage(
                        content=RECIPE_AGENT_API_CALL_PROMPT.format(
                            nutrition_json=meal)
                    )
                ]

            )
            print("CALL API")
            for tool_call in res.tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                results.append(observation["results"])

        print("*************************************************************************")

        from itertools import chain
        results = list(chain.from_iterable(results))
        """
        print("*************************************************************************")
        import json
        with open("recipes.json", "r", encoding="utf-8") as f:
            a = json.load(f)
       # print(list(filter_recipes_after_info(state["extracted"], results, a)))
        b = filter_recipes_after_info(state["extracted"], TEST_RECIPES, a)
        results = find_recipe_nutrient_match(b, state["nutrition"])
        print(len(results))
        return Command(

            update={
                "final_result":  results,
                "last_node": RecipeAgent.CALL_LLM_AND_API,

            },
            goto=RecipeAgent.SHOW_RESULTS,
        )
