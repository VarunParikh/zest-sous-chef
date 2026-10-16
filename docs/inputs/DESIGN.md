# Quick Commerce AI Sous-Chef Design Specification

A minimalist, high-clarity design system and interface specification for a dual-pane AI Sous-Chef workbench and companion mobile quick-commerce shopping experience.

---

## Colors

The color palette adopts a modern enterprise quick-commerce aesthetic: cool light neutrals, clean borders, deep violet/plum accent tones (`#381E72`), and high-contrast typography.

### Light Neutral Palette (Workbench & Core UI)
* **Canvas Background (`neutral-50`):** `#F8F9FA`
* **Card & Container Surface (`neutral-0`):** `#FFFFFF`
* **Subtle Panel Fill (`neutral-100`):** `#F1F3F5`
* **Border Line Standard (`neutral-200`):** `#E5E7EB`
* **Border Line Strong (`neutral-300`):** `#D1D5DB`
* **Text Muted / Meta (`neutral-500`):** `#6B7280`
* **Text Secondary (`neutral-700`):** `#374151`
* **Text Primary / Headings (`neutral-900`):** `#111827`

### Brand & Accent Palette
* **Brand Primary (Deep Violet):** `#381E72`
* **Brand Primary Hover:** `#2C1659`
* **Brand Primary Active / Pressed:** `#231048`
* **Brand Accent Subtle (Lavender Tint):** `#F3EEFC`
* **Brand Focus Ring:** `#381E72` (2px solid, 2px offset)

### Status & Feedback Colors
* **Status Connected / Success (Emerald Green):** `#10B981`
* **Status Success Surface:** `#ECFDF5`
* **Status Warning (Amber Ochre):** `#D97706`
* **Status Warning Surface:** `#FFFBEB`
* **Status Error (Crimson Red):** `#DC2626`
* **Status Error Surface:** `#FEF2F2`
* **Status Inactive / Dimmed Text:** `#9CA3AF`
* **Status Inactive Surface:** `#F3F4F6`

### Mobile Screen 2 Dark Celebration Palette
* **Celebration Background Canvas:** `#1E0A3C` to `#3B1464` (Radial/Fluid Violet Gradient)
* **Celebration Surface Card / Badge:** `rgba(255, 255, 255, 0.12)` with `backdrop-filter: blur(12px)`
* **Celebration Text Primary:** `#FFFFFF`
* **Celebration Text Secondary:** `#D8B4FE`
* **Celebration Checkmark Fill:** `#FFFFFF` on `#7C3AED`

---

## Typography

* **Primary Interface Font:** `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`
* **Display / Brand Font:** `"Plus Jakarta Sans"`, `Inter`, `sans-serif`
* **Monospace / Numerics Font:** `"JetBrains Mono"`, `"SF Mono"`, `Menlo`, `monospace`

---

## Font Sizes

* `text-xs`: `0.75rem` (12px)
* `text-sm`: `0.875rem` (14px)
* `text-base`: `1.0rem` (16px)
* `text-lg`: `1.125rem` (18px)
* `text-xl`: `1.25rem` (20px)
* `text-2xl`: `1.5rem` (24px)
* `text-3xl`: `1.875rem` (30px)
* `text-4xl`: `2.25rem` (36px)

---

## Font Weights

* `font-normal`: `400` (Body copy, ingredient descriptions, secondary notes)
* `font-medium`: `500` (Form inputs, button labels, category tags)
* `font-semibold`: `600` (Section headings, SKU titles, dish names, pricing)
* `font-bold`: `700` (Modal headings, celebration message, primary brand title)

---

## Line Heights

* `leading-none`: `1.0` (Price badges, icons, counter chips)
* `leading-tight`: `1.2` (Screen headers, order placed modal heading)
* `leading-snug`: `1.35` (Dish headers, card titles)
* `leading-normal`: `1.5` (Chat dialogue, ingredient list lines)
* `leading-relaxed`: `1.625` (Descriptive tooltips, long-form explanations)

---

## Spacing

* `space-0`: `0px`
* `space-1`: `4px`
* `space-2`: `8px`
* `space-3`: `12px`
* `space-4`: `16px`
* `space-5`: `20px`
* `space-6`: `24px`
* `space-8`: `32px`
* `space-10`: `40px`
* `space-12`: `48px`
* `space-16`: `64px`

