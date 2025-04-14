# Ingreedy - AI Recipe Chatbot

Ingreedy is an AI-powered recipe chatbot that helps you find recipes based on ingredients you have at home. Simply tell the chatbot what ingredients you have, and it will suggest recipes you can make.

## Features

- **Ingredient-based Recipe Search**: Find recipes based on ingredients you have
- **Natural Language Understanding**: Ask in plain English what you can make with your ingredients
- **Smart Recommendations**: Uses machine learning to find suitable recipes even without exact matches
- **Conversational Interface**: Chat naturally with the bot to discover recipes
- **Recipe Details**: View full ingredients, instructions, and nutritional information

## Tech Stack

- **Backend**: Python with FastAPI
- **Machine Learning**: K-means clustering and TF-IDF for ingredient matching
- **Frontend**: HTML, CSS, JavaScript
- **API**: Spoonacular Recipe API for comprehensive recipe data
- **Data Processing**: Pandas for data manipulation

## Screenshots

![Ingreedy Chat Interface](app/static/images/screenshot.png)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ingreedy.git
   cd ingreedy
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your Spoonacular API key:
   ```
   SPOONACULAR_API_KEY=your_api_key_here
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Open your browser and go to `http://localhost:3000`

## Usage Examples

- "What can I make with eggs and potatoes?"
- "I have chicken, broccoli, and rice"
- "Show me vegetarian recipes with mushrooms"
- "What can I cook with pasta and tomatoes?"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Spoonacular API](https://spoonacular.com/food-api) for providing recipe data
- FastAPI for the efficient API framework
- scikit-learn for machine learning algorithms 