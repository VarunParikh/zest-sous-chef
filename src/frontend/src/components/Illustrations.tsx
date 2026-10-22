// Cartoon chefs for the persona cards and icons for the specialised diets (FR-121, FR-122; Conversation Design
// UI-PERSONA, UI-DIET-ICONS; owner-approved mockup 2026-10-23). Decorative only: the card and label text carry the
// meaning, so every drawing is aria-hidden. Heads use non-skin colours; props come from the levers, never from a
// name, faith or ethnicity.
import type { ReactElement } from "react";
import type { LeverSet } from "../api/types";

type Prop = "leaf" | "dumbbell" | "clock" | "bowl" | "clipboard" | "spoon";
const HEADS = ["#CECBF6", "#9FE1CB", "#F5C4B3", "#B5D4F4", "#C0DD97", "#FAC775", "#F4C0D1"];
const INK = "#2C2C2A";
const PROP_INK = "#5F5E5A";

const hash = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);

/** The prop says what the persona eats or how they live (FR-121). */
export function personaProp(levers: LeverSet, tag: string | null): Prop {
  const s = levers.specialized_diets;
  if (s.includes("Vegan")) return "leaf";
  if (s.includes("Keto Diet") || s.includes("High-Protein Fitness")) return "dumbbell";
  if (s.includes("Intermittent Fasting / Low-GI")) return "clock";
  if (levers.diet !== "Non-Veg / Flexitarian") return "bowl";  // Jain or pure vegetarian
  return tag === "Control" ? "clipboard" : "spoon";
}

function PropShape({ prop }: { prop: Prop }) {
  switch (prop) {
    case "leaf":
      return <g><path d="M54 62 C50 52 56 45 65 45 C65 55 61 62 54 62 Z" fill="#639922" /><path d="M54 62 L63 48" stroke="#27500A" strokeWidth="1.3" /></g>;
    case "dumbbell":
      return <g fill={PROP_INK}><rect x="51" y="55" width="13" height="3" /><rect x="48" y="51" width="4" height="11" rx="1" /><rect x="63" y="51" width="4" height="11" rx="1" /></g>;
    case "clock":
      return <g><circle cx="58" cy="56" r="8" fill="#FFFFFF" stroke={PROP_INK} strokeWidth="2" /><path d="M58 51 V56 L61 58" stroke={PROP_INK} strokeWidth="2" strokeLinecap="round" fill="none" /></g>;
    case "bowl":
      return <g><path d="M48 54 H68 A10 9 0 0 1 48 54 Z" fill="#FAC775" stroke="#854F0B" strokeWidth="1.5" /><path d="M53 50 q2 -3 0 -6 M58 50 q2 -3 0 -6 M63 50 q2 -3 0 -6" stroke="#B4B2A9" strokeWidth="1.3" fill="none" /></g>;
    case "clipboard":
      return <g><rect x="50" y="46" width="15" height="19" rx="2" fill="#FFFFFF" stroke={PROP_INK} strokeWidth="1.8" /><path d="M53 52 H62 M53 56 H62 M53 60 H59" stroke={PROP_INK} strokeWidth="1.4" /></g>;
    default:
      return <g><ellipse cx="62" cy="50" rx="4" ry="5.5" fill="none" stroke={PROP_INK} strokeWidth="2" /><path d="M60 55 L52 64" stroke={PROP_INK} strokeWidth="2.6" strokeLinecap="round" /></g>;
  }
}

/** A friendly chef: coloured head, chef's hat, a smile, and the persona's prop. */
export function PersonaAvatar({ name, levers, tag, size = 52 }: { name: string; levers: LeverSet; tag: string | null; size?: number }) {
  const prop = personaProp(levers, tag);
  return (
    <svg width={size} height={size} viewBox="0 0 72 72" aria-hidden="true" data-avatar={prop} className="shrink-0">
      <circle cx="34" cy="42" r="20" fill={HEADS[hash(name) % HEADS.length]} />
      <ellipse cx="34" cy="20" rx="15" ry="8" fill="#FFFFFF" stroke="#B4B2A9" strokeWidth="1.5" />
      <rect x="23" y="20" width="22" height="8" rx="2" fill="#FFFFFF" stroke="#B4B2A9" strokeWidth="1.5" />
      <circle cx="27" cy="41" r="2.2" fill={INK} />
      <circle cx="41" cy="41" r="2.2" fill={INK} />
      <path d="M27 49 Q34 55 41 49" fill="none" stroke={INK} strokeWidth="2" strokeLinecap="round" />
      <PropShape prop={prop} />
    </svg>
  );
}

const DIET: Record<string, { bg: string; ink: string; draw: ReactElement }> = {
  "Standard / Balanced": { bg: "#E6F1FB", ink: "#185FA5",
    draw: <g fill="none" strokeWidth="1.8" strokeLinecap="round"><path d="M12 4 V19 M7 19 H17 M5 7 H19" /><path d="M5 7 L2.5 13 H7.5 Z M19 7 L16.5 13 H21.5 Z" /></g> },
  "Keto Diet": { bg: "#FAEEDA", ink: "#854F0B",
    draw: <path d="M12 3 C8 3 5.5 9 5.5 13.5 C5.5 17.5 8.5 20.5 12 20.5 C15.5 20.5 18.5 17.5 18.5 13.5 C18.5 9 16 3 12 3 Z" fill="none" strokeWidth="1.8" /> },
  "Intermittent Fasting / Low-GI": { bg: "#EEEDFE", ink: "#534AB7",
    draw: <g fill="none" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="8.5" /><path d="M12 7 V12 L15 14" /></g> },
  Vegan: { bg: "#EAF3DE", ink: "#3B6D11",
    draw: <g fill="none" strokeWidth="1.8" strokeLinecap="round"><path d="M5 19 C5 10 10 5 19 5 C19 14 14 19 5 19 Z" /><path d="M5 19 L13 11" /></g> },
  "Gluten-Free": { bg: "#FAEEDA", ink: "#854F0B",
    draw: <g fill="none" strokeWidth="1.8" strokeLinecap="round"><path d="M12 21 V6 M12 9 l-3 -2 M12 9 l3 -2 M12 13 l-3 -2 M12 13 l3 -2 M12 17 l-3 -2 M12 17 l3 -2" /><path d="M4 4 L20 20" /></g> },
  "High-Protein Fitness": { bg: "#FCEBEB", ink: "#A32D2D",
    draw: <g fill="none" strokeWidth="1.8" strokeLinecap="round"><path d="M8 12 H16 M5 8 V16 M8 7 V17 M16 7 V17 M19 8 V16" /></g> },
};

/** The icon beside a specialised-diet checkbox (FR-122). */
export function DietIcon({ diet }: { diet: string }) {
  const d = DIET[diet];
  if (!d) return null;
  return (
    <span aria-hidden="true" data-diet-icon={diet} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: d.bg }}>
      <svg width="18" height="18" viewBox="0 0 24 24" stroke={d.ink}>{d.draw}</svg>
    </span>
  );
}
