GOAL_EXTRACTION_PROMPT = """
You are a MealPlanner Assistant, that answers very friendly and uses some emojis .

Original Prompt: \"{prompt}\"

Already extracted data (JSON): {extracted_json}

Respond exclusively in JSON format with the following fields:
- extracted: All known attributes about the person so far (age, goal, weight, height, activity level, diet, cooking time, budget, etc.)
- additional_question: A **targeted and relevant** follow-up question that **helps better achieve the goal** without overwhelming the user. If all necessary information is already present, simply return an empty string: \"\".

When extracting and asking follow-up questions, pay special attention to these categories, but ask **only what’s necessary** to enable the next meaningful steps for an appropriate meal plan:
- Physical characteristics - THESE ARE IMPORTANT - (age, gender, weight, height)
- Also important: HOW MANY MEALS PER DAY DO YOU WANT
- Activity level and goal (e.g., muscle gain, weight loss)
- Health (e.g., allergies, medical conditions) — only if relevant
- Dietary preferences or restrictions
- Budget Per Meal - THIS SHOULD ALWAYS BE RECORDED AS AN INTEGER

Objective: Produce as complete yet **user-friendly** a JSON as possible, which can be supplemented in a few meaningful steps if needed—without overwhelming the user with questions.

PREVIOUS CONVERSATION: {conversation}

IT IS VERY IMPORTANT THAT YOU JUST OUTPUT THIS AS A SINGLE JSON OBJECT
"""

NUTRITION_AGENT_SYSTEM_PROMPT = """
You are a tool called \"Macro Nutrition Assistant.\"
You are given a JSON object containing user-specific information (such as age, weight, height, gender, activity level, dietary goal, etc.).

Your task is to use this JSON object to populate all necessary input fields and call the appropriate tools required to calculate the user's daily macronutrient requirements (calories, protein, fat, carbohydrates).

Use the values in the JSON to drive the calculation, and ensure that you call all relevant tools or APIs needed to complete this task based on the data provided.
"""
NUTRITION_AGENT_INFO_PROMPT = """
Here is the extracted JSON object containing the user's personal details and preferences:
{extracted_json}

➡️ Please call your tool `calc_makros` with this JSON as input.

Your task:
1. Use the `calc_macros` tool to calculate the user's macro requirements.
2. Populate all required fields of the tool accordingly using the values in the JSON.
"""
NUTRITION_AGENT_ASK_APPROVAL = """
You are a MealPlanner Assistant, that answers very friendly and uses some emojis .

You are given the output of a tool call that includes the user's **daily** macronutrient recommendations (e.g., calories, protein, fat, carbohydrates), as well as the number of meals the user wishes to eat per day.

Your task is to:

1. Present the provided daily macronutrient stats in a few short, bullet-style sentences. Explain in 1–2 sentences what you did with the data.
2. Supplement the overview with additional health-relevant nutrients (e.g., sodium_mg, fiber_g, cholesterol_limit_mg) that the tool did not provide but are relevant based on the user's profile.
3. Generate **exactly one valid JSON object** with the following two keys:
   - `"conversation_answer"`: a single string that summarizes your output in list format (e.g., each line begins with `•` or `-`).
   - `"nutrition_values"`: a **list** of objects (one per meal), each containing relevant nutrients. The sum of all meals must equal the total daily values provided in the input.

**Important instructions for nutrition_values:**

- Do **not** treat all meals equally. Distribute nutrients realistically across the day using common eating patterns:
  - **Breakfast**: light to moderate (about 20–25% of total daily calories)
  - **Lunch**: the largest meal (about 35–40%)
  - **Dinner**: moderate (about 30–35%)
- You must **respect these percentage ranges closely**. Do **not** simply assign values arbitrarily or allow extreme differences. For example: a distribution where one meal has 1200 kcal and another only 200 kcal is **unacceptable**. This is far too imbalanced and **not practical for a real meal plan**.
- Slight rounding is acceptable, but all meals must stay within a **reasonable range** of their target proportion. The calorie split should reflect **a typical daily rhythm**, not extreme or unrealistic patterns.
- Favor a **higher share of protein** in main meals (especially lunch and dinner), as breakfast tends to be lighter in protein. But keep total portion sizes realistic — no single meal should be "giant."
- Each meal object must include a `"type"` field indicating the kind of meal. Use **only** one of the following valid strings:
  - `"main course"`, `"breakfast"`



Ensure all nutrient values across meals add up exactly to the original daily targets (with acceptable rounding).

**Example output structure:**

```json
{
  "conversation_answer": "...",
  "nutrition_values": [{
    
    "max_calories": 500,
    "min_protein": 60,
    "max_fat": 30,
    "max_carbohydrates": 120,
    
 
  }]
}

PLEASE FOLLOW THE EXACT STRUCTURE FROM ABOVE REGARDING THE JSON OBJECT. YOU HAVE TO OUTPUT IT WITH ```json INFRONT
IT IS VERY IMPORTANT THAT YOU JUST OUTPUT THIS SINGLE JSON OBJECT
"""

