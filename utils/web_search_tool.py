import spoonacular as sp
import os
from dotenv import load_dotenv

load_dotenv()

# web search tool
def spoonacular_search(query):
  docs=[]
  api = sp.API(os.getenv("SPOONACULAR_API_KEY"))

  # Step 1: Search for recipes by name
  response = api.search_recipes_complex(query=query, number=2)
  data = response.json()

  if data.get("results"):
    for data in data.get("results"):
      result=""
      # Step 2: Fetch the first recipe's ID
      recipe_id = data["id"]

      # Step 3: Get detailed information about the recipe
      recipe_response = api.get_recipe_information(recipe_id)
      recipe_details = recipe_response.json()

      result += "Recipe Title: " + recipe_details["title"] + "\n"
      result += "\nDescription: " + recipe_details["summary"] + "\n"
      result += "\nIngredients:\n"
      for ingredient in recipe_details["extendedIngredients"]:
          result += f"- {ingredient['amount']} {ingredient['unit']} {ingredient['name']}\n\n"

      result += "\nInstructions:\n\n"
      for step in recipe_details["analyzedInstructions"][0]["steps"]:
          result += f"Step {step['number']}: {step['step']}\n\n"
      docs.append(result)
    return docs
  else:
      return None