---

## Grid System

* **Desktop Workbench (>= 1024px):** Strict 2-column equal split (`grid-cols-2`, `50% : 50%`), `24px` column gap, independent vertical scrolling per column.
* **Mobile Overlays (< 640px):** Single vertical mobile viewport (`390px` to `428px` target width), full-height flex column.

---

## Layout

* **Top Navigation Bar:** Height `56px`, fixed top, border-bottom `1px solid #E5E7EB`.
* **Workbench Shell:** Height `calc(100vh - 56px)`, zero page-level horizontal or vertical scroll.
* **Section 1 (Left):** Recommendation settings and live data ingestion panel (`overflow-y: auto`).
* **Section 2 (Right):** Proactive conversational sous-chef panel with fixed header, scrollable chat message feed, and bottom input dock.

---

## Containers

* **Desktop Shell Container:** Max width `1600px`, margin `0 auto`, padding `0 24px`.
* **Section Card Container:** Background `#FFFFFF`, border `1px solid #E5E7EB`, border-radius `14px`, height `100%`.
* **Mobile Modal Sheet (Screen 1 Cart):** Width `100%`, max-width `420px`, border-radius `24px 24px 0 0` on mobile or `20px` floating centered on tablet/desktop.
* **Full-Screen Modal (Screen 2 Celebration):** Viewport width `100vw`, height `100vh`, fixed overlay.

---

## Margins

* Card Vertical Separation: `16px`
* Chat Bubble Spacing: `12px`
* Form Block Bottom Margin: `14px`
* Dish Section Margin inside Cart: `18px`

---

## Padding

* Main Section Interior: `20px`
* Chat Speech Bubble: `12px 16px`
* Mobile Cart Item Row: `10px 12px`
* Primary Button: `12px 20px`
* Input Field Interior: `10px 14px`

---

## Breakpoints

* `sm`: `640px` (Mobile viewport target for Screen 1 and Screen 2)
* `md`: `768px` (Tablet view)
* `lg`: `1024px` (Laptop / desktop split workbench target)
* `xl`: `1280px` (High-resolution split workbench target)

---

## Responsive Design

* On screens `>= 1024px`, Section 1 (Reviewer Levers) and Section 2 (Chat Interface) render simultaneously side-by-side in equal halves.
* On screens `< 1024px`, the system renders a segmented switcher `[🎛️ Settings Levers] | [💬 Chat with Zest]`.
* Screen 1 (Express Cart) and Screen 2 (Order Placed) are formatted exclusively as mobile screens (`390px` portrait ratio).

---

## Navigation

* **Global Top Bar:** Brand badge `Zest 🧑‍🍳`, dark store connectivity status indicator (`● Active - 10 Min Delivery Connected`), active user persona label, and reset button.
* **Chat Starter Carousel:** Horizontal scrollable prompt pills directly below chat header.

---

## Headers

* **Workbench Panel Header:** Height `48px`, background `#FFFFFF`, border-bottom `1px solid #E5E7EB`, title font `text-base`, `font-semibold`.
* **Cart Modal Header:** Centered title `QuickMart Express Cart`, back button left (`←`), dismiss button right (`✕`).

---

## Footers

* **Section 2 Chat Input Footer:** Pinned bottom bar, background `#FFFFFF`, border-top `1px solid #E5E7EB`, holding the upload image button, input text box, and send button.
* **Cart Modal Sticky Footer:** Pinned bottom bar, padding `16px 20px`, holding subtotal and primary `⚡ Buy Now` button.

---

## Buttons

### Primary Action Button (`Buy Now`, `Send`)
* Background: `#381E72` (Deep Violet)
* Hover Background: `#2C1659`
* Active Background: `#231048`
* Text: `#FFFFFF`, `font-semibold`, `text-sm`
* Border Radius: `10px`
* Height: `44px` (`48px` on mobile cart footer)

### Secondary Outline Button
* Background: `#FFFFFF`
* Border: `1px solid #D1D5DB`
* Text: `#374151`, `font-medium`
* Hover Background: `#F9FAFB`

### Icon Action Button (`Upload Image`, `Delete 🗑️`)
* Background: `transparent`
* Text: `#6B7280`
* Hover Text: `#381E72` (or `#DC2626` for trash)
* Dimensions: `38px x 38px`