RECIPE_AGENT_API_CALL_PROMPT = """
You are given a tool called `complex_search_recipes`, which searches for recipes based on nutritional constraints and dietary filters. You are also provided with a JSON object that contains nutrition-related recommendations and restrictions (e.g., calories, protein_g, fat_g, sodium_mg, fiber_g, foods_to_avoid, etc.).

Your task is to:

1. Analyze the JSON object and extract any available values that match the parameters of the `complex_search_recipes` tool.
2. Fill out the tool call as completely as possible using only the information available in the JSON object.
3. You do NOT need to include parameters that are not specified in the JSON object. It is not necessary to guess or assume missing values.
4. Use reasonable mappings where parameter names differ slightly (e.g., use `maxCalories` if the object gives `calories`, `maxSodium` for `sodium_mg`, `excludeIngredients` for `foods_to_avoid`, etc.).
5. Only call the `complex_search_recipes` tool. Do not generate text or summaries—just the function call with best-matching parameters.

Example JSON input:
```json
{{
  "calories": 1800,
  "protein_g": 100,
  "fat_g": 60,
  "sodium_mg": 1400,
  "fiber_g": 30,
}}

HERE IS THE NUTRION JSON: {nutrition_json}
"""

RECIPE_AGENT_SHOW_RESULTS = """
You are a MealPlanner Assistant, that answers very friendly and uses some emojis. I will provide you with a list of recipes in JSON format. Each recipe contains:

- Title
- Number of servings
- Price per serving
- Dish types
- Diet tags
- Summary
- Instructions
- Ingredients
- Nutrition information
- A calculated serving size based on the user’s macro requirements (provided separately)

🎯 Your task:
For each recipe in the list, please:
1. **Introduce** the recipe with its title and summary.
2. **List** the matching diet types and dish types.
3. **Explain** how to cook the recipe, step by step using the `instructions`.
4. **Show** the total price for the **calculated serving size**, not the default one.
5. **List the ingredients** with their quantities.
6. **Summarize** the nutrition values (like calories, protein, carbs, and fat) for the **calculated serving size** in a **friendly format with emojis**.
7. Keep your tone fun, friendly, and easy to read!

I will provide a list of JSON objects, each describing a recipe. The list is ordered, and each item corresponds to a specific meal in the day

📦 Here's the data:
{recipe_list}

Please go through each recipe and format the output clearly for the user, making it fun and accessible. Use emojis where appropriate (e.g. 🥗 for salad, 🔥 for cooking steps, 💰 for price, 🍽️ for nutrition). Structure each section with clear headers like:

- 📝 Summary
- 🍽️ Dish & Diet Info
- 👨‍🍳 How to Cook
- 💸 Price for Your Serving
- 🧂 Ingredients
- ⚡ Nutrition Info

At the end, provide a total summary of all nutrients and calories which you will also get from the JSON input.
"""


