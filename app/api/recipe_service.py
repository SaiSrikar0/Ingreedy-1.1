import os
import json
import random
import httpx
import pandas as pd
from typing import List, Dict, Any, Optional

class RecipeService:
    """Service to fetch and manage recipe data from Spoonacular API"""
    
    def __init__(self):
        """Initialize the recipe service with API key and data"""
        self.api_key = os.getenv("SPOONACULAR_API_KEY", "")
        self.api_base_url = "https://api.spoonacular.com"
        self.recipes_data_path = "app/data/recipes.json"
        self.recipes_df = None
        
        # Load recipes data if available or fetch from API
        self._load_or_fetch_recipes()
    
    def _load_or_fetch_recipes(self):
        """Load recipes from local file or fetch from API if not available"""
        try:
            if os.path.exists(self.recipes_data_path):
                with open(self.recipes_data_path, 'r') as f:
                    recipes = json.load(f)
                self.recipes_df = pd.DataFrame(recipes)
                print(f"Loaded {len(recipes)} recipes from local file")
            else:
                # If no local data, we'll fetch when needed
                self.recipes_df = pd.DataFrame([])
        except Exception as e:
            print(f"Error loading recipes: {e}")
            self.recipes_df = pd.DataFrame([])
    
    async def _save_recipes(self, recipes: List[Dict[str, Any]]):
        """Save recipes to local file"""
        try:
            os.makedirs(os.path.dirname(self.recipes_data_path), exist_ok=True)
            with open(self.recipes_data_path, 'w') as f:
                json.dump(recipes, f)
            print(f"Saved {len(recipes)} recipes to local file")
        except Exception as e:
            print(f"Error saving recipes: {e}")
    
    async def get_random_recipes(self, number: int = 10) -> List[Dict[str, Any]]:
        """Get random recipes from the API or local data"""
        if not self.recipes_df.empty and len(self.recipes_df) >= number:
            # Return random recipes from local data
            random_recipes = self.recipes_df.sample(number).to_dict('records')
            return random_recipes
        
        # Fetch from API if no local data or not enough recipes
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "apiKey": self.api_key,
                    "number": number,
                    "limitLicense": True,
                }
                response = await client.get(f"{self.api_base_url}/recipes/random", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    recipes = data.get("recipes", [])
                    
                    # Process recipes to extract essential data
                    processed_recipes = []
                    for recipe in recipes:
                        processed_recipe = {
                            "id": recipe.get("id"),
                            "title": recipe.get("title"),
                            "image": recipe.get("image"),
                            "readyInMinutes": recipe.get("readyInMinutes"),
                            "servings": recipe.get("servings"),
                            "sourceUrl": recipe.get("sourceUrl"),
                            "summary": recipe.get("summary"),
                            "ingredients": [
                                {
                                    "name": ingredient.get("name", ""),
                                    "amount": ingredient.get("amount", 0),
                                    "unit": ingredient.get("unit", "")
                                }
                                for ingredient in recipe.get("extendedIngredients", [])
                            ],
                            "instructions": recipe.get("instructions", "")
                        }
                        processed_recipes.append(processed_recipe)
                    
                    # Update local data with new recipes
                    if not self.recipes_df.empty:
                        new_df = pd.DataFrame(processed_recipes)
                        self.recipes_df = pd.concat([self.recipes_df, new_df]).drop_duplicates(subset=['id'])
                    else:
                        self.recipes_df = pd.DataFrame(processed_recipes)
                    
                    # Save updated data
                    await self._save_recipes(self.recipes_df.to_dict('records'))
                    
                    return processed_recipes
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    
                    # If API fails, try to return from local data even if fewer than requested
                    if not self.recipes_df.empty:
                        sample_size = min(number, len(self.recipes_df))
                        return self.recipes_df.sample(sample_size).to_dict('records')
                    return []
        except Exception as e:
            print(f"Error fetching recipes: {e}")
            # Fallback to local data
            if not self.recipes_df.empty:
                sample_size = min(number, len(self.recipes_df))
                return self.recipes_df.sample(sample_size).to_dict('records')
            return []
    
    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        """Search recipes by name or ingredients"""
        try:
            # Check if we have recipes locally first
            if not self.recipes_df.empty:
                # Simple local search on title or ingredients
                filtered_recipes = self.recipes_df[
                    self.recipes_df['title'].str.contains(query, case=False, na=False) | 
                    self.recipes_df['ingredients'].apply(
                        lambda ingredients: any(query.lower() in str(ingredient).lower() for ingredient in ingredients)
                    )
                ]
                
                if not filtered_recipes.empty:
                    return filtered_recipes.to_dict('records')
            
            # Search via API if no local results
            async with httpx.AsyncClient() as client:
                params = {
                    "apiKey": self.api_key,
                    "query": query,
                    "number": 10,
                    "instructionsRequired": True,
                }
                response = await client.get(f"{self.api_base_url}/recipes/complexSearch", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    recipes = data.get("results", [])
                    
                    # Fetch full recipe details for each search result
                    full_recipes = []
                    for recipe in recipes:
                        recipe_id = recipe.get("id")
                        recipe_detail = await self.get_recipe_by_id(recipe_id)
                        if recipe_detail:
                            full_recipes.append(recipe_detail)
                    
                    return full_recipes
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return []
    
    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get recipe details by ID"""
        # Check if we have it locally first
        if not self.recipes_df.empty:
            recipe = self.recipes_df[self.recipes_df['id'] == recipe_id]
            if not recipe.empty:
                return recipe.iloc[0].to_dict()
        
        # Fetch from API if not in local data
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "apiKey": self.api_key,
                    "includeNutrition": False,
                }
                response = await client.get(f"{self.api_base_url}/recipes/{recipe_id}/information", params=params)
                
                if response.status_code == 200:
                    recipe = response.json()
                    processed_recipe = {
                        "id": recipe.get("id"),
                        "title": recipe.get("title"),
                        "image": recipe.get("image"),
                        "readyInMinutes": recipe.get("readyInMinutes"),
                        "servings": recipe.get("servings"),
                        "sourceUrl": recipe.get("sourceUrl"),
                        "summary": recipe.get("summary"),
                        "ingredients": [
                            {
                                "name": ingredient.get("name", ""),
                                "amount": ingredient.get("amount", 0),
                                "unit": ingredient.get("unit", "")
                            }
                            for ingredient in recipe.get("extendedIngredients", [])
                        ],
                        "instructions": recipe.get("instructions", "")
                    }
                    
                    # Add to our local data
                    new_recipe_df = pd.DataFrame([processed_recipe])
                    if not self.recipes_df.empty:
                        self.recipes_df = pd.concat([self.recipes_df, new_recipe_df]).drop_duplicates(subset=['id'])
                    else:
                        self.recipes_df = new_recipe_df
                    
                    # Save to file
                    await self._save_recipes(self.recipes_df.to_dict('records'))
                    
                    return processed_recipe
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error fetching recipe details: {e}")
            return None
    
    async def get_recipes_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """Get recipes that match the given ingredients"""
        try:
            # Check if we have recipes locally first
            if not self.recipes_df.empty:
                # Count how many of the requested ingredients are in each recipe
                def count_matching_ingredients(recipe_ingredients, requested_ingredients):
                    count = 0
                    for requested in requested_ingredients:
                        for recipe_ing in recipe_ingredients:
                            ing_name = str(recipe_ing.get('name', '')).lower()
                            if requested.lower() in ing_name:
                                count += 1
                                break
                    return count
                
                # Make a copy of the dataframe to avoid modifying the original
                temp_df = self.recipes_df.copy()
                
                # Apply counting function and filter recipes that have at least one ingredient
                temp_df['ingredient_match_count'] = temp_df['ingredients'].apply(
                    lambda recipe_ingredients: count_matching_ingredients(recipe_ingredients, ingredients)
                )
                
                # Filter recipes with at least one ingredient match
                filtered_recipes = temp_df[temp_df['ingredient_match_count'] > 0]
                
                # Sort by number of matching ingredients (descending)
                if not filtered_recipes.empty:
                    filtered_recipes = filtered_recipes.sort_values(by='ingredient_match_count', ascending=False)
                    
                    # Extract the results before trying to modify the DataFrame further
                    result_recipes = filtered_recipes.copy()
                    
                    # Clean up the temporary column before returning
                    result_recipes = result_recipes.drop(columns=['ingredient_match_count'])
                    return result_recipes.to_dict('records')
            
            # Fetch from API if no local results
            ingredients_param = ",+".join(ingredients)
            async with httpx.AsyncClient() as client:
                params = {
                    "apiKey": self.api_key,
                    "ingredients": ingredients_param,
                    "number": 10,
                    "ranking": 1,  # Maximize used ingredients
                    "ignorePantry": False,
                }
                response = await client.get(f"{self.api_base_url}/recipes/findByIngredients", params=params)
                
                if response.status_code == 200:
                    recipes = response.json()
                    
                    # Fetch full recipe details for each result
                    full_recipes = []
                    for recipe in recipes:
                        recipe_id = recipe.get("id")
                        recipe_detail = await self.get_recipe_by_id(recipe_id)
                        if recipe_detail:
                            full_recipes.append(recipe_detail)
                    
                    return full_recipes
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            print(f"Error finding recipes by ingredients: {e}")
            return [] 