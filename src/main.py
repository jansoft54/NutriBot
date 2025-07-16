

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
    recipe_final: str
    image_name: str


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
builder = StateGraph(State)
agents = [GoalsAgent(llm), NutritionAgent(
    llm), RecipeAgent(llm), ImageAgent(llm)]
for agent in agents:
    builder = agent.build_graph(builder)
memory = MemorySaver()
graph = builder.compile(checkpointer=memory,
                        )
config = {"configurable": {"thread_id": "gradio_session"}}
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
            "extracted": {},
            "additional_question": "",
            "messages": [],
            "nutrition": {},
            "final_result": [],
            "last_node": None,
            "nutrition_text": "",
            "image_name": "",
            "recipe_final": "Hey there, food adventurer! 🌟 I'm super excited to share these amazing recipes tailored just for you! Let's dive into your delicious meal plan! 🥳\n\n***\n\n### 1. Chocolate Caramel Sea Salt Smoothie 🍫🧂🥤\n\n📝 **Summary**\nGet ready for a treat! This Chocolate Caramel Sea Salt Smoothie is a fantastic way to kick off your day. It's a quick blend that packs a punch, perfect for a busy morning! It usually takes about 45 minutes from start to finish, but for a smoothie, that's mostly chilling time! 😉\n\n🍽️ **Dish & Diet Info**\nThis yummy smoothie is:\n*   **Diet Types**: Gluten-Free, Lacto Ovo Vegetarian 🌱\n*   **Dish Types**: Morning Meal, Brunch, Beverage, Breakfast, Drink ☀️\n\n👨\u200d🍳 **How to Cook**\nOopsie! Looks like the step-by-step instructions for this smoothie weren't provided, but don't worry, smoothies are usually super simple! Just blend all the ingredients until smooth and enjoy! 🌪️\n\n💸 **Price for Your Serving**\nFor your calculated serving size (1.5 servings), this delightful smoothie will cost approximately **$2.71**! 💰\n\n🧂 **Ingredients (for 1.5 servings)**\nHere's what you'll need:\n*   1 cup plain Greek yogurt\n*   1 cup milk\n*   7.5 small pitted dates\n*   0.75 frozen banana\n*   1.5 Tablespoons cocoa\n*   1.5 scoop Barlean's Chocolate Silk Greens\n*   1.5 Tablespoon peanut butter\n*   1.5 pinch of sea salt\n*   1.5 handful of ice\n\n⚡ **Nutrition Info (for 1.5 servings)**\nFueling your day with this smoothie means:\n*   **Calories**: 655.83 kcal 🔥\n*   **Protein**: 37.74 g 💪\n*   **Fat**: 22.34 g 🥑\n*   **Carbohydrates**: 87.97 g 🍞\n\n***\n\n### 2. Stir Fried Quinoa, Brown Rice and Chicken Breast 🍚🍗🌶️\n\n📝 **Summary**\nLooking for a satisfying main course? This Stir Fried Quinoa, Brown Rice and Chicken Breast is a winner! It's hearty, flavorful, and a great option for lunch or dinner. It takes about 45 minutes to get this deliciousness on your plate! 😋\n\n🍽️ **Dish & Diet Info**\nThis amazing stir-fry is:\n*   **Diet Types**: Gluten-Free 🌱\n*   **Dish Types**: Lunch, Main Course, Main Dish, Dinner 🍽️\n\n👨\u200d🍳 **How to Cook**\nLet's get cooking! 🔥\n1.  In a bowl, season your chicken breast with seasoning cubes and suya spice. Let it marinate for 2 hours (or if you're super hungry, cook it right away!).\n2.  In a pot with 1 cup of boiling water, add your quinoa mix and a teaspoon of oil. Boil until soft (about 5-7 minutes). Pour into a bowl and set aside.\n3.  Heat up melted butter in a pan. Pan-fry the chicken breast on medium heat, flipping it constantly until it browns on both sides. Reduce the heat, cover the pan, and let the chicken cook through. If the pan gets too dry, add 2 tablespoons of water.\n4.  Stir in the chopped vegetables into the pan with the frying chicken.\n5.  Finally, add the quinoa/brown rice mix.\n6.  Serve hot! Enjoy! 🎉\n\n💸 **Price for Your Serving**\nFor your calculated serving size (1.5 servings), this tasty meal will cost approximately **$5.37**! 💰\n\n🧂 **Ingredients (for 1.5 servings)**\nHere's what you'll need:\n*   1.5 teaspoon of suya spice or Yaji (optional)\n*   0.75 cup of quinoa and brown rice mix\n*   2.25 teaspoon of melted butter\n*   1.5 handful of chopped carrots\n*   6 whole cherry tomatoes (optional)\n*   1.5 chicken breast (Thinly sliced)\n*   3 cloves of garlic\n*   1.5 serving Seasoning cubes\n*   1.5 handful of chopped green pepper\n*   1.5 medium roma tomato\n*   1.5 scotch bonnet pepper (ata rodo)\n*   1.5 chopped spring onion\n*   1.5 teaspoon of vegetable oil\n*   1.5 cup water\n\n⚡ **Nutrition Info (for 1.5 servings)**\nThis power-packed meal provides:\n*   **Calories**: 1125.03 kcal 🔥\n*   **Protein**: 86.68 g 💪\n*   **Fat**: 29.29 g 🥑\n*   **Carbohydrates**: 116.45 g 🍞\n\n***\n\n### 3. Butternut Squash Frittata 🍳🎃🧀\n\n📝 **Summary**\nSay hello to the Butternut Squash Frittata! This dish is not only delicious but also super easy to make, ready in about 45 minutes. It's a fantastic main course that's sure to impress! 🌟\n\n🍽️ **Dish & Diet Info**\nThis delightful frittata is:\n*   **Diet Types**: Gluten-Free 🌱\n*   **Dish Types**: Lunch, Main Course, Morning Meal, Brunch, Main Dish, Breakfast, Dinner ☀️🍽️\n\n👨\u200d🍳 **How to Cook**\nLet's whip up this frittata! 🔥\n1.  Preheat your oven to 350°F (175°C).\n2.  Spray a 10 oz oven-safe dish with cooking spray.\n3.  Add your butternut squash to the dish.\n4.  In a measuring cup, combine your eggs and milk. Mix until well combined, then pour over the butternut squash.\n5.  Sprinkle with pepper and top with cheese.\n6.  Bake in the oven for 30-35 minutes, or until the middle is slightly firm.\n7.  Let it cool for a few minutes before serving. Enjoy! 🥰\n\n💸 **Price for Your Serving**\nFor your calculated serving size (2 servings), this yummy frittata will cost approximately **$6.81**! 💰\n\n🧂 **Ingredients (for 2 servings)**\nHere's what you'll need:\n*   2 large butternut squash, peeled, seeded, thinly sliced (with a mandoline)\n*   1 oz goat cheese\n*   1 cup liquid egg substitute\n*   4 tbsp. non-fat milk\n*   2 serving Pepper to taste\n\n⚡ **Nutrition Info (for 2 servings)**\nThis wholesome frittata offers:\n*   **Calories**: 929.46 kcal 🔥\n*   **Protein**: 48.88 g 💪\n*   **Fat**: 7.97 g 🥑\n*   **Carbohydrates**: 159.16 g 🍞\n\n***\n\n### 4. Tuscan White Bean Soup with Olive Oil and Rosemary 🥣🌿🫒\n\n📝 **Summary**\nWarm up with this comforting Tuscan White Bean Soup! It's a fantastic, wholesome soup that's perfect for any time of day, especially on a chilly evening. This recipe is a true crowd-pleaser and takes about 45 minutes to prepare! 🍲\n\n🍽️ **Dish & Diet Info**\nThis hearty soup is:\n*   **Diet Types**: Gluten-Free, Dairy-Free, Lacto Ovo Vegetarian, Vegan 🌱💚\n*   **Dish Types**: Lunch, Soup, Main Course, Main Dish, Dinner 🥣🍽️\n\n👨\u200d🍳 **How to Cook**\nLet's make some soup! 🔥\n1.  Rinse the beans thoroughly and place them in a 7-quart slow cooker along with the water, onion, garlic, and bay leaf. Cover and cook on LOW for about 8 hours, or until the beans are nice and tender.\n2.  Remove the bay leaf. Using a handheld immersion blender, puree the remaining ingredients to your desired texture. Add salt to taste.\n3.  Ladle the soup into bowls. Drizzle with olive oil, sprinkle with rosemary, and serve. Bon appétit! 😋\n\n💸 **Price for Your Serving**\nFor your calculated serving size (1 serving), this comforting soup will cost approximately **$0.50**! 💰\n\n🧂 **Ingredients (for 1 serving)**\nHere's what you'll need:\n*   1 bay leaf\n*   1 tablespoon chopped fresh rosemary\n*   6 cloves garlic\n*   1 teaspoon olive oil\n*   1 medium onion, chopped\n*   6 servings Salt\n*   2 tablespoons water\n*   2 cups dried white beans, such as great northern or cannellini\n\n⚡ **Nutrition Info (for 1 serving)**\nThis nourishing soup provides:\n*   **Calories**: 242.41 kcal 🔥\n*   **Protein**: 16.13 g 💪\n*   **Fat**: 1.29 g 🥑\n*   **Carbohydrates**: 32.71 g 🍞\n\n***\n\n### ✨ Your Daily Meal Plan Nutrition Summary ✨\n\nHere's the grand total for all your fantastic meals today! 🥳\n\n*   **Total Calories**: 2952.73 kcal 🔥\n*   **Total Protein**: 189.44 g 💪\n*   **Total Fat**: 60.89 g 🥑\n*   **Total Carbohydrates**: 396.29 g 🍞\n\nHope you enjoy these delicious recipes! Is there any recipe you'd like a realistic-looking image of? Just let me know! 📸"

        }
        state = graph.invoke(start_state, config)
        interrupt_obj = state["__interrupt__"][0].value

    # 2) Inspect result.next to see which node just ran
    node = interrupt_obj["last_node"]
    print(state["extracted"])
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
