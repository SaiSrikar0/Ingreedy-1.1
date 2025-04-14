// Wait for DOM to load before executing code
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const searchBtn = document.getElementById('search-btn');
    const recipeSearch = document.getElementById('recipe-search');
    const recipesList = document.getElementById('recipes-list');
    const recipeDetail = document.getElementById('recipe-detail');
    const recipeDetailContent = document.getElementById('recipe-detail-content');
    const closeDetailBtn = document.querySelector('.close-detail-btn');
    
    // Templates
    const userMessageTemplate = document.getElementById('user-message-template');
    const botMessageTemplate = document.getElementById('bot-message-template');
    const thinkingTemplate = document.getElementById('thinking-template');
    const recipeDetailTemplate = document.getElementById('recipe-detail-template');
    
    // Initialize event listeners
    initEventListeners();
    
    /**
     * Initialize all event listeners
     */
    function initEventListeners() {
        // Chat form submission
        chatForm.addEventListener('submit', handleChatSubmit);
        
        // Recipe search
        searchBtn.addEventListener('click', handleRecipeSearch);
        recipeSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleRecipeSearch();
            }
        });
        
        // View recipe details from main list
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('view-recipe-btn') || 
                e.target.classList.contains('view-suggestion-btn')) {
                const recipeCard = e.target.closest('[data-id]');
                if (recipeCard) {
                    const recipeId = recipeCard.dataset.id;
                    fetchRecipeDetails(recipeId);
                }
            }
        });
        
        // Close recipe detail view
        closeDetailBtn.addEventListener('click', function() {
            recipeDetail.style.display = 'none';
        });
    }
    
    /**
     * Handle chat form submission
     * @param {Event} e - Form submit event
     */
    async function handleChatSubmit(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Clear input field
        userInput.value = '';
        
        // Add user message to chat
        addUserMessage(message);
        
        // Show thinking indicator
        const thinkingIndicator = addThinkingIndicator();
        
        try {
            // Send message to backend
            const response = await sendMessage(message);
            
            // Remove thinking indicator
            chatMessages.removeChild(thinkingIndicator);
            
            // Add bot response to chat
            addBotResponse(response);
            
            // Scroll to bottom of chat
            scrollToBottom();
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove thinking indicator
            chatMessages.removeChild(thinkingIndicator);
            
            // Add error message
            addBotMessage('Sorry, I encountered an error while processing your request. Please try again.');
        }
    }
    
    /**
     * Send message to backend
     * @param {string} message - User message
     * @returns {Promise<string>} - Bot response HTML
     */
    async function sendMessage(message) {
        const formData = new FormData();
        formData.append('message', message);
        
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.text();
    }
    
    /**
     * Add user message to chat
     * @param {string} message - User message text
     */
    function addUserMessage(message) {
        const messageNode = userMessageTemplate.content.cloneNode(true);
        messageNode.querySelector('p').textContent = message;
        chatMessages.appendChild(messageNode);
        scrollToBottom();
    }
    
    /**
     * Add bot message to chat
     * @param {string} message - Bot message text
     */
    function addBotMessage(message) {
        const messageNode = botMessageTemplate.content.cloneNode(true);
        messageNode.querySelector('p').textContent = message;
        chatMessages.appendChild(messageNode);
        scrollToBottom();
    }
    
    /**
     * Add bot response HTML to chat
     * @param {string} html - Bot response HTML
     */
    function addBotResponse(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        const messageNode = botMessageTemplate.content.cloneNode(true);
        const messageContent = messageNode.querySelector('.message-content');
        
        // Clear default <p> in the template
        messageContent.innerHTML = '';
        
        // Add the response content
        const responseContent = tempDiv.querySelector('.bot-response');
        if (responseContent) {
            messageContent.appendChild(responseContent);
        } else {
            // Fallback if no proper response structure
            messageContent.innerHTML = html;
        }
        
        chatMessages.appendChild(messageNode);
        
        // Add click events to any recipe suggestion buttons in the response
        const suggestionBtns = chatMessages.querySelectorAll('.view-suggestion-btn');
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const recipeCard = this.closest('[data-id]');
                if (recipeCard) {
                    const recipeId = recipeCard.dataset.id;
                    fetchRecipeDetails(recipeId);
                }
            });
        });
    }
    
    /**
     * Add thinking indicator to chat
     * @returns {Node} - The thinking indicator node
     */
    function addThinkingIndicator() {
        const thinkingNode = thinkingTemplate.content.cloneNode(true);
        chatMessages.appendChild(thinkingNode);
        
        // Get the actual node that was added to the DOM
        const thinkingElement = chatMessages.lastElementChild;
        
        scrollToBottom();
        return thinkingElement;
    }
    
    /**
     * Scroll to bottom of chat messages
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    /**
     * Handle recipe search
     */
    async function handleRecipeSearch() {
        const query = recipeSearch.value.trim();
        if (!query) return;
        
        try {
            const response = await fetch(`/recipes/search?query=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const recipes = await response.json();
            updateRecipesList(recipes);
        } catch (error) {
            console.error('Error searching recipes:', error);
        }
    }
    
    /**
     * Update recipes list with search results
     * @param {Array} recipes - Recipe data
     */
    function updateRecipesList(recipes) {
        recipesList.innerHTML = '';
        
        if (recipes.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.textContent = 'No recipes found. Try a different search.';
            recipesList.appendChild(noResults);
            return;
        }
        
        recipes.forEach(recipe => {
            const recipeCard = document.createElement('div');
            recipeCard.className = 'recipe-card';
            recipeCard.dataset.id = recipe.id;
            
            recipeCard.innerHTML = `
                <div class="recipe-image">
                    ${recipe.image ? 
                        `<img src="${recipe.image}" alt="${recipe.title}">` : 
                        `<div class="placeholder-image"><i class="fas fa-camera"></i></div>`}
                </div>
                <div class="recipe-info">
                    <h3 class="recipe-title">${recipe.title}</h3>
                    <div class="recipe-meta">
                        <span><i class="far fa-clock"></i> ${recipe.readyInMinutes || '?'} min</span>
                        <span><i class="fas fa-users"></i> ${recipe.servings || '?'} servings</span>
                    </div>
                    <button class="view-recipe-btn">View Recipe</button>
                </div>
            `;
            
            recipesList.appendChild(recipeCard);
            
            // Add animation class after a small delay to trigger animation
            setTimeout(() => {
                recipeCard.classList.add('fadeInUp');
            }, 10);
        });
    }
    
    /**
     * Fetch recipe details by ID
     * @param {string|number} recipeId - Recipe ID
     */
    async function fetchRecipeDetails(recipeId) {
        try {
            const response = await fetch(`/recipes/search?query=id:${recipeId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const recipes = await response.json();
            
            if (recipes.length > 0) {
                displayRecipeDetail(recipes[0]);
            } else {
                console.error('Recipe not found');
            }
        } catch (error) {
            console.error('Error fetching recipe details:', error);
        }
    }
    
    /**
     * Display recipe detail view
     * @param {Object} recipe - Recipe data
     */
    function displayRecipeDetail(recipe) {
        // Clone the recipe detail template
        const detailContent = recipeDetailTemplate.content.cloneNode(true);
        
        // Set recipe details
        detailContent.querySelector('.recipe-detail-title').textContent = recipe.title;
        
        // Set image
        const imgElement = detailContent.querySelector('.recipe-detail-img');
        if (recipe.image) {
            imgElement.src = recipe.image;
            imgElement.alt = recipe.title;
        } else {
            imgElement.parentNode.innerHTML = `<div class="placeholder-image large-placeholder"><i class="fas fa-camera"></i></div>`;
        }
        
        // Set preparation time and servings
        detailContent.querySelector('.prep-time').textContent = recipe.readyInMinutes || '?';
        detailContent.querySelector('.servings').textContent = recipe.servings ? `${recipe.servings} servings` : 'Unknown';
        
        // Set summary (if available)
        if (recipe.summary) {
            detailContent.querySelector('.recipe-summary').innerHTML = recipe.summary;
        } else {
            detailContent.querySelector('.recipe-summary').textContent = 'No summary available.';
        }
        
        // Set ingredients
        const ingredientsList = detailContent.querySelector('.ingredients-list');
        if (recipe.ingredients && recipe.ingredients.length > 0) {
            recipe.ingredients.forEach(ingredient => {
                const li = document.createElement('li');
                li.textContent = `${ingredient.amount ? `${ingredient.amount} ` : ''}${ingredient.unit || ''} ${ingredient.name}`.trim();
                ingredientsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Ingredients not available.';
            ingredientsList.appendChild(li);
        }
        
        // Set instructions
        const instructionsContent = detailContent.querySelector('.instructions-content');
        if (recipe.instructions) {
            instructionsContent.innerHTML = recipe.instructions;
        } else {
            instructionsContent.textContent = 'Instructions not available.';
        }
        
        // Set source URL
        const sourceLink = detailContent.querySelector('.source-link');
        if (recipe.sourceUrl) {
            sourceLink.href = recipe.sourceUrl;
        } else {
            sourceLink.style.display = 'none';
        }
        
        // Clear previous content and add new content
        recipeDetailContent.innerHTML = '';
        recipeDetailContent.appendChild(detailContent);
        
        // Show the detail view
        recipeDetail.style.display = 'block';
    }
}); 