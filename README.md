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

## Data Flow Diagram

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  User Interface │         │  Backend API    │         │  Recipe Service │
│                 │         │                 │         │                 │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │  HTTP   │                 │  API    │                 │
│ User enters     │ ───────►│ FastAPI         │ ───────►│ Spoonacular API │
│ ingredients     │  POST   │ processes       │  GET    │                 │
│                 │         │ request         │         │                 │
└─────────────────┘         └────────┬────────┘         └─────────────────┘
                                     │                           ▲
                                     ▼                           │
                            ┌─────────────────┐                  │
                            │                 │                  │
                            │ ML Recommender  │                  │
                            │ processes       │──────────────────┘
                            │ ingredients     │   If needed
                            │                 │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │                 │
                            │ Response with   │
                            │ recipe          │
                            │ recommendations │
                            │                 │
                            └─────────────────┘
```

This diagram illustrates the flow of data in the Ingreedy application:

1. The user enters ingredients or a query through the user interface
2. The frontend sends an HTTP POST request to the FastAPI backend
3. The backend processes the request and extracts ingredients
4. If exact matches are needed, the backend queries the Spoonacular API directly
5. For more complex matching, the ML Recommender processes the ingredients using clustering algorithms
6. The results are formatted and returned to the user interface as recipe recommendations

## Screenshots

![Ingreedy Chat Interface](app/static/images/screenshot.png)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/SaiSrikar0/Ingreedy-1.1.git
   cd Ingreedy-1.1
   ```

2. Create a virtual environment and install dependencies:
   
   **Windows:**
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
   
   **macOS/Linux:**
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your Spoonacular API key:
   ```
   SPOONACULAR_API_KEY=your_api_key_here
   ```

4. Run the application:
   
   **Windows:**
   ```
   python run.py
   ```
   
   **macOS/Linux:**
   ```
   python3 run.py
   ```

5. Open your browser and go to `http://localhost:3000`

## Usage Examples

- "What can I make with eggs and potatoes?"
- "I have chicken, broccoli, and rice"
- "Show me vegetarian recipes with mushrooms"
- "What can I cook with pasta and tomatoes?"

## System Requirements

### Software Requirements

1. **Operating System**:
   - Windows 10/11
   - macOS 10.15 (Catalina) or newer
   - Ubuntu 20.04 or newer (or other Linux distributions with equivalent packages)

2. **Backend Dependencies**:
   - Python 3.8 or newer
   - FastAPI 0.68.0 or newer
   - Uvicorn 0.15.0 or newer
   - scikit-learn 1.0.0 or newer
   - Pandas 1.3.0 or newer
   - NLTK 3.6.0 or newer
   - Requests 2.26.0 or newer
   - python-dotenv 0.19.0 or newer

3. **Frontend Dependencies**:
   - Modern web browser with JavaScript enabled:
     - Google Chrome 90+
     - Mozilla Firefox 88+
     - Microsoft Edge 90+
     - Safari 14+

4. **Network Requirements**:
   - Internet connection (for API calls to Spoonacular)
   - Open port for local development server (default: 3000)

### Hardware Requirements

1. **Minimum Requirements**:
   - Processor: Dual-core 2GHz or better
   - RAM: 4GB
   - Storage: 100MB free space
   - Network: Broadband internet connection

2. **Recommended Requirements**:
   - Processor: Quad-core 2.5GHz or better
   - RAM: 8GB or more
   - Storage: 500MB free space
   - Network: High-speed broadband connection

3. **Mobile Support**:
   - The web interface is responsive and supports mobile devices with a minimum screen width of 320px

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Spoonacular API](https://spoonacular.com/food-api) for providing recipe data
- FastAPI for the efficient API framework
- scikit-learn for machine learning algorithms