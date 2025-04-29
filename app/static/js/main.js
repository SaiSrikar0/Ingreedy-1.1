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
    
    // Initialize the theme toggle
    initThemeToggle();
    
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
        
        // View all recipes button
        const viewAllBtn = document.getElementById('view-all-recipes-btn');
        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', loadAllRecipes);
        }
        
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
        
        // Add event listener for the back home button
        const backHomeBtn = document.getElementById('back-home-btn');
        if (backHomeBtn) {
            backHomeBtn.addEventListener('click', function() {
                loadInitialRecipes();
            });
        }
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
     * @returns {Promise<Object>} - Bot response object with message and recipes
     */
    async function sendMessage(message) {
        const response = await fetch('/chat/simple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
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
     * Add bot response to chat
     * @param {Object} response - Bot response object with message and recipes
     */
    function addBotResponse(response) {
        const messageNode = botMessageTemplate.content.cloneNode(true);
        const messageContent = messageNode.querySelector('.message-content');
        
        // Clear default <p> in the template
        messageContent.innerHTML = '';
        
        // Add the text message
        const messageP = document.createElement('p');
        messageP.textContent = response.message;
        messageContent.appendChild(messageP);
        
        // Add recipe suggestions if available
        if (response.recipes && response.recipes.length > 0) {
            const suggestedRecipes = document.createElement('div');
            suggestedRecipes.className = 'suggested-recipes';
            
            const suggestionsHeader = document.createElement('div');
            suggestionsHeader.className = 'suggestions-header';
            suggestionsHeader.textContent = 'Suggested Recipes:';
            suggestedRecipes.appendChild(suggestionsHeader);
            
            const suggestionCards = document.createElement('div');
            suggestionCards.className = 'suggestion-cards';
            
            response.recipes.forEach(recipe => {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.dataset.id = recipe.id;
                
                // Create image container
                const imgContainer = document.createElement('div');
                imgContainer.className = 'suggestion-img';
                
                if (recipe.image) {
                    const img = document.createElement('img');
                    img.src = recipe.image;
                    img.alt = recipe.title;
                    imgContainer.appendChild(img);
                } else {
                    const placeholder = document.createElement('div');
                    placeholder.className = 'placeholder-image';
                    const icon = document.createElement('i');
                    icon.className = 'fas fa-camera';
                    placeholder.appendChild(icon);
                    imgContainer.appendChild(placeholder);
                }
                
                // Find where the button is created
                const btnContainer = document.createElement('div');
                btnContainer.className = 'suggestion-info';
                
                const title = document.createElement('h4');
                title.className = 'suggestion-title';
                title.textContent = recipe.title;
                btnContainer.appendChild(title);
                
                const viewBtn = document.createElement('button');
                viewBtn.className = 'view-suggestion-btn';
                viewBtn.textContent = 'View Recipe';
                viewBtn.style.backgroundColor = '#ff6b6b'; // Set the Ingreedy red color explicitly
                btnContainer.appendChild(viewBtn);
                
                card.appendChild(imgContainer);
                card.appendChild(btnContainer);
                suggestionCards.appendChild(card);
            });
            
            suggestedRecipes.appendChild(suggestionCards);
            messageContent.appendChild(suggestedRecipes);
        }
        
        chatMessages.appendChild(messageNode);
        scrollToBottom();
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
                <div class="recipe-image" data-title="${recipe.title}">
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
            // Show loading state
            recipeDetail.style.display = 'block';
            recipeDetailContent.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading recipe details...</div>';
            
            // Use the dedicated recipe endpoint
            const response = await fetch(`/recipes/${recipeId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const recipe = await response.json();
            displayRecipeDetail(recipe);
        } catch (error) {
            console.error('Error fetching recipe details:', error);
            recipeDetailContent.innerHTML = '<div class="error">Sorry, we could not load the recipe details. Please try again.</div>';
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
        
        // Ensure the detail view is visible
        recipeDetail.style.display = 'block';
    }

    function initThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        
        // Check if user has a saved preference
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.checked = true;
            themeIcon.classList.replace('fa-moon', 'fa-sun');
        }
        
        // Theme toggle event listener
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
                themeIcon.classList.replace('fa-moon', 'fa-sun');
            } else {
                document.body.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
                themeIcon.classList.replace('fa-sun', 'fa-moon');
            }
        });
    }

    // Function to load initial recipes (homepage)
    async function loadInitialRecipes() {
        try {
            // Show loading state
            const recipesList = document.getElementById('recipes-list');
            recipesList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading recipes...</p></div>';
            
            // Fetch random recipes for homepage
            const response = await fetch('/');
            
            if (!response.ok) {
                throw new Error('Failed to fetch recipes');
            }
            
            // Since we're fetching the homepage HTML, we need to extract just the recipes container
            const html = await response.text();
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Get the recipes container HTML
            const newRecipesContainer = tempDiv.querySelector('#recipes-list');
            if (newRecipesContainer) {
                recipesList.innerHTML = newRecipesContainer.innerHTML;
            } else {
                recipesList.innerHTML = '<div class="error"><p>Could not load recipes.</p></div>';
            }
            
            // Add event listeners to the recipe cards
            addRecipeCardEventListeners();
            
        } catch (error) {
            console.error('Error loading initial recipes:', error);
            document.getElementById('recipes-list').innerHTML = 
                '<div class="error"><p>Error loading recipes. Please try again later.</p></div>';
        }
    }

    // Function to load all recipes (updated to use the new endpoint)
    async function loadAllRecipes() {
        try {
            // Show loading state
            const recipesList = document.getElementById('recipes-list');
            recipesList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading all recipes...</p></div>';
            
            // Fetch all recipes from the new endpoint
            const response = await fetch('/api/recipes/all');
            
            if (!response.ok) {
                throw new Error(`Failed to fetch recipes: ${response.status} ${response.statusText}`);
            }
            
            const recipes = await response.json();
            
            // Clear loading indicator
            recipesList.innerHTML = '';
            
            if (!recipes || recipes.length === 0) {
                recipesList.innerHTML = '<div class="error"><p>No recipes found.</p></div>';
                return;
            }
            
            // Render all recipes
            recipes.forEach(recipe => {
                const recipeCard = createRecipeCard(recipe);
                recipesList.appendChild(recipeCard);
            });
            
            // Add event listeners to the new recipe cards
            addRecipeCardEventListeners();
            
        } catch (error) {
            console.error('Error loading all recipes:', error);
            document.getElementById('recipes-list').innerHTML = 
                `<div class="error"><p>Error loading recipes: ${error.message}</p><p>Please try again later.</p></div>`;
        }
    }

    // Updated function to create a recipe card with visible title overlay
    function createRecipeCard(recipe) {
        const card = document.createElement('div');
        card.className = 'recipe-card';
        card.dataset.id = recipe.id;
        
        let imageHtml = '';
        if (recipe.image) {
            imageHtml = `
                <div class="recipe-image">
                    <img src="${recipe.image}" alt="${recipe.title}">
                    <div class="recipe-image-overlay">${recipe.title}</div>
                </div>`;
        } else {
            imageHtml = `
                <div class="recipe-image">
                    <div class="placeholder-image"><i class="fas fa-camera"></i></div>
                    <div class="recipe-image-overlay">${recipe.title}</div>
                </div>`;
        }
        
        card.innerHTML = `
            ${imageHtml}
            <div class="recipe-info">
                <h3 class="recipe-title">${recipe.title}</h3>
                <div class="recipe-meta">
                    <span><i class="far fa-clock"></i> ${recipe.readyInMinutes} min</span>
                    <span><i class="fas fa-users"></i> ${recipe.servings} servings</span>
                </div>
                <button class="view-recipe-btn">View Recipe</button>
            </div>
        `;
        
        return card;
    }

    // Function to add event listeners to recipe cards
    function addRecipeCardEventListeners() {
        const recipeCards = document.querySelectorAll('.recipe-card');
        
        recipeCards.forEach(card => {
            // Remove any existing event listeners to avoid duplicates
            const clonedCard = card.cloneNode(true);
            card.parentNode.replaceChild(clonedCard, card);
            
            // Get the view recipe button in this card
            const viewRecipeBtn = clonedCard.querySelector('.view-recipe-btn');
            
            // Add click event to the entire card
            clonedCard.addEventListener('click', function(e) {
                // Only proceed if the click wasn't on the button (button has its own handler)
                if (!e.target.closest('.view-recipe-btn')) {
                    const recipeId = this.dataset.id;
                    loadRecipeDetail(recipeId);
                }
            });
            
            // Add click event to the view recipe button
            if (viewRecipeBtn) {
                viewRecipeBtn.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent the card click from firing
                    const recipeId = clonedCard.dataset.id;
                    loadRecipeDetail(recipeId);
                });
            }
        });
    }

    // Function to load recipe details (assuming this exists elsewhere in your code)
    async function loadRecipeDetail(recipeId) {
        try {
            // Show loading in recipe detail
            const recipeDetailContainer = document.getElementById('recipe-detail-content');
            recipeDetailContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading recipe details...</p></div>';
            
            // Show the recipe detail container
            document.getElementById('recipe-detail').style.display = 'block';
            document.getElementById('chat-container').style.display = 'none';
            
            // Fetch recipe details
            const response = await fetch(`/recipes/${recipeId}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch recipe details');
            }
            
            const recipe = await response.json();
            
            // Get the recipe detail template
            const template = document.getElementById('recipe-detail-template');
            const content = template.content.cloneNode(true);
            
            // Populate the template with recipe data
            content.querySelector('.recipe-detail-img').src = recipe.image || '';
            content.querySelector('.recipe-detail-img').alt = recipe.title;
            content.querySelector('.recipe-detail-title').textContent = recipe.title;
            content.querySelector('.prep-time').textContent = recipe.readyInMinutes;
            content.querySelector('.servings').textContent = recipe.servings;
            
            // Add the summary
            content.querySelector('.recipe-summary').innerHTML = recipe.summary;
            
            // Add ingredients
            const ingredientsList = content.querySelector('.ingredients-list');
            recipe.ingredients.forEach(ingredient => {
                const li = document.createElement('li');
                li.textContent = `${ingredient.amount} ${ingredient.unit} ${ingredient.name}`;
                ingredientsList.appendChild(li);
            });
            
            // Add instructions
            content.querySelector('.instructions-content').innerHTML = recipe.instructions;
            
            // Add source link
            const sourceLink = content.querySelector('.source-link');
            sourceLink.href = recipe.sourceUrl;
            
            // Clear the container and add the populated template
            recipeDetailContainer.innerHTML = '';
            recipeDetailContainer.appendChild(content);
            
            // Add event listener to close button
            const closeBtn = document.querySelector('.close-detail-btn');
            closeBtn.addEventListener('click', function() {
                document.getElementById('recipe-detail').style.display = 'none';
                document.getElementById('chat-container').style.display = 'block';
            });
            
        } catch (error) {
            console.error('Error loading recipe detail:', error);
            document.getElementById('recipe-detail-content').innerHTML = 
                '<div class="error"><p>Error loading recipe details. Please try again later.</p></div>';
        }
    }

    // Remove view all button event listener
    document.getElementById('view-all-recipes-btn')?.removeEventListener('click', () => {
        window.location.href = '/recipes';
    });
}); 