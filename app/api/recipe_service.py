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
    
    async def get_recipes_by_ingredients(self, ingredients: List[str], operators: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get recipes that match the given ingredients.
        
        Args:
            ingredients: List of ingredients to search for
            operators: List of operators ('and', 'or') between ingredients. 
                      If None, all ingredients are considered with 'and' logic.
        """
        try:
            # Check if we have recipes locally first
            if not self.recipes_df.empty:
                # Make a copy of the dataframe to avoid modifying the original
                temp_df = self.recipes_df.copy()
                
                # If no operators provided, default to 'and' logic for all ingredients
                if not operators or len(operators) == 0:
                    operators = ['and'] * (len(ingredients) - 1) if len(ingredients) > 1 else []
                
                # Group ingredients by 'and' operators to create required sets
                required_groups = []
                current_group = [ingredients[0]]
                
                for i, op in enumerate(operators):
                    if op.lower() == 'and':
                        # Add to current AND group
                        current_group.append(ingredients[i+1])
                    else:  # 'or' operator
                        # Finish current AND group and start a new one
                        required_groups.append(current_group)
                        current_group = [ingredients[i+1]]
                
                # Add the last group
                if current_group:
                    required_groups.append(current_group)
                
                # Count matching ingredients and group coverage for each recipe
                def evaluate_recipe_match(recipe_ingredients, required_groups):
                    # Count total matches from all groups
                    total_matches = 0
                    
                    # Count how many groups are fully covered
                    groups_covered = 0
                    
                    # For each required group, check if all ingredients are present
                    for group in required_groups:
                        group_matches = 0
                        for ingredient in group:
                            ingredient_found = False
                            for recipe_ing in recipe_ingredients:
                                ing_name = str(recipe_ing.get('name', '')).lower()
                                # More strict matching to ensure ingredient is actually present
                                if ingredient.lower() in ing_name.split() or f"{ingredient.lower()}s" in ing_name.split():
                                    total_matches += 1
                                    group_matches += 1
                                    ingredient_found = True
                                    break
                            
                            # If an ingredient in an AND group is not found, the entire group fails
                            if not ingredient_found and op.lower() == 'and':
                                break
                        
                        # If all ingredients in this group are matched, count the group as covered
                        if group_matches == len(group):
                            groups_covered += 1
                    
                    return {
                        'total_matches': total_matches,
                        'groups_covered': groups_covered,
                        'total_groups': len(required_groups),
                        'percentage_matched': total_matches / sum(len(group) for group in required_groups) if required_groups else 0
                    }
                
                # Apply evaluation function
                match_results = temp_df['ingredients'].apply(
                    lambda recipe_ingredients: evaluate_recipe_match(recipe_ingredients, required_groups)
                )
                
                # Extract match metrics to columns
                temp_df['total_matches'] = match_results.apply(lambda x: x['total_matches'])
                temp_df['groups_covered'] = match_results.apply(lambda x: x['groups_covered'])
                temp_df['total_groups'] = match_results.apply(lambda x: x['total_groups'])
                temp_df['percentage_matched'] = match_results.apply(lambda x: x['percentage_matched'])
                
                # Filter recipes with complete matches for all AND groups
                # For a recipe to match, it must have all ingredients in at least one AND group
                filtered_recipes = temp_df[temp_df['groups_covered'] > 0]
                
                # Sort recipes in priority order:
                # 1. Number of required groups fully covered (descending)
                # 2. Percentage of ingredients matched (descending)
                # 3. Total number of matching ingredients (descending)
                # 4. Recipe title (alphabetical) as a tiebreaker
                if not filtered_recipes.empty:
                    filtered_recipes = filtered_recipes.sort_values(
                        by=['groups_covered', 'percentage_matched', 'total_matches', 'title'], 
                        ascending=[False, False, False, True]
                    )
                    
                    # Extract the results before trying to modify the DataFrame further
                    result_recipes = filtered_recipes.copy()
                    
                    # Clean up the temporary columns before returning
                    result_recipes = result_recipes.drop(columns=['total_matches', 'groups_covered', 'total_groups', 'percentage_matched'])
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