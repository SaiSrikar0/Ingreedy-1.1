import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    def __init__(self):
        # API Keys
        self.SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
        self.GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Application Settings
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Recipe Settings
        self.MAX_RECIPES_PER_SEARCH = int(os.getenv("MAX_RECIPES_PER_SEARCH", "20"))
        self.MIN_LOCAL_RECIPES = int(os.getenv("MIN_LOCAL_RECIPES", "3"))
        self.PRIORITY_SOURCES = os.getenv(
            "PRIORITY_SOURCES",
            "indianhealthyrecipes.com,vegrecipesofindia.com,hebbarskitchen.com,archanaskitchen.com"
        ).split(",")
        
    def validate(self) -> bool:
        """Validate required settings"""
        if not self.SPOONACULAR_API_KEY:
            raise ValueError("SPOONACULAR_API_KEY is required")
        return True
    
    # Common ingredient variations
    INGREDIENT_VARIATIONS: Dict[str, List[str]] = {
        "paneer": ["cottage cheese", "indian cheese"],
        "dal": ["lentils", "pulses"],
        "besan": ["gram flour", "chickpea flour"],
        "ghee": ["clarified butter"],
        "curd": ["yogurt", "dahi"],
        "rava": ["semolina", "sooji"],
        "poha": ["flattened rice", "beaten rice"],
        "idli rava": ["idli rice", "parboiled rice"],
        "dosa batter": ["dosa mix", "dosa flour"],
        "curry leaves": ["kadi patta", "sweet neem leaves"],
        "coriander leaves": ["cilantro", "dhania"],
        "mint leaves": ["pudina"],
        "green chili": ["green chilli", "hari mirch"],
        "mustard seeds": ["rai", "sarson"],
        "fenugreek": ["methi"],
        "asafoetida": ["hing"],
        "cardamom": ["elaichi"],
        "cinnamon": ["dalchini"],
        "cloves": ["laung"],
        "pepper": ["kali mirch"],
        "turmeric": ["haldi"],
        "cumin": ["jeera"],
        "coriander": ["dhania"],
        "garam masala": ["all spice mix"],
        "sambar powder": ["sambar masala"],
        "rasam powder": ["rasam masala"],
        "chili powder": ["red chili powder", "lal mirch powder"],
        "urad dal": ["black gram", "black lentils"],
        "moong dal": ["mung dal", "yellow lentils"],
        "toor dal": ["arhar dal", "pigeon peas"],
        "chana dal": ["bengal gram", "split chickpeas"],
        "rajma": ["kidney beans"],
        "chole": ["chickpeas", "garbanzo beans"],
        "bhature": ["fried bread"],
        "dahi vada": ["curd vada", "dahi bhalla"],
        "rasgulla": ["rasgola", "ras malai"],
        "gulab jamun": ["gulab jam"],
        "ladies finger": ["okra", "bhindi"],
        "brinjal": ["eggplant", "aubergine", "baingan"],
        "cauliflower": ["gobi", "phool gobi"],
        "cabbage": ["patta gobi"],
        "peas": ["matar"],
        "ginger": ["adrak"],
        "garlic": ["lehsun"],
        "cashew": ["kaju"],
        "almond": ["badam"],
        "raisin": ["kishmish"],
        "peanut": ["moongphali"],
        "coconut": ["nariyal"],
        "jaggery": ["gur"],
        "tamarind": ["imli"],
        "lemon": ["nimbu"],
        "water": ["pani"]
    }
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if the application is properly configured"""
        return bool(cls.SPOONACULAR_API_KEY)

# Create a singleton instance
settings = Settings() 