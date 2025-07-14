from typing import Optional, List, Union, Dict, Any
from pathlib import Path
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

import os
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("SPOONACULAR_API_KEY")
if not API_KEY:
    raise RuntimeError("Bitte setze SPOONACULAR_API_KEY in deiner .env-Datei")


@tool
def complex_search_recipes(
    # Full‐text and classification
    query:              Optional[str] = None,
    cuisine:            Optional[str] = None,
    excludeCuisine:     Optional[str] = None,
    diet:               Optional[str] = None,
    intolerances:       Optional[str] = None,
    equipment:          Optional[str] = None,
    includeIngredients: Optional[str] = None,
    excludeIngredients: Optional[str] = None,
    type:               Optional[str] = None,
    # Recipe metadata flags
    instructionsRequired:  Optional[bool] = None,
    fillIngredients:       Optional[bool] = None,
    addRecipeInformation:  Optional[bool] = None,
    addRecipeInstructions: Optional[bool] = None,
    addRecipeNutrition:    Optional[bool] = None,
    author:                Optional[str] = None,
    tags:                  Optional[str] = None,
    recipeBoxId:           Optional[int] = None,
    titleMatch:            Optional[str] = None,
    maxReadyTime:          Optional[int] = None,
    minServings:           Optional[int] = None,
    maxServings:           Optional[int] = None,
    ignorePantry:          Optional[bool] = None,
    sort:                  Optional[str] = None,
    sortDirection:         Optional[str] = None,
    # Macronutrient filters
    minCarbs:    Optional[float] = None,
    maxCarbs:    Optional[float] = None,
    minProtein:  Optional[float] = None,
    maxProtein:  Optional[float] = None,
    minFat:      Optional[float] = None,
    maxFat:      Optional[float] = None,
    minCalories: Optional[float] = None,
    maxCalories: Optional[float] = None,
    # Micronutrient filters
    minAlcohol:     Optional[float] = None,
    maxAlcohol:     Optional[float] = None,
    minCaffeine:    Optional[float] = None,
    maxCaffeine:    Optional[float] = None,
    minCopper:      Optional[float] = None,
    maxCopper:      Optional[float] = None,
    minCalcium:     Optional[float] = None,
    maxCalcium:     Optional[float] = None,
    minCholine:     Optional[float] = None,
    maxCholine:     Optional[float] = None,
    minCholesterol: Optional[float] = None,
    maxCholesterol: Optional[float] = None,
    minFluoride:    Optional[float] = None,
    maxFluoride:    Optional[float] = None,
    minSaturatedFat: Optional[float] = None,
    maxSaturatedFat: Optional[float] = None,
    minVitaminA:    Optional[float] = None,
    maxVitaminA:    Optional[float] = None,
    minVitaminC:    Optional[float] = None,
    maxVitaminC:    Optional[float] = None,
    minVitaminD:    Optional[float] = None,
    maxVitaminD:    Optional[float] = None,
    minVitaminE:    Optional[float] = None,
    maxVitaminE:    Optional[float] = None,
    minVitaminK:    Optional[float] = None,
    maxVitaminK:    Optional[float] = None,
    minVitaminB1:   Optional[float] = None,
    maxVitaminB1:   Optional[float] = None,
    minVitaminB2:   Optional[float] = None,
    maxVitaminB2:   Optional[float] = None,
    minVitaminB5:   Optional[float] = None,
    maxVitaminB5:   Optional[float] = None,
    minVitaminB3:   Optional[float] = None,
    maxVitaminB3:   Optional[float] = None,
    minVitaminB6:   Optional[float] = None,
    maxVitaminB6:   Optional[float] = None,
    minVitaminB12:  Optional[float] = None,
    maxVitaminB12:  Optional[float] = None,
    minFiber:       Optional[float] = None,
    maxFiber:       Optional[float] = None,
    minFolate:      Optional[float] = None,
    maxFolate:      Optional[float] = None,
    minFolicAcid:   Optional[float] = None,
    maxFolicAcid:   Optional[float] = None,
    minIodine:      Optional[float] = None,
    maxIodine:      Optional[float] = None,
    minIron:        Optional[float] = None,
    maxIron:        Optional[float] = None,
    minMagnesium:   Optional[float] = None,
    maxMagnesium:   Optional[float] = None,
    minManganese:   Optional[float] = None,
    maxManganese:   Optional[float] = None,
    minPhosphorus:  Optional[float] = None,
    maxPhosphorus:  Optional[float] = None,
    minPotassium:   Optional[float] = None,
    maxPotassium:   Optional[float] = None,
    minSelenium:    Optional[float] = None,
    maxSelenium:    Optional[float] = None,
    minSodium:      Optional[float] = None,
    maxSodium:      Optional[float] = None,
    minSugar:       Optional[float] = None,
    maxSugar:       Optional[float] = None,
    minZinc:        Optional[float] = None,
    maxZinc:        Optional[float] = None,
    # Pagination & randomness
    offset:         int = 0,
    number:         int = 10,
    random:         bool = False
) -> Dict[str, Any]:
    """
    Calls Spoonacular’s complexSearch with all supported filters.
    Returns parsed JSON.
    """
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Please set your SPOONACULAR_API_KEY environment variable.")

    url = "https://api.spoonacular.com/recipes/complexSearch"
    params: Dict[str, Union[str, int, bool]] = {"apiKey": api_key}

    delta = 1/3
    for k, v in locals().items():
        if k in ("api_key", "url") or v is None:
            continue
        params[k] = str(v).lower() if isinstance(v, bool) else v
        if k.startswith("min"):
            params[k] = params[k]*(1-delta)
        elif k.startswith("max"):
            params[k] = params[k]*(1+delta)

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_recipe_info(recipes):
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Please set your SPOONACULAR_API_KEY environment variable.")

    url = "https://api.spoonacular.com/recipes/informationBulk"
    ids = ",".join([f"{r['id']}" for r in recipes])
    params: Dict[str, Union[str, int, bool]] = {"apiKey": api_key, "ids": ids}

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def filter_recipes_after_info(extraced_prefs, recipes_nutriens, recipes_info):
    def filter_recipes(recipe):
        if recipe["readyInMinutes"] > 45:
            return False
        if (recipe["pricePerServing"] * recipe["servings"])/100 > extraced_prefs["budget_per_meal"]*1.15:
            return False
        return True

    def add_nutriens(recipe):
        r_nutriens = list(filter(
            lambda r_n: r_n["id"] == recipe["id"], recipes_nutriens))[0]
        recipe["nutrition"] = r_nutriens["nutrition"]
        return recipe
    return list(map(add_nutriens, filter(filter_recipes, recipes_info)))


