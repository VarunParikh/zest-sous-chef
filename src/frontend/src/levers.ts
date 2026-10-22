// Lever labels and grouping from docs/inputs/RecommendationSettingsPanel.md (C10: the panel wins over the mockup).
import type { LeverSet, Weights } from "./api/types";

export const WEIGHT_LABELS: { key: keyof Weights; label: string; share: string }[] = [
  { key: "culinary_pairing", label: "Culinary Pairing Weight", share: "s_p" },
  { key: "purchase_history", label: "User Purchase History Weight", share: "s_h" },
  { key: "market_trend", label: "Market Trend & Velocity Weight", share: "s_t" },
  { key: "persona_gourmet", label: "Persona & Gourmet Boost Weight", share: "s_g" },
];

export const HISTORY_LABELS: { key: keyof LeverSet["history"]; label: string }[] = [
  { key: "bakery", label: "Bakery & Breads Affinity" },
  { key: "dairy", label: "Dairy & Raita Affinity" },
  { key: "desserts", label: "Desserts & Sweets Affinity" },
  { key: "salads", label: "Salads & Healthy Drinks Affinity" },
  { key: "kebabs", label: "Kebabs & High-Protein Affinity" },
];

export const TREND_LABELS: { key: keyof LeverSet["trends"]; label: string }[] = [
  { key: "weekend_indulgence", label: "Weekend Indulgence & Festive Surge" },
  { key: "cooling_drinks", label: "Cooling Drinks & Fresh Sides Trend" },
];

/** ŵ = w / Σw (FR-08); all zero restores the defaults at session start (the server sends the notice). */
export function shares(w: Weights, defaults: Weights): { shares: Record<string, number>; restored: boolean } {
  const raw = WEIGHT_LABELS.map((x) => w[x.key]);
  const restored = raw.every((v) => v === 0);
  const use = restored ? WEIGHT_LABELS.map((x) => defaults[x.key]) : raw;
  const total = use.reduce((a, b) => a + b, 0);
  return { shares: Object.fromEntries(WEIGHT_LABELS.map((x, i) => [x.share, use[i] / total])), restored };
}

/** Lever equality for the banner (FR-03); specialised-diet order does not matter, as in the server's hash. */
export function sameLevers(a: LeverSet | null, b: LeverSet | null): boolean {
  if (!a || !b) return true;
  const norm = (l: LeverSet) => JSON.stringify({ ...l, specialized_diets: [...l.specialized_diets].sort() });
  return norm(a) === norm(b);
}

export const clone = (l: LeverSet): LeverSet => JSON.parse(JSON.stringify(l));

/** Plain-language lever help (FR-122; Conversation Design §6.7). Rule: removes options. Preference: re-ranks them. */
export type LeverTag = "Rule" | "Preference";
export const REMOVED = "Dishes that break it are removed before ranking and never suggested.";
const HISTORY_TIP = "How often you have bought from this category before (mock history).";
const TREND_TIP = "How strongly this week's store trends count (mock trends).";
export const LEVER_HELP: Record<string, { tag: LeverTag; text: string }> = {
  "Culinary Pairing Weight": { tag: "Preference", text: "How much Zest favours dishes that match your request and pair well with it." },
  "User Purchase History Weight": { tag: "Preference", text: "How much your (mock) past purchases count." },
  "Market Trend & Velocity Weight": { tag: "Preference", text: "How much Zest favours what is popular in the store right now." },
  "Persona & Gourmet Boost Weight": { tag: "Preference", text: "How much your style settings below (gourmet, organic) count." },
  "Probable Gender": { tag: "Preference", text: "A small preference: Female slightly favours iron- and calcium-rich items, Male slightly favours high-protein items. It never removes a dish." },
  "Dietary Preference": { tag: "Rule", text: REMOVED },
  "Religious / Cultural Beliefs": { tag: "Rule", text: REMOVED },
  "Specialized Diet Mode": { tag: "Rule", text: "Each diet you tick removes dishes that break it before ranking; they are never suggested." },
  "Gourmet / Imported Food Affinity": { tag: "Preference", text: "Nudges Zest towards gourmet and imported products." },
  "Artisanal & Organic Preference": { tag: "Preference", text: "Nudges Zest towards artisanal and organic products." },
  ...Object.fromEntries(HISTORY_LABELS.map((h) => [h.label, { tag: "Preference" as LeverTag, text: HISTORY_TIP }])),
  ...Object.fromEntries(TREND_LABELS.map((t) => [t.label, { tag: "Preference" as LeverTag, text: TREND_TIP }])),
  "Max Companion Add-on Price Cap": { tag: "Rule", text: "Add-on suggestions never cost more than this." },
  "Hide out-of-stock items (stock filter)": { tag: "Rule", text: "When on, out-of-stock items are removed before ranking and never carted." },
};