TEST_RECIPES = [{'id': 636589, 'title': 'Butternut Squash Frittata', 'image': 'https://img.spoonacular.com/recipes/636589-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 464.731, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 24.4417, 'unit': 'g'}, {'name': 'Fat', 'amount': 3.98554, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 79.5799, 'unit': 'g'}]}}, {'id': 644044, 'title': 'Protein Strawberry Smoothie', 'image': 'https://img.spoonacular.com/recipes/644044-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 387.73, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 34.1397, 'unit': 'g'}, {'name': 'Fat', 'amount': 3.6687, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 50.8294, 'unit': 'g'}]}}, {'id': 646515, 'title': 'Healthy Southwestern Oatmeal', 'image': 'https://img.spoonacular.com/recipes/646515-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 439.995, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 26.4398, 'unit': 'g'}, {'name': 'Fat', 'amount': 23.331, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 26.5166, 'unit': 'g'}]}}, {'id': 638257, 'title': 'Chicken Porridge', 'image': 'https://img.spoonacular.com/recipes/638257-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 393.05, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 27.7378, 'unit': 'g'}, {'name': 'Fat', 'amount': 6.53238, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 51.3431, 'unit': 'g'}]}}, {'id': 663845, 'title': 'TROPICAL BANANA GREEN SMOOTHIE', 'image': 'https://img.spoonacular.com/recipes/663845-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 214.505, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 28.4501, 'unit': 'g'}, {'name': 'Fat', 'amount': 2.7629, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 18.2178, 'unit': 'g'}]}}, {'id': 652111, 'title': 'Mixed Berry Yogurt with Almonds', 'image': 'https://img.spoonacular.com/recipes/652111-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 335.697, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 26.044, 'unit': 'g'}, {'name': 'Fat', 'amount': 8.0423, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 34.579, 'unit': 'g'}]}}, {'id': 157259, 'title': 'Cocoa Protein Pancakes', 'image': 'https://img.spoonacular.com/recipes/157259-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 410.475, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 25.807, 'unit': 'g'}, {'name': 'Fat', 'amount': 13.7747, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 41.3507, 'unit': 'g'}]}}, {'id': 638825, 'title': 'CHOCOLATE BANANA MORNING BUZZ SMOOTHIE', 'image': 'https://img.spoonacular.com/recipes/638825-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 403.651, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 36.6511, 'unit': 'g'}, {'name': 'Fat', 'amount': 11.7339, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 41.2027, 'unit': 'g'}]}}, {'id': 653472, 'title': 'Oatmeal Pancake (Yummy & Heart Healthy)', 'image': 'https://img.spoonacular.com/recipes/653472-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 583.824, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 25.034, 'unit': 'g'}, {'name': 'Fat', 'amount': 6.22787, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 97.0282, 'unit': 'g'}]}}, {'id': 683130, 'title': 'Chocolate Caramel Sea Salt Smoothie', 'image': 'https://img.spoonacular.com/recipes/683130-312x231.png', 'imageType': 'png', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 437.223, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 25.1619, 'unit': 'g'}, {'name': 'Fat', 'amount': 14.8916, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 58.6471, 'unit': 'g'}]}}, {'id': 660306, 'title': 'Slow Cooker: Pork and Garbanzo Beans', 'image': 'https://img.spoonacular.com/recipes/660306-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 586.781, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 65.7805, 'unit': 'g'}, {'name': 'Fat', 'amount': 14.0409, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 34.4211, 'unit': 'g'}]}}, {'id': 716361, 'title': 'Stir Fried Quinoa, Brown Rice and Chicken Breast', 'image': 'https://img.spoonacular.com/recipes/716361-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 750.018, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 57.7884, 'unit': 'g'}, {'name': 'Fat', 'amount': 19.5283, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 77.6316, 'unit': 'g'}]}}, {'id': 715523, 'title': 'Chorizo and Beef Quinoa Stuffed Pepper', 'image': 'https://img.spoonacular.com/recipes/715523-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 685.038, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 51.1523, 'unit': 'g'}, {'name': 'Fat', 'amount': 37.035, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 27.6868, 'unit': 'g'}]}}, {'id': 664090, 'title': 'Turkish Chicken Salad with Home-made Cacik Yogurt Sauce', 'image': 'https://img.spoonacular.com/recipes/664090-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 642.888, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 67.0766, 'unit': 'g'}, {'name': 'Fat', 'amount': 29.7798, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 20.0745, 'unit': 'g'}]}}, {'id': 661259, 'title': 'Spinach and Gorgonzola Stuffed Flank Steak', 'image': 'https://img.spoonacular.com/recipes/661259-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 523.455, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 46.9998, 'unit': 'g'}, {'name': 'Fat', 'amount': 28.4418, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 15.9889, 'unit': 'g'}]}}, {'id': 1000566, 'title': 'Easy Instant Pot Beef Tips and Rice', 'image': 'https://img.spoonacular.com/recipes/1000566-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 370.729, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 52.7266, 'unit': 'g'}, {'name': 'Fat', 'amount': 10.6038, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 11.988, 'unit': 'g'}]}}, {'id': 631868, 'title': '4 Ingredient Chicken Pot Pie', 'image': 'https://img.spoonacular.com/recipes/631868-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 802.329, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 79.3658, 'unit': 'g'}, {'name': 'Fat', 'amount': 30.2504, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 43.8159, 'unit': 'g'}]}}, {'id': 1046982, 'title': 'How to Make the Perfect Sweet Potato Sloppy Joes', 'image': 'https://img.spoonacular.com/recipes/1046982-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 679.312, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 48.9097, 'unit': 'g'}, {'name': 'Fat', 'amount': 18.0641, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 70.7787, 'unit': 'g'}]}}, {'id': 640321, 'title': 'Crab Stacks', 'image': 'https://img.spoonacular.com/recipes/640321-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 729.841, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 56.411, 'unit': 'g'}, {'name': 'Fat', 'amount': 26.1427, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 58.2989, 'unit': 'g'}]}}, {'id': 640921, 'title': 'Stuffed Artichoke Main Dish', 'image': 'https://img.spoonacular.com/recipes/640921-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 500.04, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 55.6139, 'unit': 'g'}, {'name': 'Fat', 'amount': 8.76446, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 41.2183, 'unit': 'g'}]}}, {
    'id': 715446, 'title': 'Slow Cooker Beef Stew', 'image': 'https://img.spoonacular.com/recipes/715446-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 433.816, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 44.2412, 'unit': 'g'}, {'name': 'Fat', 'amount': 11.6296, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 28.6163, 'unit': 'g'}]}}, {'id': 660306, 'title': 'Slow Cooker: Pork and Garbanzo Beans', 'image': 'https://img.spoonacular.com/recipes/660306-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 586.781, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 65.7805, 'unit': 'g'}, {'name': 'Fat', 'amount': 14.0409, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 34.4211, 'unit': 'g'}]}}, {'id': 715447, 'title': 'Easy Vegetable Beef Soup', 'image': 'https://img.spoonacular.com/recipes/715447-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 565.839, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 45.4263, 'unit': 'g'}, {'name': 'Fat', 'amount': 19.1498, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 43.8948, 'unit': 'g'}]}}, {'id': 716361, 'title': 'Stir Fried Quinoa, Brown Rice and Chicken Breast', 'image': 'https://img.spoonacular.com/recipes/716361-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 750.018, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 57.7884, 'unit': 'g'}, {'name': 'Fat', 'amount': 19.5283, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 77.6316, 'unit': 'g'}]}}, {'id': 646651, 'title': 'Herb chicken with sweet potato mash and sautéed broccoli', 'image': 'https://img.spoonacular.com/recipes/646651-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 709.73, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 46.5086, 'unit': 'g'}, {'name': 'Fat', 'amount': 24.5577, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 65.331, 'unit': 'g'}]}}, {'id': 664090, 'title': 'Turkish Chicken Salad with Home-made Cacik Yogurt Sauce', 'image': 'https://img.spoonacular.com/recipes/664090-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 642.888, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 67.0766, 'unit': 'g'}, {'name': 'Fat', 'amount': 29.7798, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 20.0745, 'unit': 'g'}]}}, {'id': 1044252, 'title': 'Shredded Roast Beef Stuffed Sweet Potatoes (Whole 30 & PALEO)', 'image': 'https://img.spoonacular.com/recipes/1044252-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 386.427, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 42.3042, 'unit': 'g'}, {'name': 'Fat', 'amount': 9.24277, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 31.3876, 'unit': 'g'}]}}, {'id': 639411, 'title': 'Cilantro Lime Halibut', 'image': 'https://img.spoonacular.com/recipes/639411-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 422.055, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 43.5827, 'unit': 'g'}, {'name': 'Fat', 'amount': 21.956, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 5.7786, 'unit': 'g'}]}}, {'id': 661259, 'title': 'Spinach and Gorgonzola Stuffed Flank Steak', 'image': 'https://img.spoonacular.com/recipes/661259-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 523.455, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 46.9998, 'unit': 'g'}, {'name': 'Fat', 'amount': 28.4418, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 15.9889, 'unit': 'g'}]}}, {'id': 1000566, 'title': 'Easy Instant Pot Beef Tips and Rice', 'image': 'https://img.spoonacular.com/recipes/1000566-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 370.729, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 52.7266, 'unit': 'g'}, {'name': 'Fat', 'amount': 10.6038, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 11.988, 'unit': 'g'}]}}, {'id': 782601, 'title': 'Red Kidney Bean Jambalaya', 'image': 'https://img.spoonacular.com/recipes/782601-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 392.803, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 18.1297, 'unit': 'g'}, {'name': 'Fat', 'amount': 6.45348, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 53.1092, 'unit': 'g'}]}}, {'id': 664147, 'title': 'Tuscan White Bean Soup with Olive Oil and Rosemary', 'image': 'https://img.spoonacular.com/recipes/664147-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 242.405, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 16.1338, 'unit': 'g'}, {'name': 'Fat', 'amount': 1.29326, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 32.7079, 'unit': 'g'}]}}, {'id': 646043, 'title': 'Gujarati Dry Mung Bean Curry', 'image': 'https://img.spoonacular.com/recipes/646043-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 375.585, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 19.8333, 'unit': 'g'}, {'name': 'Fat', 'amount': 5.14869, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 52.0656, 'unit': 'g'}]}}, {'id': 652393, 'title': 'Moosewood Lentil Soup', 'image': 'https://img.spoonacular.com/recipes/652393-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 396.326, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 25.6476, 'unit': 'g'}, {'name': 'Fat', 'amount': 3.55166, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 35.1691, 'unit': 'g'}]}}, {'id': 715391, 'title': 'Slow Cooker Chicken Taco Soup', 'image': 'https://img.spoonacular.com/recipes/715391-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 311.769, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 24.3302, 'unit': 'g'}, {'name': 'Fat', 'amount': 3.78036, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 37.0715, 'unit': 'g'}]}}, {'id': 632718, 'title': 'Armenian Stew', 'image': 'https://img.spoonacular.com/recipes/632718-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 327.843, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 16.0288, 'unit': 'g'}, {'name': 'Fat', 'amount': 2.5247, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 45.0459, 'unit': 'g'}]}}, {'id': 715392, 'title': 'Easy Slow Cooker Chicken Tortilla Soup', 'image': 'https://img.spoonacular.com/recipes/715392-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 282.76, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 32.402, 'unit': 'g'}, {'name': 'Fat', 'amount': 4.41672, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 21.8461, 'unit': 'g'}]}}, {'id': 649946, 'title': 'Lentil, Sweet Potato and Spinach Soup', 'image': 'https://img.spoonacular.com/recipes/649946-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 303.722, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 19.5204, 'unit': 'g'}, {'name': 'Fat', 'amount': 1.11348, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 31.7063, 'unit': 'g'}]}}, {'id': 13073, 'title': 'Seared Ahi Tuna Salad', 'image': 'https://img.spoonacular.com/recipes/13073-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 356.921, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 17.0855, 'unit': 'g'}, {'name': 'Fat', 'amount': 3.23904, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 55.1827, 'unit': 'g'}]}}, {'id': 646185, 'title': 'Ham and Red Bean Soup', 'image': 'https://img.spoonacular.com/recipes/646185-312x231.jpg', 'imageType': 'jpg', 'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 236.484, 'unit': 'kcal'}, {'name': 'Protein', 'amount': 18.6539, 'unit': 'g'}, {'name': 'Fat', 'amount': 5.8827, 'unit': 'g'}, {'name': 'Carbohydrates', 'amount': 20.386, 'unit': 'g'}]}}]
