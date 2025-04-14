# Ingreedy - AI-Powered Recipe Chatbot

Ingreedy is an intelligent recipe chatbot that helps you find recipes based on the ingredients you have. It uses machine learning algorithms to match your ingredients with the best possible recipes.

![Ingreedy Screenshot](docs/ingreedy-screenshot.png)

## Features

- 🤖 **AI-Powered Chatbot**: Ask for recipes with the ingredients you have
- 🔍 **Intelligent Search**: Finds recipes that match your ingredients
- 📋 **Recipe Listing**: Browse through a collection of recipes
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🧠 **Machine Learning**: Uses K-means and Hierarchical clustering to find the best recipe matches

## Technologies Used

- **Backend**: Python with FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: scikit-learn for K-means and Hierarchical clustering
- **API**: Spoonacular API for recipe data
- **Data Processing**: Pandas for data manipulation

## How It Works

1. **Ingredient Extraction**: The system extracts ingredients from your messages
2. **K-means Clustering**: Finds recipes with exact or nearest matching ingredients
3. **Hierarchical Clustering**: Falls back to this if K-means can't find a good match
4. **Recipe Recommendation**: Returns the best matching recipes based on your ingredients

## Getting Started

### Prerequisites

- Python 3.8+
- A Spoonacular API key (get one at [spoonacular.com/food-api](https://spoonacular.com/food-api))

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ingreedy.git
   cd ingreedy
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the root directory with your Spoonacular API key:
   ```
   SPOONACULAR_API_KEY=your_api_key_here
   ```

### Running the Application

1. Start the development server:
   ```
   python -m app.main
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Example Usage

1. Ask Ingreedy for recipes with your ingredients:
   - "What can I make with chicken, broccoli, and rice?"
   - "I have tomatoes, pasta, and garlic. What should I cook?"
   - "Give me a recipe using eggs and potatoes"

2. Browse the suggested recipes and view details about any recipe that interests you

## Project Structure

```
ingreedy/
├── app/                  # Main application package
│   ├── api/              # API endpoints and services
│   ├── data/             # Data storage (local recipe database)
│   ├── ml/               # Machine learning models
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # HTML templates
│   └── main.py           # Entry point of the application
├── venv/                 # Virtual environment (not tracked in git)
├── .env                  # Environment variables (not tracked in git)
├── .gitignore            # Git ignore file
├── LICENSE               # License file
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Spoonacular API](https://spoonacular.com/food-api) for providing recipe data
- [scikit-learn](https://scikit-learn.org/) for machine learning algorithms
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework 