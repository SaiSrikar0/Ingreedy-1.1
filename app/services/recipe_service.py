import json
import logging
from typing import List, Optional
import requests
from app.config.settings import Settings
from app.models.recipe import Recipe

logger = logging.getLogger(__name__)

class RecipeService:
    """Service for handling recipe operations"""
    
    def __init__(self):
        self.settings = Settings()
        self.base_url = "https://api.spoonacular.com/recipes"
        self.api_key = self.settings.SPOONACULAR_API_KEY
        
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make request to Spoonacular API"""
        params["apiKey"] = self.api_key
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Spoonacular API: {e}")
            return {}
    
    def search_by_ingredients(self, ingredients: List[str], number: int = 5) -> List[Recipe]:
        """Search recipes by ingredients"""
        params = {
            "ingredients": ",".join(ingredients),
            "number": number,
            "ranking": 1  # Maximize used ingredients
        }
        
        data = self._make_request("findByIngredients", params)
        recipes = []
        
        for recipe_data in data:
            # Get detailed recipe information
            details = self._make_request(f"{recipe_data['id']}/information", {})
            if details:
                recipe = Recipe(
                    title=details["title"],
                    ingredients=[ing["original"] for ing in details["extendedIngredients"]],
                    instructions=[step["step"] for step in details["analyzedInstructions"][0]["steps"]],
                    cooking_time=details.get("readyInMinutes"),
                    servings=details.get("servings"),
                    source_url=details.get("sourceUrl"),
                    image_url=details.get("image"),
                    is_indian=self._is_indian_recipe(details),
                    source="spoonacular"
                )
                recipes.append(recipe)
        
        return recipes
    
    def _is_indian_recipe(self, recipe_data: dict) -> bool:
        """Check if recipe is Indian cuisine"""
        if not recipe_data.get("cuisines"):
            return False
            
        indian_keywords = ["indian", "south asian", "north indian", "south indian"]
        return any(keyword in cuisine.lower() for cuisine in recipe_data["cuisines"] 
                  for keyword in indian_keywords)
    
    def get_random_recipes(self, number: int = 3) -> List[Recipe]:
        """Get random recipes"""
        params = {
            "number": number,
            "tags": "vegetarian"  # Optional: add more tags as needed
        }
        
        data = self._make_request("random", params)
        recipes = []
        
        for recipe_data in data.get("recipes", []):
            recipe = Recipe(
                title=recipe_data["title"],
                ingredients=[ing["original"] for ing in recipe_data["extendedIngredients"]],
                instructions=[step["step"] for step in recipe_data["analyzedInstructions"][0]["steps"]],
                cooking_time=recipe_data.get("readyInMinutes"),
                servings=recipe_data.get("servings"),
                source_url=recipe_data.get("sourceUrl"),
                image_url=recipe_data.get("image"),
                is_indian=self._is_indian_recipe(recipe_data),
                source="spoonacular"
            )
            recipes.append(recipe)
        
        return recipes 