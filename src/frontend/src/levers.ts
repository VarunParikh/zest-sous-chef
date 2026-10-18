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
