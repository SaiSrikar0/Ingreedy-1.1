import os
import json
import random
import httpx
import pandas as pd
from typing import List, Dict, Any, Optional
import requests
import logging

class RecipeService:
    """Service to fetch and manage recipe data"""
    
    def __init__(self):
        """Initialize the recipe service"""
        self.api_key = os.getenv("SPOONACULAR_API_KEY", "")
        self.api_base_url = "https://api.spoonacular.com"
        self.recipes_data_path = "app/data/recipes.json"
        self.recipes_df = None
        # Add more Indian recipe sources
        self.priority_sources = [
            "indianhealthyrecipes.com",
            "vegrecipesofindia.com",
            "hebbarskitchen.com",
            "archanaskitchen.com",
            "cooking.nytimes.com/recipes/indian",
            "allrecipes.com/recipes/world-cuisine/asian/indian"
        ]
        self._load_recipes()
    
    def _load_recipes(self):
        """Load recipes from local file or create sample data if none exists"""
        try:
            if os.path.exists(self.recipes_data_path):
                with open(self.recipes_data_path, 'r') as f:
                    recipes = json.load(f)
                self.recipes_df = pd.DataFrame(recipes)
            else:
                # Create sample recipes if no data file exists
                sample_recipes = [
                    {
                        "id": 1,
                        "title": "Set Dosa",
                        "image": "https://indianhealthyrecipes.com/wp-content/uploads/2023/01/set-dosa-recipe.jpg",
                        "readyInMinutes": 30,
                        "servings": 4,
                        "sourceUrl": "https://indianhealthyrecipes.com/set-dosa-recipe/",
                        "summary": "Soft and spongy set dosa made with rice and urad dal batter.",
                        "ingredients": [
                            {"name": "rice", "amount": 2, "unit": "cups"},
                            {"name": "urad dal", "amount": 0.5, "unit": "cup"},
                            {"name": "fenugreek seeds", "amount": 0.5, "unit": "tsp"},
                            {"name": "salt", "amount": 1, "unit": "tsp"},
                            {"name": "water", "amount": 2, "unit": "cups"}
                        ],
                        "instructions": "1. Soak rice, urad dal, and fenugreek seeds for 4-6 hours\n2. Grind to a smooth batter\n3. Ferment overnight\n4. Add salt and water to adjust consistency\n5. Cook on a hot griddle until golden brown"
                    },
                    {
                        "id": 2,
                        "title": "Masala Dosa",
                        "image": "https://indianhealthyrecipes.com/wp-content/uploads/2023/01/masala-dosa-recipe.jpg",
                        "readyInMinutes": 45,
                        "servings": 4,
                        "sourceUrl": "https://indianhealthyrecipes.com/masala-dosa-recipe/",
                        "summary": "Crispy dosa stuffed with spicy potato filling.",
                        "ingredients": [
                            {"name": "rice", "amount": 2, "unit": "cups"},
                            {"name": "urad dal", "amount": 0.5, "unit": "cup"},
                            {"name": "potatoes", "amount": 4, "unit": "medium"},
                            {"name": "onions", "amount": 2, "unit": "medium"},
                            {"name": "green chilies", "amount": 2, "unit": "pieces"},
                            {"name": "mustard seeds", "amount": 0.5, "unit": "tsp"},
                            {"name": "turmeric", "amount": 0.25, "unit": "tsp"},
                            {"name": "salt", "amount": 1, "unit": "tsp"}
                        ],
                        "instructions": "1. Prepare dosa batter as in Set Dosa\n2. Make potato filling with onions and spices\n3. Spread dosa batter thin and cook\n4. Add potato filling and fold"
                    },
                    {
                        "id": 3,
                        "title": "Idli",
                        "image": "https://indianhealthyrecipes.com/wp-content/uploads/2023/01/idli-recipe.jpg",
                        "readyInMinutes": 30,
                        "servings": 4,
                        "sourceUrl": "https://indianhealthyrecipes.com/idli-recipe/",
                        "summary": "Soft and fluffy steamed rice cakes.",
                        "ingredients": [
                            {"name": "rice", "amount": 2, "unit": "cups"},
                            {"name": "urad dal", "amount": 0.5, "unit": "cup"},
                            {"name": "fenugreek seeds", "amount": 0.5, "unit": "tsp"},
                            {"name": "salt", "amount": 1, "unit": "tsp"}
                        ],
                        "instructions": "1. Soak rice and urad dal separately\n2. Grind to smooth batter\n3. Ferment overnight\n4. Add salt and steam in idli molds"
                    },
                    {
                        "id": 4,
                        "title": "Pongal",
                        "image": "https://indianhealthyrecipes.com/wp-content/uploads/2023/01/ven-pongal-recipe.jpg",
                        "readyInMinutes": 30,
                        "servings": 4,
                        "sourceUrl": "https://indianhealthyrecipes.com/ven-pongal-recipe/",
                        "summary": "Comforting rice and lentil porridge with ghee and pepper.",
                        "ingredients": [
                            {"name": "rice", "amount": 1, "unit": "cup"},
                            {"name": "moong dal", "amount": 0.5, "unit": "cup"},
                            {"name": "ghee", "amount": 2, "unit": "tbsp"},
                            {"name": "pepper", "amount": 1, "unit": "tsp"},
                            {"name": "cumin", "amount": 1, "unit": "tsp"},
                            {"name": "ginger", "amount": 1, "unit": "inch"},
                            {"name": "cashews", "amount": 10, "unit": "pieces"}
                        ],
                        "instructions": "1. Cook rice and dal together\n2. Temper with ghee, pepper, cumin, and cashews\n3. Mix well and serve hot"
                    }
                ]
                self.recipes_df = pd.DataFrame(sample_recipes)
                # Save sample recipes
                os.makedirs(os.path.dirname(self.recipes_data_path), exist_ok=True)
                with open(self.recipes_data_path, 'w') as f:
                    json.dump(sample_recipes, f)
        except Exception as e:
            print(f"Error loading recipes: {e}")
            self.recipes_df = pd.DataFrame([])
    
    def _is_priority_source(self, source_url: str) -> bool:
        """Check if a recipe is from a priority source"""
        if not source_url:
            return False
        return any(domain in source_url.lower() for domain in self.priority_sources)
    
    def _is_indian_recipe(self, recipe: Dict[str, Any]) -> bool:
        """Check if a recipe is Indian based on title and ingredients"""
        indian_keywords = {
            'dosa', 'idli', 'sambar', 'rasam', 'curry', 'biryani', 'pulao',
            'roti', 'naan', 'paratha', 'puri', 'pongal', 'upma', 'poha',
            'vada', 'pakora', 'samosa', 'chutney', 'dal', 'sabzi', 'bhaji',
            'paneer', 'tikka', 'masala', 'tandoori', 'korma', 'vindaloo',
            'butter chicken', 'chana masala', 'aloo gobi', 'palak paneer',
            'rajma', 'chole', 'bhature', 'dahi vada', 'rasgulla', 'gulab jamun'
        }
        
        # Check title
        title = recipe.get('title', '').lower()
        if any(keyword in title for keyword in indian_keywords):
            return True
        
        # Check ingredients
        ingredients = recipe.get('ingredients', [])
        indian_ingredients = {
            'turmeric', 'cumin', 'coriander', 'mustard seeds', 'fenugreek',
            'asafoetida', 'cardamom', 'cinnamon', 'cloves', 'pepper',
            'chili powder', 'garam masala', 'sambar powder', 'rasam powder',
            'curry leaves', 'coriander leaves', 'mint leaves', 'ghee',
            'urad dal', 'moong dal', 'toor dal', 'chana dal', 'besan'
        }
        
        ingredient_names = {ing.get('name', '').lower() for ing in ingredients}
        if any(ing in ingredient_names for ing in indian_ingredients):
            return True
        
        return False
    
    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        """Search recipes by name or ingredients"""
        try:
            # Try local search first
            if not self.recipes_df.empty:
                filtered_recipes = self.recipes_df[
                    self.recipes_df['title'].str.contains(query, case=False, na=False)
                ]
                if not filtered_recipes.empty:
                    recipes = filtered_recipes.to_dict('records')
                    return self._prioritize_recipes(recipes)
            
            # Fallback to API search if API key is available
            if self.api_key:
                async with httpx.AsyncClient() as client:
                    params = {
                        "apiKey": self.api_key,
                        "query": query,
                        "number": 10,
                    }
                    response = await client.get(f"{self.api_base_url}/recipes/complexSearch", params=params)
                    
                    if response.status_code == 200:
                        recipes = response.json().get("results", [])
                        return self._prioritize_recipes(recipes)
            
            return []
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return []
    
    async def get_recipes_by_ingredients(self, ingredients: List[str], operators: List[str] = None) -> List[Dict[str, Any]]:
        """Get recipes containing the specified ingredients"""
        try:
            # Convert input ingredients to lowercase for case-insensitive matching
            input_ingredients_lower = [ing.lower() for ing in ingredients]
            
            # First try to find recipes in local data
            if not self.recipes_df.empty:
                def ingredient_match(recipe_ingredients):
                    matches = 0
                    for ingredient in recipe_ingredients:
                        ingredient_name = ingredient['name'].lower()
                        # Check for partial matches
                        for input_ing in input_ingredients_lower:
                            if input_ing in ingredient_name or ingredient_name in input_ing:
                                matches += 1
                                break
                    # Return true if at least half of the ingredients match
                    return matches >= len(input_ingredients_lower) / 2
                
                filtered_recipes = self.recipes_df[
                    self.recipes_df['ingredients'].apply(ingredient_match)
                ]
                
                if not filtered_recipes.empty:
                    recipes = filtered_recipes.to_dict('records')
                    # Sort by priority and number of matching ingredients
                    return sorted(recipes, 
                        key=lambda x: (
                            not self._is_priority_source(x.get('sourceUrl', '')),
                            not self._is_indian_recipe(x),
                            sum(1 for ing in input_ingredients_lower 
                                if any(ing in i['name'].lower() or i['name'].lower() in ing 
                                    for i in x['ingredients']))
                        )
                    )
            
            # Fallback to API search if API key is available
            if self.api_key:
                async with httpx.AsyncClient() as client:
                    params = {
                        "apiKey": self.api_key,
                        "ingredients": ",".join(ingredients),
                        "number": 10,
                        "ranking": 2  # Maximize used ingredients
                    }
                    response = await client.get(f"{self.api_base_url}/recipes/findByIngredients", params=params)
                    
                    if response.status_code == 200:
                        recipes = response.json()
                        return sorted(recipes, 
                            key=lambda x: (
                                not self._is_priority_source(x.get('sourceUrl', '')),
                                not self._is_indian_recipe(x),
                                sum(1 for ing in input_ingredients_lower 
                                    if any(ing in i['name'].lower() or i['name'].lower() in ing 
                                        for i in x['ingredients']))
                            )
                        )
            
            return []
        except Exception as e:
            print(f"Error finding recipes by ingredients: {e}")
            return []
    
    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get recipe details by ID"""
        try:
            # Check local data first
            if not self.recipes_df.empty:
                recipe = self.recipes_df[self.recipes_df['id'] == recipe_id]
                if not recipe.empty:
                    return recipe.iloc[0].to_dict()
            
            # Fallback to API if API key is available
            if self.api_key:
                async with httpx.AsyncClient() as client:
                    params = {"apiKey": self.api_key}
                    response = await client.get(f"{self.api_base_url}/recipes/{recipe_id}/information", params=params)
                    
                    if response.status_code == 200:
                        return response.json()
            
            return None
        except Exception as e:
            print(f"Error fetching recipe details: {e}")
            return None
    
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
    
    async def _save_recipes(self, recipes: List[Dict[str, Any]]):
        """Save recipes to local file"""
        try:
            os.makedirs(os.path.dirname(self.recipes_data_path), exist_ok=True)
            with open(self.recipes_data_path, 'w') as f:
                json.dump(recipes, f)
            print(f"Saved {len(recipes)} recipes to local file")
        except Exception as e:
            print(f"Error saving recipes: {e}")

    def _prioritize_recipes(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize recipes from preferred sources and Indian recipes"""
        priority_recipes = []
        other_recipes = []
        
        for recipe in recipes:
            # Check if it's from a priority source
            if self._is_priority_source(recipe.get('sourceUrl', '')):
                priority_recipes.append(recipe)
            # Check if it's an Indian recipe by title or ingredients
            elif self._is_indian_recipe(recipe):
                priority_recipes.append(recipe)
            else:
                other_recipes.append(recipe)
        
        return priority_recipes + other_recipes

    async def get_all_recipes(self) -> List[Dict[str, Any]]:
        """Get all available recipes"""
        try:
            # First try to get recipes from local data
            if not self.recipes_df.empty:
                return self.recipes_df.to_dict('records')
            
            # If no local data, fetch from API
            if not self.api_key:
                return []
                
            async with httpx.AsyncClient() as client:
                params = {
                    "apiKey": self.api_key,
                    "number": 100,  # Maximum number of recipes to fetch
                    "addRecipeInformation": True,
                    "fillIngredients": True
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
                    
                    # Update local data
                    self.recipes_df = pd.DataFrame(processed_recipes)
                    
                    # Save recipes
                    await self._save_recipes(processed_recipes)
                    
                    return processed_recipes
                else:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logging.error(f"Error in get_all_recipes: {e}")
            return [] 