---

## Icons

* **Library:** Lucide Monoline SVG Icons, stroke width `1.75px`.
* **Key Icons:**
  * `Image` / `Camera`: Upload food/fridge image.
  * `Send`: Submit message prompt.
  * `Trash2`: Remove cart item / dish.
  * `Plus` / `Minus`: Quantity adjusters.
  * `CheckCircle2` / `BadgeCheck`: Order confirmed seal.
  * `Bike`: Delivery rider progress tracker.

---

## Images

* **Food Thumbnails (Express Cart):** Dimensions `48px x 48px`, border-radius `8px`, border `1px solid #E5E7EB`, object-fit `cover`.
* **Uploaded Fridge Photos:** Dimensions `140px x 90px`, border-radius `10px`, border `1px solid #E5E7EB`.
* **Dish Suggestion Cards:** Dimensions `80px x 80px`, border-radius `10px`, object-fit `cover`.

---

## Illustrations

* **Delivery Rider Icon (Screen 2):** Minimalist line-and-fill scooter rider illustration with motion path dots.
* **Empty Cart Illustration:** Minimal outline grocery basket with dashed placeholder items.

---

## Logos

* **Brand Wordmark:** `Zest 🧑‍🍳` set in `Plus Jakarta Sans`, weight `700`, font size `18px`, color `#111827`, subtitle `QuickMart AI Sous-Chef`.

---

## Borders

* Standard Structural Borders: `1px solid #E5E7EB`
* Selected / Active Card Border: `1.5px solid #381E72`
* Inactive Item Border: `1px dashed #D1D5DB`
* Focus Ring: `2px solid #381E72` with `2px` offset

---

## Border Radius

* `rounded-xs`: `4px` (Price chips, status indicators)
* `rounded-sm`: `6px` (Quantity stepper controls, input badges)
* `rounded-md`: `8px` (Food thumbnail images, dropdown triggers)
* `rounded-lg`: `12px` (Cards, chat bubbles, prompt chips)
* `rounded-xl`: `16px` (Desktop panel containers)
* `rounded-2xl`: `24px` (Mobile modal sheets)
* `rounded-full`: `9999px` (Pill chips, avatar circles)

---

## Shadows

* `shadow-sm`: `0 1px 2px rgba(0, 0, 0, 0.04)`
* `shadow-card`: `0 2px 6px -1px rgba(0, 0, 0, 0.06), 0 1px 3px -1px rgba(0, 0, 0, 0.03)`
* `shadow-modal`: `0 20px 35px -5px rgba(0, 0, 0, 0.15), 0 10px 15px -5px rgba(0, 0, 0, 0.05)`

---

## Elevation

* **Level 0 (Canvas):** `#F8F9FA`
* **Level 1 (Cards & Workbench Panels):** `#FFFFFF`, `shadow-sm`
* **Level 2 (Dropdowns, Floating Chips):** `#FFFFFF`, `shadow-card`
* **Level 3 (Screen 1 Cart Modal):** `#FFFFFF`, `shadow-modal`
* **Level 4 (Screen 2 Order Placed Full-Screen):** `#1E0A3C`, z-index `100`

---

## Backgrounds

* Desktop App Canvas: `#F8F9FA`
* Section Panels: `#FFFFFF`
* User Chat Bubble: `#381E72` (White text)
* Bot Chat Bubble: `#F1F3F5` (Dark charcoal text `#111827`)
* Inactive / Dimmed Ingredient Row: `#F9FAFB`
* Screen 2 Full Overlay: `#1E0A3C` gradient

---

## Cards

* **Dish Group Card (Inside Cart):** Background `#FFFFFF`, border `1px solid #E5E7EB`, border-radius `12px`, padding `14px`. Includes dish title, total dish cost, dish trash icon, and ingredient rows.
* **Recommendation Summary Card (Chat):** Background `#F3EEFC`, border-left `4px solid #381E72`, border-radius `8px`, padding `12px`.

---

## Forms

* Structured vertically within collapsible accordion drawers in Section 1.
* Field Labels: `text-xs`, `font-semibold`, uppercase, tracking `0.05em`, color `#374151`.

---

## Input Fields

