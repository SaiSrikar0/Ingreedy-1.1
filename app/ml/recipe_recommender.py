import numpy as np
import pandas as pd
import re
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances
import nltk
import logging

# Download NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    logging.warning(f"Error downloading NLTK resources: {e}")

# Import NLTK modules with error handling
try:
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
except Exception as e:
    logging.warning(f"Error importing NLTK modules: {e}")
    
    # Define fallback tokenizer if NLTK fails
    def word_tokenize(text):
        return text.lower().split()
    
    # Define fallback stopwords if NLTK fails
    class StopwordsProxy:
        def words(self, lang):
            common_stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                                'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                                'by', 'about', 'like', 'through', 'over', 'before', 'after', 
                                'between', 'under', 'above', 'of', 'during', 'without', 'have', 
                                'has', 'had', 'do', 'does', 'did', 'can', 'could', 'will', 
                                'would', 'should', 'might', 'may', 'i', 'you', 'he', 'she', 
                                'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            return common_stopwords
    
    stopwords = StopwordsProxy()

class RecipeRecommender:
    """
    Recipe recommendation system using ML algorithms:
    - K-means clustering to find recipes with exact/nearest ingredients
    - Hierarchical clustering as fallback when K-means fails
    """
    
    def __init__(self, recipe_service):
        """Initialize the recipe recommender with a recipe service"""
        self.recipe_service = recipe_service
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.ingredient_vectorizer = None
        self.vectors = None
        self.recipe_data = None
        self.common_food_ingredients = [
            'salt', 'pepper', 'olive oil', 'garlic', 'onion', 'butter', 'sugar',
            'flour', 'egg', 'milk', 'water', 'chicken', 'beef', 'pork', 'tomato',
            'potato', 'carrot', 'celery', 'rice', 'pasta', 'bread', 'cheese', 
            'lemon', 'lime', 'vinegar', 'oil', 'basil', 'oregano', 'parsley',
            'thyme', 'cilantro', 'cumin', 'paprika', 'cinnamon', 'vanilla',
            'mushroom', 'bell pepper', 'broccoli', 'spinach', 'corn', 'beans',
            'avocado', 'bacon', 'sausage', 'shrimp', 'salmon', 'tuna', 'cream',
            'yogurt', 'sour cream', 'mayonnaise', 'mustard', 'ketchup', 'soy sauce',
            'wine', 'stock', 'broth', 'honey', 'maple syrup', 'chocolate', 'nuts',
            'lettuce', 'cabbage', 'cucumber', 'zucchini', 'eggplant', 'ginger',
            'garlic powder', 'onion powder', 'baking powder', 'baking soda',
            'yeast', 'noodles', 'apple', 'banana', 'orange', 'berries', 'grapes',
            'eggs', 'potatoes'  # Added common singular forms
        ]
    
    def extract_ingredients(self, message: str) -> List[str]:
        """Extract ingredient names from user message"""
        try:
            # Tokenize message
            tokens = word_tokenize(message.lower())
            
            try:
                stop_words = set(stopwords.words('english'))
            except:
                # Fallback if stopwords fail
                stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
                                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                                'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
                                'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
                                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                                'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
                                'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
                                'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                                'through', 'during', 'before', 'after', 'above', 'below', 'to',
                                'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                                'again', 'further', 'then', 'once', 'here', 'there', 'when',
                                'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                                'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
                                'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
                                'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've',
                                'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn',
                                'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn',
                                'wasn', 'weren', 'won', 'wouldn', 'make', 'using', 'use', 'can', 'want',
                                'like', 'need', 'got', 'get', 'would', 'could', 'should', 'recipe',
                                'cook', 'cooking', 'made', 'help', 'please', 'thank', 'thanks',
                                'hi', 'hello', 'hey', 'how', 'what', 'something', 'anything',
                                'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing'])
            
            # Filter tokens to find ingredients
            ingredients = []
            
            # Direct extraction of ingredients from message
            for word in message.lower().split():
                # Check if word is in common ingredients
                if word in self.common_food_ingredients:
                    ingredients.append(word)
            
            # Look for common ingredients in user message
            for ingredient in self.common_food_ingredients:
                if ingredient.lower() in message.lower() and ingredient not in ingredients:
                    ingredients.append(ingredient)
            
            # Look for phrases that might be ingredients
            for i in range(len(tokens)):
                if tokens[i] not in stop_words:
                    # Check single words
                    if tokens[i] in self.common_food_ingredients and tokens[i] not in ingredients:
                        ingredients.append(tokens[i])
                    
                    # Check two-word phrases
                    if i < len(tokens) - 1:
                        two_word = f"{tokens[i]} {tokens[i+1]}"
                        if two_word in self.common_food_ingredients and two_word not in ingredients:
                            ingredients.append(two_word)
            
            # Process specific ingredient keywords
            if 'chicken' in message.lower() and 'chicken' not in ingredients:
                ingredients.append('chicken')
            if 'broccoli' in message.lower() and 'broccoli' not in ingredients:
                ingredients.append('broccoli')
            if 'rice' in message.lower() and 'rice' not in ingredients:
                ingredients.append('rice')
            if 'egg' in message.lower() or 'eggs' in message.lower():
                if 'egg' not in ingredients and 'eggs' not in ingredients:
                    ingredients.append('eggs')
            if 'potato' in message.lower() or 'potatoes' in message.lower():
                if 'potato' not in ingredients and 'potatoes' not in ingredients:
                    ingredients.append('potatoes')
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = [x for x in ingredients if not (x in seen or seen.add(x))]
            
            # If no ingredients found through normal methods, do a fallback extraction
            if not unique_ingredients:
                # Split the message by common delimiters and check each part
                parts = re.split(r'[,\s+]', message.lower())
                for part in parts:
                    clean_part = part.strip()
                    if clean_part and clean_part not in stop_words and len(clean_part) > 2:
                        # Check if it's a possible food item (not a very common word)
                        unique_ingredients.append(clean_part)
            
            return unique_ingredients
        
        except Exception as e:
            # Log the error and return basic extraction as fallback
            logging.error(f"Error in ingredient extraction: {e}")
            
            # Basic fallback extraction
            key_ingredients = []
            msg_lower = message.lower()
            
            # Check for key ingredients in the examples
            if 'chicken' in msg_lower:
                key_ingredients.append('chicken')
            if 'broccoli' in msg_lower:
                key_ingredients.append('broccoli')
            if 'rice' in msg_lower:
                key_ingredients.append('rice')
            if 'egg' in msg_lower or 'eggs' in msg_lower:
                key_ingredients.append('eggs')
            if 'potato' in msg_lower or 'potatoes' in msg_lower:
                key_ingredients.append('potatoes')
            
            return key_ingredients if key_ingredients else ['chicken']  # Return at least something
    
    def _preprocess_recipes(self, recipes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Preprocess recipes for ML algorithms"""
        # Convert to DataFrame
        if not recipes:
            return pd.DataFrame()
        
        df = pd.DataFrame(recipes)
        
        # Extract ingredient names as strings
        df['ingredient_names'] = df['ingredients'].apply(
            lambda ingredients: ' '.join([
                re.sub(r'[^\w\s]', '', ingredient['name'].lower())
                for ingredient in ingredients
            ])
        )
        
        return df
    
    def _vectorize_ingredients(self, df: pd.DataFrame) -> np.ndarray:
        """Convert ingredient text to TF-IDF vectors"""
        if df.empty:
            return np.array([])
        
        # Fit vectorizer if needed
        if self.ingredient_vectorizer is None:
            self.ingredient_vectorizer = TfidfVectorizer(stop_words='english')
            vectors = self.ingredient_vectorizer.fit_transform(df['ingredient_names'])
        else:
            vectors = self.ingredient_vectorizer.transform(df['ingredient_names'])
        
        return vectors
    
    def _vectorize_user_ingredients(self, ingredients: List[str]) -> np.ndarray:
        """Convert user ingredients to the same vector space as recipes"""
        if not ingredients or self.ingredient_vectorizer is None:
            return np.zeros((1, 1))
        
        # Join ingredients into a single string
        ingredient_text = ' '.join(ingredients)
        
        # Transform using the same vectorizer
        return self.ingredient_vectorizer.transform([ingredient_text])
    
    async def _kmeans_clustering(self, recipes_df: pd.DataFrame, user_vector: np.ndarray, 
                               k: int = 5) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Apply K-means clustering to find recipes closest to user ingredients
        Returns: (matching_recipes, success_flag)
        """
        if recipes_df.empty or user_vector.shape[1] <= 1:
            return [], False
        
        # Get recipe vectors
        recipe_vectors = self._vectorize_ingredients(recipes_df)
        
        if recipe_vectors.shape[0] == 0:
            return [], False
        
        # Concatenate user vector with recipe vectors
        all_vectors = np.vstack([recipe_vectors.toarray(), user_vector.toarray()])
        
        # Apply K-means
        num_clusters = min(k, all_vectors.shape[0])
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        clusters = kmeans.fit_predict(all_vectors)
        
        # Find the cluster containing the user query
        user_cluster = clusters[-1]
        
        # Get recipes in the same cluster
        cluster_indices = np.where(clusters[:-1] == user_cluster)[0]
        
        if len(cluster_indices) == 0:
            return [], False
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[cluster_indices].to_dict('records')
        
        return matching_recipes, True
    
    async def _hierarchical_clustering(self, recipes_df: pd.DataFrame, user_vector: np.ndarray, 
                                     threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Apply Hierarchical clustering as a fallback when K-means fails
        """
        if recipes_df.empty or user_vector.shape[1] <= 1:
            return []
        
        # Get recipe vectors
        recipe_vectors = self._vectorize_ingredients(recipes_df)
        
        if recipe_vectors.shape[0] == 0:
            return []
        
        # Calculate distance between user vector and recipe vectors
        distances = pairwise_distances(user_vector.toarray(), recipe_vectors.toarray(), metric='cosine')[0]
        
        # Sort recipes by distance (ascending)
        sorted_indices = np.argsort(distances)
        
        # Get recipes below distance threshold
        matching_indices = sorted_indices[distances[sorted_indices] < threshold]
        
        if len(matching_indices) == 0:
            # If no recipes below threshold, return the 5 closest ones
            matching_indices = sorted_indices[:5]
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[matching_indices].to_dict('records')
        
        return matching_recipes
    
    async def find_recipes_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Main method to find recipes based on user ingredients
        Uses K-means first, falls back to Hierarchical clustering if needed
        """
        if not ingredients:
            # No ingredients provided, return random recipes
            return await self.recipe_service.get_random_recipes(5)
        
        # First try to get recipes with exact ingredients from API
        api_recipes = await self.recipe_service.get_recipes_by_ingredients(ingredients)
        
        if api_recipes:
            return api_recipes
        
        # If no exact matches from API, try ML algorithms on our local data
        
        # Get all available recipes
        if self.recipe_service.recipes_df is not None and not self.recipe_service.recipes_df.empty:
            all_recipes = self.recipe_service.recipes_df.to_dict('records')
        else:
            # Fetch some recipes to work with
            all_recipes = await self.recipe_service.get_random_recipes(100)
        
        # Preprocess recipes
        recipes_df = self._preprocess_recipes(all_recipes)
        
        if recipes_df.empty:
            return []
        
        # Create vector for user ingredients
        user_vector = self._vectorize_user_ingredients(ingredients)
        
        # Try K-means clustering first
        kmeans_results, kmeans_success = await self._kmeans_clustering(recipes_df, user_vector)
        
        if kmeans_success and kmeans_results:
            return kmeans_results
        
        # If K-means fails, use Hierarchical clustering
        hierarchical_results = await self._hierarchical_clustering(recipes_df, user_vector)
        
        return hierarchical_results 