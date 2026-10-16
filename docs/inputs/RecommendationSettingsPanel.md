# Recommendation Settings Panel - Complete Master Spec

## 1. Master Scoring & Algorithmic Weights
These sliders control the mathematical composition of the recommendation score $S_{\text{final}}(i \mid u, D)$ for any candidate pairing item $i$:

| Parameter Name | UI Type | Default Value | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Culinary Pairing Weight ($w_p$)** | Slider | `0.30` | `0.0 - 1.0` | Controls how heavily the intrinsic co-occurrence affinity between the main dish and companion items influences recommendations (e.g., Biryani & Raita). |
| **User Purchase History Weight ($w_h$)** | Slider | `0.35` | `0.0 - 1.0` | Determines how strongly past orders and category purchase frequencies dictate personalized upsells. |
| **Market Trend & Velocity Weight ($w_t$)** | Slider | `0.20` | `0.0 - 1.0` | Amplifies or dampens real-time locality demand multipliers (e.g., Friday evening dessert surges or monsoon snack spikes). |
| **Persona & Gourmet Boost Weight ($w_g$)** | Slider | `0.15` | `0.0 - 1.0` | Scales the demographic cohort affinity and gourmet/imported preference multipliers. |

---

## 2. User Persona & Hard-Constraint Guardrails
Unlike soft weights, these act as **zero-tolerance binary eligibility filters ($M_{\text{elig}} \in \{0, 1\}$)**. If an item violates a hard guardrail, its composite score is forced to `0`, blocking it from being pitched by the chatbot.

| Parameter Name | UI Type | Options / Values | Description |
| :--- | :--- | :--- | :--- |
| **Probable Gender** | Dropdown | `Female`, `Male`, `Unisex / Neutral` | Applies demographic cohort affinity boosts to items like iron/calcium-rich beverages vs. high-protein athletic snacks. |
| **Probable Dietary Preference** | Dropdown | `Pure Veg (Strict)`, `Jain (No Root Veggies / Pure Veg)`, `Non-Veg / Flexitarian` | Automatically masks out non-veg or onion/garlic items when strict vegetarian or Jain filters are active. |
| **Probable Religious / Cultural Beliefs** | Dropdown | `Hindu (Shravan Month / Fasting Active)`, `Jain (Strict Root-Free)`, `Muslim (Strict Halal Only)`, `Hindu (Regular)`, `None / Secular` | Enforces strict seasonal and religious compliance (e.g., blocking non-halal meat during Eid or non-satvik ingredients during Shravan/Fasting). |

---

## 3. Specialized Diets & Lifestyle Levers
Activates hard masks and specialized recipe/ingredient substitution rules to match dietary health goals.

| Parameter Name | UI Type | Options / Values | Description |
| :--- | :--- | :--- | :--- |
| **Specialized Diet Mode** | Single/Multi-Select | `Standard / Balanced`, `Keto Diet`, `Intermittent Fasting / Low-GI`, `Vegan`, `Gluten-Free`, `High-Protein Fitness` | **Keto:** Filters out high-carb staples and boosts high-fat dairy/avocado.<br>**Vegan:** Enforces hard block on all dairy/animal products.<br>**Gluten-Free:** Filters out standard wheat/maida items. |

---

## 4. Gourmet & Culinary Style Levers
Tunes the bot's propensity to recommend upscale, specialty, or artisanal products over mass-market SKUs.

| Parameter Name | UI Type | Default Value | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Gourmet / Imported Food Affinity** | Slider | `0.50` | `0.0 - 1.0` | Biases recommendations toward specialty cheeses, truffle oils, exotic microgreens, and imported condiments. |
| **Artisanal & Organic Preference** | Slider | `0.60` | `0.0 - 1.0` | Prioritizes farm-to-table organic produce, cold-pressed oils, unrefined jaggery, and small-batch local brands. |

---

## 5. Purchase History Category Affinity Sliders
Fine-tunes the user's historical affinity across specific quick-commerce catalog verticals.

| Parameter Name | UI Type | Default Value | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Bakery & Breads Affinity** | Slider | `0.85` | `0.0 - 1.0` | Boosts ready-to-bake garlic breads, artisan buns, and naan kits. |
| **Dairy & Raita Affinity** | Slider | `0.70` | `0.0 - 1.0` | Controls recommendations for curd, buttermilk, boondi raita, and paneer. |
| **Desserts & Sweets Affinity** | Slider | `0.65` | `0.0 - 1.0` | Tunes recommendations for gulab jamun tubs, ice creams, and regional mithai. |
| **Salads & Healthy Drinks Affinity** | Slider | `0.60` | `0.0 - 1.0` | Boosts zero-sugar coolers, kombucha, sprout salads, and zero-calorie mixers. |
| **Kebabs & High-Protein Affinity** | Slider | `0.75` | `0.0 - 1.0` | Adjusts weight for ready-to-grill soy chunks, chicken seekh, or protein packs. |

---

## 6. Real-Time Market Trends & Contextual Levers
Amplifies velocity multipliers based on temporal, weather, or cultural surges.

| Parameter Name | UI Type | Default Value | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Weekend Indulgence & Festive Surge** | Slider | `0.80` | `0.0 - 1.0` | Scales up velocity multipliers for premium desserts, party snacks, and festive bundles. |
| **Cooling Drinks & Fresh Sides Trend** | Slider | `0.65` | `0.0 - 1.0` | Dynamically boosts iced teas, lemonades, chaas, and raitas during hot weather or spicy meals. |

---

## 7. Business & Inventory Guardrails
Operational limits imposed by dark-store logistics and pricing thresholds.

| Parameter Name | UI Type | Default Value | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Max Companion Add-on Price Cap (₹)** | Number / Slider | `₹200` | `₹80 - ₹400` | Sets an upper budget limit on suggested pairing add-ons to prevent inflating the cart total. |
| **Dark Store Stock Availability Flag** | Toggle | `Enabled` | `True / False` | Automatically filters out items currently flagged as out-of-stock at the user's nearest dark store, swapping in real-time alternatives. |