* **Chat Text Box (Section 2):**
  * Height: `44px`
  * Background: `#FFFFFF`
  * Border: `1px solid #D1D5DB`
  * Border Radius: `10px`
  * Padding: `0 14px`
  * Controls: Accompanied strictly by the `Upload Image` action button and the `Send` button.

---

## Dropdowns

* Native/Custom Select Box: Height `40px`, background `#FFFFFF`, border `1px solid #D1D5DB`, border-radius `8px`, font `text-sm`, padding `0 12px`.

---

## Checkboxes

* Dimensions: `18px x 18px`, border `1.5px solid #D1D5DB`, border-radius `4px`.
* Checked state: Background `#381E72`, check icon white.

---

## Radio Buttons

* Dimensions: `18px x 18px`, border `1.5px solid #D1D5DB`, border-radius `9999px`.
* Active State: Outer border `#381E72`, inner center dot `#381E72` (`8px`).

---

## Toggles

* Track: Width `42px`, height `22px`, border-radius `9999px`, background `#D1D5DB`.
* Active Track: Background `#381E72`.
* Thumb: Width `18px`, height `18px`, background `#FFFFFF`, translate `20px` when active.

---

## Modals

* **Screen 1 (Express Cart):** Modal bottom sheet overlay with backdrop scrim `rgba(17, 24, 39, 0.45)` with `backdrop-filter: blur(4px)`.
* **Screen 2 (Order Placed):** Full-screen viewport modal takeover.

---

## Dialogs

* Mobile Dialog Dimensions: Max-width `420px`, full vertical height on mobile viewports, centered container on desktop viewports.

---

## Tooltips

* Dark slate bubble (`#111827`), white text, `text-xs`, padding `6px 10px`, border-radius `6px`, `200ms` hover trigger.

---

## Popovers

* Contextual popover for manual SKU substitution: White card, `shadow-card`, border `1px solid #E5E7EB`, padding `12px`.

---

## Alerts

* **Server Struggling Error Alert:**
  * Background: `#FEF2F2`
  * Border: `1px solid #FCA5A5`
  * Text Color: `#DC2626`
  * Copy: *"Your food will be ready but seems like our servers are struggling. We will be back shortly"*

---

## Notifications

* Toast notifications anchored top-right: Height `44px`, background `#111827`, text `#FFFFFF`, border-radius `8px`, auto-dismiss `3500ms`.

---

## Badges

* **Connectivity Badge:** Green dot (`#10B981`) with copy `Active - 10 Min Delivery Connected`, background `#ECFDF5`, border `1px solid #A7F3D0`.
* **Cart Count Badge:** Deep violet pill (`#381E72`), white text, `font-semibold`.

---

## Tags

* **In Kitchen (Detected):** Background `#ECFDF5`, text `#065F46`, border `1px solid #A7F3D0`.
* **Missing (Added):** Background `#FEF2F2`, text `#991B1B`, border `1px solid #FECACA`.
* **Inactive / Dimmed:** Background `#F3F4F6`, text `#6B7280`, border `1px solid #E5E7EB`.

---

## Tabs

* Segmented controller: Background `#F1F3F5`, padding `3px`, border-radius `8px`. Active tab white with `shadow-sm`, text `#381E72`.

---

## Accordions

* Section 1 Collapsible Groups: Header height `48px`, font-size `text-sm`, font-weight `600`, chevron icon rotating 180° on expansion.

---

## Tables

* Live Ingested Ingredients Database Inspector: Clean row height `42px`, alternating row hover `#F9FAFB`, header background `#F8F9FA`.

---

## Lists

* Cart Ingredient Item Rows:
  * Left: Food image thumbnail (`48px x 48px`).
  * Center: Product name, unit pack size, price.
  * Right: Stepper `-[ 1 ]+` and trash icon `🗑️`.

---

## Pagination

* Not used in infinite chat stream; simple `Page 1 of 2` stepper in manual catalog inspector.

---

## Breadcrumbs

* Simple locator header in Section 1: `Reviewer Workbench > Active Persona Levers`.

---

## Search

* In-catalog override search: Height `36px`, border `1px solid #D1D5DB`, search magnifying glass icon left, clear button right.

---

## Filters

* Dietary Filter Chips: `[All]`, `[Pure Veg]`, `[Jain]`, `[Gluten-Free]`, `[Keto]`.

