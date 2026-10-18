# Product Vision (owner's brief, verbatim intent)

An interactive sous-chef AI bot linked to a quick-commerce application such as JioMart. Changes made to the recommendation engine directly affect the recommendations the chatbot suggests. Users interact in natural language, by sharing YouTube videos, and by uploading pictures.

## Interaction methods
1. **YouTube link:** analyse the transcript and add the ingredient list to the cart.
2. **Text recipe** (one or many messages): analyse and add the ingredients to the cart.
3. **Natural language** (e.g. "I am feeling indulgent"): interpret the meaning and add the relevant ingredients.
4. **Picture:** assumed to show ingredients the user already has. Identify them, find matching recipes, respond with the recipes, and add any missing ingredients to the cart.

## Cart
1. Cart icon at the top right of the chat window, with a notification bubble.
2. Click shows all dishes; a dish's cost is the sum of its ingredients.
3. User can remove a dish, or remove or edit each ingredient.
4. "Buy Now" places the order.
5. Message: "Order is placed, the rider will see you in 10 mins", shown in the same mobile-shaped window, which collapses after 10 seconds with a progress bar.
6. Empty cart: icon greyed out and not clickable.

## Other rules
- Levers are changed before starting a new chat session.
- Chat history can be cleared independently; the recommendation engine can be reset to defaults independently.
- **Very important:** engine changes must affect the chat recommendations.

## Platform and look
Web-based. Screen split in two: left = recommendation levers (per RecommendationSettingsPanel), right = bot chat. The cart window has a vertical mobile-phone aspect ratio.

## Project must-haves
AI software development lifecycle · documentation · engine affects recommendations · all use cases work · edge cases handled · everything on GitHub · mock data only.

## System
Local LLMs allowed · MacBook M5, 16 GB RAM, 1 TB SSD · bot may access the internet · Claude Code for development.

## Project future features
1. Voice chat.
2. Ability of the bot to upsell sponsored ingredients. 
3. Increase in accuracy of object identification.
4. Allow the user to converse in multiple indian languages 
5. The message tone of the bot must be friendlier 
6. An MCP that can be integrated with existing chatbots (Example: Claude / ChatGPT / Gemini etc)
7. A WhatsApp variant for the bot.
