<img width="2811" height="2268" alt="image" src="https://github.com/user-attachments/assets/b8649ded-a3f9-4292-babd-bc0bd01689fc" /><img width="2811" height="2268" alt="image" src="https://github.com/user-attachments/assets/fb6c3ac5-d97e-48c9-9dcf-93d84da9724e" /># Product Vision (owner's brief, verbatim intent)

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

## Future Product Vision & Roadmap

| ID | Feature | Description | Business Value | User Value | Priority |
|----|----------|-------------|----------------|------------|----------|
| F1 | Voice Chat | Enable users to interact with the assistant using natural voice conversations. | High | High | High |
| F2 | Ingredient Addition via Text / Voice | Allow users to add products directly to their cart using commands such as "Add eggs to my cart". | High | Very High | High |
| F3 | Sponsored Ingredient Recommendations | Promote sponsored products and ingredients within recommendations while maintaining relevance and transparency. | Very High | Medium | Medium |
| F4 | Improved Object Identification Accuracy | Enhance computer vision capabilities to improve ingredient and grocery item recognition accuracy. | Very High | Very High | Critical |
| F5 | Multilingual Indian Language Support | Support conversational interactions in multiple Indian languages across text and voice channels. | High | Very High | High |
| F6 | Friendlier Conversational Tone | Improve the bot's personality, contextual awareness, and conversational experience. | Medium | High | High |
| F7 | MCP Integration for External Chatbots | Develop a Model Context Protocol (MCP) interface that enables integrations with ChatGPT, Claude, Gemini, Microsoft Copilot, and other AI platforms. | Strategic | Medium | Medium |
| F8 | WhatsApp Integration | Make the assistant available through WhatsApp, including text, voice notes, image sharing, and shopping workflows. | Very High | High | Medium |
| F9 | Calorie Calculator | Provide calorie estimation, nutritional analysis, and wellness-related insights for ingredients and recipes. | Medium | High | Medium |
| F10 | Subscription Scheduling | Allow users to automate recurring purchases through customizable schedules (e.g., monthly whey protein orders). | High | Medium | Medium |