---

## Loading States

* **Bot Thinking Bubble:** Three pulsating dots (`#6B7280`) inside a `#F1F3F5` chat bubble.
* **Image Upload Analysis:** Shimmer skeleton container with animated gradient.

---

## Empty States

* **Empty Cart:** Centered illustration of empty shopping basket, copy *"Your cart is empty. Pick a recipe or paste a YouTube link to get started!"*.

---

## Error States

* Offline / Server Timeout Toast:
  > *"Your food will be ready but seems like our servers are struggling. We will be back shortly"*

---

## Success States

* Inline green confirmation chip: *"Ingredients added to cart ✅"*.

---

## Hover States

* Buttons: Background shifts 5% darker.
* Sliders: Thumb border thickens, value tooltip displays floating above.

---

## Focus States

* High-contrast focus outline: `2px solid #381E72`, offset `2px`.

---

## Active States

* Buttons: Scale `transform: scale(0.98)`, transition `50ms ease`.

---

## Disabled States

* Opacity: `0.40`, `cursor: not-allowed`, pointer-events disabled.

---

## Animations

* Modal Entry: `200ms cubic-bezier(0.16, 1, 0.3, 1)` slide-up.
* Screen 2 Full-Screen Takeover: Instant display, stays active for exactly **3000ms**, then auto-collapses.

---

## Transitions

* Global interactive element transition: `all 150ms ease-in-out`.

---

## Microinteractions

* Quantity increment: Stepper number scales up `1.15x` momentarily before returning to default size.
* Prompt pill click: Pill depresses slightly and injects message into chat stream instantly.

---

## Accessibility

* Complies with **WCAG 2.1 AA** standards.
* Proper ARIA live regions on the incoming chat message stream (`aria-live="polite"`).
* Interactive controls support standard keyboard navigation (`Tab`, `Space`, `Enter`, `Escape`).

---

## Contrast Ratios

* Primary Deep Violet (`#381E72`) on White (`#FFFFFF`): `11.8:1` (Exceeds WCAG AAA `7:1`).
* Primary Text (`#111827`) on White (`#FFFFFF`): `16.1:1` (Exceeds WCAG AAA).
* Secondary Text (`#374151`) on White (`#FFFFFF`): `9.4:1` (Exceeds WCAG AAA).
* Dimmed/Inactive Text (`#9CA3AF`) on `#F9FAFB`: `2.8:1` (Intentionally accessible as inactive state accompanied by explanatory text).

---

## Keyboard Navigation

* `Tab`: Advances sequentially through left panel sliders $\rightarrow$ right chat input $\rightarrow$ action buttons.
* `Esc`: Closes Screen 1 (Express Cart) modal immediately.
* `Enter`: Submits message in chat box; triggers `Buy Now` when focused.

---

## Screen Reader Support

* `aria-label="Upload food or fridge image"` on the chat input attachment button.
* `aria-disabled="true"` on dimmed duplicate cart lines with `aria-describedby` referencing primary dish ownership.

---

## Component Variants

### Starter Prompt Pill Variants
* `YouTube Link Pill`: Prefixed with video player icon.
* `Upload Photo Pill`: Prefixed with camera icon.
* `Text Recipe Pill`: Prefixed with cutlery icon.

---

## Component States

1. `Default`
2. `Hover`
3. `Focus`
4. `Active`
5. `Disabled`
6. `Loading / Skeleton`

---

## Design Tokens

```json
{
  "color": {
    "canvas": "#F8F9FA",
    "surface": "#FFFFFF",
    "surfaceSubtle": "#F1F3F5",
    "border": "#E5E7EB",
    "textPrimary": "#111827",
    "textSecondary": "#374151",
    "textMuted": "#6B7280",
    "brandPrimary": "#381E72",
    "brandPrimaryHover": "#2C1659",
    "statusSuccess": "#10B981",
    "statusError": "#DC2626",
    "celebrationBg": "#1E0A3C"
  },
  "spacing": {
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "6": "24px",
    "8": "32px"
  },
  "radius": {
    "sm": "6px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "full": "9999px"
  },
  "shadow": {
    "card": "0 2px 6px -1px rgba(0, 0, 0, 0.06)",
    "modal": "0 20px 35px -5px rgba(0, 0, 0, 0.15)"
  }
}
```