def find_recipe_nutrient_match(recipes, nutrion_target):

    def find_best_fit(candiates, meal_nutrition):
        serving_sizes = [1, 1.5, 2, 2.5, 3]

        best_fit = 2**31
        best_candiate = None
        best_serving_size = None
        for serving_size in serving_sizes:
            for candiate in candiates:
                sum_ = 0
                for macro in candiate["nutrition"]['nutrients']:
                    macro_name = macro["name"].lower()
                    macro_name = f"min_{macro_name}" if f"min_{macro_name}" in meal_nutrition.keys(
                    ) else f"max_{macro_name}"

                    sum_ += (serving_size *
                             macro["amount"] - meal_nutrition[macro_name])**2
                if sum_ < best_fit:
                    best_fit = sum_
                    best_candiate = candiate
                    best_serving_size = serving_size

        return best_candiate, best_serving_size

    results = []
    for meal_nutrition_target in nutrion_target:
        candiates = list(
            filter(
                lambda r: meal_nutrition_target["type"] in r["dishTypes"], recipes))

        print(meal_nutrition_target["type"], len(candiates))
        best_fit = find_best_fit(candiates, meal_nutrition_target)

        recipes = list(filter(lambda r: r["id"] != best_fit[0]["id"], recipes))
        results.append(best_fit)

    return results
