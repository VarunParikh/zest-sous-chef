// Inline monoline icons (Lucide style, stroke 1.75; DESIGN.md Icons). Category tiles use emoji with text labels.
import type { ReactNode, SVGProps } from "react";

function Svg({ children, size = 18, ...rest }: SVGProps<SVGSVGElement> & { size?: number; children: ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...rest}>
      {children}
    </svg>
  );
}

export const Send = () => <Svg><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></Svg>;
export const ImageIcon = () => <Svg><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21" /></Svg>;
export const Trash = () => <Svg size={16}><path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></Svg>;
export const Plus = () => <Svg size={14}><path d="M12 5v14M5 12h14" /></Svg>;
export const Minus = () => <Svg size={14}><path d="M5 12h14" /></Svg>;
export const Close = () => <Svg><path d="M18 6 6 18M6 6l12 12" /></Svg>;
export const Back = () => <Svg><path d="m12 19-7-7 7-7M19 12H5" /></Svg>;
export const Chevron = ({ open }: { open: boolean }) => (
  <Svg size={16} className={`transition-transform duration-150 ${open ? "rotate-180" : ""}`}><path d="m6 9 6 6 6-6" /></Svg>
);
export const CartIcon = () => <Svg size={20}><circle cx="8" cy="21" r="1" /><circle cx="19" cy="21" r="1" /><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12" /></Svg>;
export const Check = () => <Svg size={40} strokeWidth={2.5}><path d="M20 6 9 17l-5-5" /></Svg>;
export const Bike = () => <Svg size={36}><circle cx="5.5" cy="17.5" r="3.5" /><circle cx="18.5" cy="17.5" r="3.5" /><path d="M15 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm-3 11.5V14l-3-3 4-3 2 3h2" /></Svg>;
export const Play = () => <Svg size={14}><polygon points="6 3 20 12 6 21 6 3" /></Svg>;
export const Camera = () => <Svg size={14}><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z" /><circle cx="12" cy="13" r="3" /></Svg>;
export const Utensils = () => <Svg size={14}><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2M7 2v20M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7" /></Svg>;
export const Sparkle = () => <Svg size={14}><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1" /></Svg>;

const CATEGORY: Record<string, [string, string]> = {
  vegetables: ["🥬", "Vegetables"], dairy: ["🧀", "Dairy"], spices: ["🌶️", "Spices"], grains: ["🌾", "Grains"],
  fruits: ["🍎", "Fruits"], beverages: ["🥤", "Beverages"], pulses: ["🫘", "Pulses"], bakery: ["🍞", "Bakery"],
  meat: ["🍗", "Meat"], snacks: ["🍿", "Snacks"], oils: ["🫒", "Oils"], sauces: ["🥫", "Sauces"],
  sweeteners: ["🍯", "Sweeteners"], nuts: ["🥜", "Nuts"], protein: ["🥚", "Protein"], breakfast: ["🥣", "Breakfast"],
  ready: ["🍱", "Ready to eat"], frozen: ["🧊", "Frozen"], household: ["🧴", "Household"],
};
const COURSE: Record<string, [string, string]> = {
  main: ["🍛", "Main course"], side: ["🥗", "Side"], beverage: ["🥤", "Beverage"], dessert: ["🍮", "Dessert"],
  breakfast: ["🍳", "Breakfast"], soup: ["🍲", "Soup"], snack: ["🥨", "Snack"],
};

export function CategoryTile({ icon, size = 48 }: { icon: string; size?: number }) {
  const [emoji, label] = CATEGORY[icon] ?? ["🛒", "Grocery"];
  return (
    <span role="img" aria-label={label} title={label} style={{ width: size, height: size }}
      className="flex shrink-0 items-center justify-center rounded-md border border-line bg-subtle text-2xl">
      {emoji}
    </span>
  );
}

export function CourseIcon({ course }: { course: string | null }) {
  const [emoji, label] = (course && COURSE[course]) || ["🍽️", "Your recipe"];
  return <span role="img" aria-label={label} title={label} className="text-lg">{emoji}</span>;
}

export const rupees = (n: number) => `₹${n.toLocaleString("en-IN")}`;