---

## Design Principles

1. **Deterministic Feedback:** Reviewer adjustments to levers on the left immediately update the recommendation logic on the right.
2. **Transparent Deduplication:** Never double-charge users for shared ingredients; make active vs. inactive ownership clear.
3. **Frictionless Action:** Section 2's input is focused on quick food communication—supporting natural text and direct image uploads.
4. **Delightful Gratification:** Celebrate completed orders instantly with clear delivery partner expectations.

---

## User Flows

### Flow 1: YouTube Recipe Link $\rightarrow$ Auto-Cart $\rightarrow$ Mobile Checkout
1. Reviewer configures User Persona Levers in Section 1.
2. User taps starter prompt `"📺 YouTube: Paneer Butter Masala"`.
3. System extracts transcript ingredients; displays cart preview link in chat.
4. User taps `"🛒 View Cart"`. Screen 1 (Express Cart Mobile View) opens.
5. User reviews ingredients with food images and taps `"⚡ Buy Now"`.
6. Screen 2 (Order Placed) takes over for 3 seconds, confirming rider dispatch in 10 mins.

### Flow 2: Fridge Image Upload $\rightarrow$ Missing Items Delta $\rightarrow$ Deduplication
1. User clicks the `Upload Image` button in the chat box and uploads a photo of paneer and peppers.
2. Vision model identifies items; bot suggests 3 dishes.
3. User selects *Kadai Paneer* and adds *Garlic Butter Naan*.
4. Express Cart modal opens:
   * *Amul Salted Butter* is active and priced under Dish 1 (*Paneer Butter Masala*).
   * *Amul Salted Butter* is dimmed and inactive under Dish 2 (*Garlic Butter Naan*).
   * Removing butter from Dish 1 automatically transfers active ownership to Dish 2.

---

## Wireframes

### Main Screen Wireframe (Single Web Window: 50/50 Split)
```
+---------------------------------------------------------------------------------------------------------+
|  Zest 🧑‍🍳   QuickMart AI Sous-Chef             ● Active - 10 Min Delivery Connected      [Reset Levers]  |
+----------------------------------------------------+----------------------------------------------------+
| SECTION 1: RECOMMENDATION LEVERS                   | SECTION 2: CHAT WITH ZEST                          |
|                                                    |                                                    |
| v User Persona & Dietary Levers (Hard Guardrails)  | [📺 YouTube Link]  [📸 Upload Photo] [🍝 Pasta]    |
|   Gender: [Female        v]                        |                                                    |
|   Diet:   [Pure Veg      v]                        | -------------------------------------------------- |
|   Faith:  [Hindu Regular v]                        | [🧑‍🍳 Zest]: Hey there! What's cooking today?      |
|   Diet:   [Keto          v]                        |                                                    |
|                                                    | [👤 User]: [Uploaded_Fridge_Items.jpg]             |
| v Historical Category Affinity                     |                                                    |
|   Bakery & Breads: [--------O---] 0.85             | [🧑‍🍳 Zest]: Spotted Paneer & Peppers! Pick:       |
|   Dairy & Raita:   [--------O---] 0.85             | (1) Kadai Paneer  (2) Tikka Wrap  (3) Stir-Fry     |
|   Desserts:        [----O-------] 0.40             |                                                    |
|   Salads:          [-------O----] 0.75             | [👤 User]: Let's make Kadai Paneer                 |
|   Protein:         [------O-----] 0.60             |                                                    |
|                                                    | [🧑‍🍳 Zest]: Added 3 missing items (Rs 139)!      |
| v Database & Extracted Ingredients                 | [🛒 View Cart (3 items • Rs 139)]                  |
|   Source: YouTube / Vision Ingestion               |                                                    |
|   [Paneer (Kitchen)] [Kadai Masala (Added)]        | -------------------------------------------------- |
|   [Butter (Kitchen)] [Coriander (Added)]           | [ [Upload Image] | Type a message here... | [Send] ]|
+----------------------------------------------------+----------------------------------------------------+
```

