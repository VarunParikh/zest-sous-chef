// Types mirroring the backend models (API Spec v0.6; backend.flows.cards, backend.session.levers).

export interface Weights {
  culinary_pairing: number;
  purchase_history: number;
  market_trend: number;
  persona_gourmet: number;
}

export interface LeverSet {
  weights: Weights;
  gender: string;
  diet: string;
  faith: string;
  specialized_diets: string[];
  gourmet_affinity: number;
  artisanal_organic: number;
  history: { bakery: number; dairy: number; desserts: number; salads: number; kebabs: number };
  trends: { weekend_indulgence: number; cooling_drinks: number };
  business: { price_cap_inr: number; stock_filter: boolean };
}

export interface LeverConfig {
  defaults: LeverSet;
  options: { gender: string[]; diet: string[]; faith: string[]; specialized_diets: string[] };
  ranges: Record<string, { min: number; max: number }>;
  default_shares: Record<string, number>;
  presets: { name: string; levers: LeverSet; summary: string; tag: string | null }[];
}

export interface ChoiceOption { value: string; label: string }
export interface SwapOption { dish_id: string; name: string }
export interface Breakdown {
  components: Record<string, number>;
  contributions: Record<string, number>;
  weights_effective: Record<string, number>;
  final: number;
}

/** The "Why this?" payload (FR-63): a reason always; scores when the suggestion has one. */
export interface WhyInfo extends Partial<Breakdown> {
  kind?: "dish" | "addon" | "photo" | "alternative" | "nearest";
  reason?: string;
  drivers?: string[];
  alternatives?: { dish_id: string; name: string; final: number }[];
  anchor?: string;
  retrieval?: { curated_strength: number | null; curated_rank: number | null; vector_rank: number | null; fused_rank: number };
  used?: string[];
}

export type Card =
  | { type: "starter_chips"; chips: string[] }
  | { type: "help"; examples: { label: string; kind: "send" | "sample"; value: string }[]; note: string; tour: boolean }
  | { type: "dish_added"; suggestion_id: string; dish_id: string; dish_name: string; reason: string; line_count: number; dish_total_inr: number }
  | { type: "swap_options"; suggestion_id: string; options: SwapOption[] }
  | { type: "undo"; suggestion_id: string }
  | { type: "why_this"; suggestion_id: string; breakdown: WhyInfo | null }
  | { type: "clarify"; question_id: string; prompt: string; options: ChoiceOption[] }
  | { type: "confirm"; confirm_id: string; prompt: string; options: ChoiceOption[] }
  | { type: "addon_suggestion"; suggestion_id: string; item: { name: string; variant: string | null; price_inr: number }; reason: string }
  | { type: "substitution"; substitution_id: string; from_item: string; to_item: string; price_delta_inr: number; flavour_note: string }
  | { type: "photo_consent"; notice: string }
  | { type: "sample_photos"; photos: { id: string; caption: string; label: string }[] }
  | { type: "notice"; level: "info" | "warning"; template_id: string; text: string }
  | { type: "cart_summary"; item_count: number; subtotal_inr: number };

export interface Message {
  message_id: string;
  role: "user" | "assistant" | "system";
  template_id: string | null;
  text: string;
  cards: Card[];
}

export interface CartLine {
  line_id: string;
  ingredient_name: string;
  variant_id: string;
  variant_name: string;
  packs: { sku_id: string; count: number; pack: string }[];
  price_inr: number;
  priced: boolean;
  shared_from_line_id: string | null;
  estimated: boolean;
  reason: string;
  alternative_variant_ids: string[];
  in_stock: boolean;
  quantity: number;
  icon: string;
}

export interface CartDish {
  cart_dish_id: string;
  dish_id: string | null;
  name: string;
  course: string | null;
  dish_total_inr: number;
  lines: CartLine[];
}

export interface CartView { dishes: CartDish[]; item_count: number; subtotal_inr: number }

export interface TurnResponse {
  turn_id: string;
  messages: Message[];
  cart: CartView;
  cart_changed: boolean;
  pending: Record<string, unknown> | null;
  suggestions: { suggestion_id: string; type: string; candidate_id: string; rank: number }[];
  notices: Extract<Card, { type: "notice" }>[];
  fallbacks_used: string[];
  levers_changed_since_snapshot: boolean;
}

export interface SessionResponse { session_id: string; snapshot_hash: string; persona_label: string; turn: TurnResponse }

export interface Order {
  order_id: string;
  subtotal_inr: number;
  placed_at: string;
  message: { template_id: string; text: string };
  collapse_after_s: number;
}

export interface InspectorRow {
  candidate_id: string;
  name: string;
  lexical_rank: number | null;
  vector_rank: number | null;
  vector_distance: number | null;
  fused_rank: number;
  eligible: boolean;
  filtered_by: string[];
  components: Record<string, number>;
  final: number;
}

export interface AddonRow extends InspectorRow { curated_rank: number | null; curated_strength: number | null }
export interface Inspector {
  rows: InspectorRow[];
  shown: string[];
  weights_effective: Record<string, number>;
  addon?: { anchor: string; rows: AddonRow[]; shown: string[] };  // FR-119
}

export interface ApiErrorBody {
  code: string;
  template_id: string | null;
  user_message: string;
  retryable: boolean;
  details: Record<string, unknown>;
}

export const EMPTY_CART: CartView = { dishes: [], item_count: 0, subtotal_inr: 0 };