### Screen 1: Mobile Express Cart Wireframe
```
+---------------------------------------------------+
|  [←]        QuickMart Express Cart            [✕] |
+---------------------------------------------------+
|  Dish 1: Paneer Butter Masala (₹198)          [🗑️]|
|  +-----+ Amul Paneer (200g)                       |
|  | IMG | Price: ₹95      Qty: - [ 1 ] +       [🗑️]|
|  +-----+                                          |
|  +-----+ Amul Salted Butter (100g)                |
|  | IMG | Price: ₹58      Qty: - [ 1 ] +       [🗑️]|
|  +-----+                                          |
|                                                   |
|  Dish 2: Garlic Butter Naan (₹120)            [🗑️]|
|  +-----+ Garlic Kit                               |
|  | IMG | Price: ₹40      Qty: - [ 1 ] +       [🗑️]|
|  +-----+                                          |
|  +-----+ Amul Salted Butter (100g)                |
|  | IMG | Inactive / Dimmed                        |
|  +-----+ Already included in Paneer Butter Masala |
+---------------------------------------------------+
|  [                ⚡ Buy Now                      ] |
+---------------------------------------------------+
```

### Screen 2: Mobile Order Placed Full-Screen Wireframe
```
+---------------------------------------------------+
|                                                   |
|                      [ ✓ ]                        |
|                  Order Placed!                    |
|                                                   |
|             Our delivery partner will             |
|                 see you in 10mins                 |
|                                                   |
|                    [ 🛵 ... ]                     |
|        Packed  →  Dispatched  →  Arriving Shortly |
|                                                   |
+---------------------------------------------------+
```

---

## Screen Specifications

* **Screen 0 (Main Split Workbench):** Desktop viewport `100vw x 100vh`, split into two `50%` columns with independent scrolling.
* **Screen 1 (QuickMart Express Cart):** Mobile modal view, target aspect ratio `9:19.5` (`390px x 844px`), display food image thumbnails, quantity adjusters, and active/inactive deduplication states.
* **Screen 2 (Order Placed Confirmation):** Full mobile viewport takeover, dark violet fluid gradient, centered checkmark seal, delivery partner status progression, active duration exactly **3 seconds**.

---

## Interaction Patterns

### Cart Deduplication Ownership Rule
1. When Dish 1 and Dish 2 both require *Amul Salted Butter (100g)*:
   * Dish 1 line is marked **Active** (Priced: `₹58`, Quantity stepper enabled, trash button active).
   * Dish 2 line is marked **Inactive / Dimmed** (Display text: *"Inactive / Dimmed - Already included in Dish 1"*, price not added to subtotal).
2. If user clicks the trash icon on the active butter line in Dish 1:
   * Dish 1 line is removed.
   * Dish 2 line automatically switches from **Inactive** to **Active** (Priced: `₹58`).
   * Total price remains mathematically accurate without user prompts.

### Multi-Sourcing Quantity Rule
* Separate recipe requirements maintain discrete lines (e.g., Dish 1 requires 200g Paneer, Dish 2 requires 200g Paneer $\rightarrow$ cart lists two distinct 200g packets).

---

## Data Visualization

* Scored candidate pairing charts in Section 1 provide immediate visual transparency into how persona, history, and trends impact the bot's upsell choices.

---

## Charts

* **Recommendation Score Breakdown Chart:** Stacked horizontal bar chart in Section 1 displaying match contributions across History (Deep Violet), Trend (Amber), Culinary Co-occurrence (Emerald), and Persona Guardrail (Slate).

---

## Graphs

* Real-time demand sparkline embedded inside the Market Trend accordion drawer (`+14% order surge`).

---

## Responsive Behavior

* On viewports `>= 1024px`, both sections display concurrently in a 50/50 split.
* On viewports `< 1024px`, top segmented control allows toggling between Section 1 and Section 2.
* Screen 1 and Screen 2 are rendered as dedicated mobile viewport overlays.

---

## Dark Mode

* Screen 2 (Order Placed) operates exclusively in Dark Mode (`#1E0A3C` gradient canvas, `#FFFFFF` high-contrast typography, violet status tracker).

---

## Light Mode

* Section 1, Section 2, and Screen 1 (Express Cart) operate in Light Mode (`#F8F9FA` canvas, `#FFFFFF` cards, `#111827` primary text, `#381E72` deep violet brand accents).

---

## Design Constraints

1. **Single Web Window:** Section 1 and Section 2 must exist within the exact same browser screen without splitting across browser windows.
2. **Simplified Chat Input:** The chat text box must contain only the image upload button, the text input, and the send action.
3. **Visual Prototype Semantics:** The `Buy Now` trigger is purely a prototype demonstration and triggers the 3-second celebration modal.
4. **Automatic Reset:** Refreshing the browser resets all levers and cart lines back to clean default states.

---

## Content Guidelines

* Conversational, culinary-focused, friendly, and concise.
* Avoid mechanical status text; phrase suggestions around taste pairings and quick preparation.

---

## UX Writing

* **Chat Greeting:** *"Hey there! I'm Zest, your AI cooking assistant. Paste a YouTube recipe link, describe what's in your fridge, or upload a photo of your ingredients to start!"*
* **Missing Items Nudge:** *"I've identified Paneer, Peppers, and Onions. You can make Kadai Paneer! I've added 3 missing items (₹139) to your cart."*
* **Cart Deduplication Note:** *"Inactive / Dimmed - Already included in Paneer Butter Masala"*
* **Celebration Banner (Screen 2):** *"Order Placed! Our delivery partner will see you in 10mins"*
* **Server Fallback Error:** *"Your food will be ready but seems like our servers are struggling. We will be back shortly"*

---

## Platform-Specific Guidelines

* **Web Desktop:** Custom slim violet scrollbars (`::-webkit-scrollbar { width: 6px; }`, thumb `#D1D5DB`, hover `#381E72`).
* **Mobile Web Viewports:** Viewport heights enforced with `100dvh` to prevent mobile address bar clipping.

---

## Design References

* **Fynd Clean Commerce UI:** High-contrast violet and pale gray accents with minimalist white cards.
* **Blinkit & Swiggy Instamart:** 10-minute grocery dispatch speed, deduplicated recipe baskets, and rider status bars.

---

## Asset Guidelines

* Food item thumbnails must be optimized WebP format, square `1:1`, resolution `96x96px` (displayed at `48x48px` for retina sharpness).
* All interface icons must be inline SVGs.

---

## Spacing Scale

* `4px`: Micro padding, badge offsets
* `8px`: Inline icon-to-label gaps
* `12px`: Chat bubble padding
* `16px`: Form row gap, card internal padding
* `20px`: Panel padding
* `24px`: Split-screen gutter gap
* `32px`: Section separation margins

---

## Z-Index

* `z-0`: Background Canvas
* `z-10`: Split Panels & Inner Scrollables
* `z-20`: Pinned Top Bar & Bottom Chat Input Dock
* `z-40`: Modal Backdrop Overlay
* `z-50`: Screen 1 (Express Cart Mobile Sheet)
* `z-100`: Screen 2 (Order Placed Full-Screen Celebration Modal)

---

## Opacity

* Inactive / Dimmed Cart Row: `0.45`
* Disabled Button: `0.40`
* Backdrop Scrim: `0.45`

---

## Aspect Ratios

* Screen 1 & Screen 2 Mobile Viewport: `9:19.5` (`390px x 844px`)
* Food Thumbnails: `1:1`
* Fridge Upload Preview: `16:10`

---

## Image Treatments

* Clean border `1px solid #E5E7EB`, border-radius `8px`, natural color saturation, zero heavy drop shadows.

---

## Iconography

* Lucide Monoline SVG icons rendered at `18px` with stroke width `1.75px` in `#6B7280` or brand violet `#381E72`.

---

## Design System Version

* **Name:** Zest Minimalist Workbench Design System
* **Version:** `v3.0.0`
* **Status:** Approved for Google Stitch Prototype & GitHub Repository

---

## Change Log

### [v3.0.0]
* Updated color palette to deep violet (`#381E72`), high-contrast light neutrals (`#F8F9FA`, `#FFFFFF`), and emerald status green (`#10B981`) matching reference styling.
* Restricted Section 2 chat box to strictly include an image upload button, text field, and send action.
* Updated Screen 1 (QuickMart Express Cart) to display inline food images, dish subtotals, quantity adjusters, and active/inactive deduplication states.
* Updated Screen 2 (Order Placed) to a full mobile celebration screen with the exact copy: *"Order Placed! Our delivery partner will see you in 10mins"* and delivery tracking progression.
* Re-ordered all sections to match the exact 92-section specification format.