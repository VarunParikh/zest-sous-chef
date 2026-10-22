// First-screen tour (FR-126, AC-60, AC-61; Conversation Design §6.7; Zest 2.0). Six steps over `data-tour`
// anchors. It never blocks the app: the highlight ignores the pointer and only the bubble takes clicks.
// "Seen" lives in this browser's storage (a per-viewer convenience); without storage the tour simply shows again.
import { useEffect, useLayoutEffect, useRef, useState } from "react";

const SEEN_KEY = "zest2.tourSeen";
const STEPS = [
  { anchor: "starters", title: "Start here", text: "Tap a starter to try Zest in one click." },
  { anchor: "chatbox", title: "Chat with Zest", text: "Or type here: a dish, a recipe, a mood, or paste a YouTube link. Press Enter or Send." },
  { anchor: "personas", title: "Who's cooking?", text: "Pick a persona. Their diet and faith rules are applied in code, every time." },
  { anchor: "lever", title: "Levers", text: "Move a lever to change what Zest suggests. The ⓘ says whether it's a Rule (removes dishes) or a Preference (re-ranks them)." },
  { anchor: "cart", title: "Your cart", text: "Everything Zest adds goes into your cart, at the top right. Open it to change quantities, swap items or place a mock order." },
  { anchor: "inspector", title: "Inspector", text: "For the curious: every candidate, its ranks, whether it passed your rules, and its score. It fills in once you start chatting and Zest suggests a dish." },
];

export function tourSeen(): boolean {
  try { return window.localStorage.getItem(SEEN_KEY) === "1"; } catch { return false; }
}
function markSeen() {
  try { window.localStorage.setItem(SEEN_KEY, "1"); } catch { /* storage unavailable: the tour shows again next time */ }
}

type Rect = { top: number; left: number; width: number; height: number };

/** `userActions` counts the user's messages; a new one while on step 1 moves the tour on (AC-60). */
export function Tour({ open, onClose, userActions, onStep }: {
  open: boolean; onClose: () => void; userActions: number; onStep?: (anchor: string) => void;
}) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const returnTo = useRef<Element | null>(null);
  const startActions = useRef(userActions);

  useEffect(() => {
    if (open) { setStep(0); startActions.current = userActions; returnTo.current = document.activeElement; }
  }, [open]);  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {  // step 1 is interactive: using a starter (or sending anything) is the same as Next
    if (open && step === 0 && userActions > startActions.current) { startActions.current = userActions; setStep(1); }  // used once
  }, [open, step, userActions]);

  useEffect(() => { if (open) onStep?.(STEPS[step].anchor); }, [open, step]);  // eslint-disable-line react-hooks/exhaustive-deps

  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const el = document.querySelector<HTMLElement>(`[data-tour="${STEPS[step].anchor}"]`);
      const r = el && el.offsetParent !== null ? el.getBoundingClientRect() : null;
      setRect(r ? { top: r.top, left: r.left, width: r.width, height: r.height } : null);
    };
    document.querySelector(`[data-tour="${STEPS[step].anchor}"]`)?.scrollIntoView({ block: "nearest" });
    place();
    const again = window.setTimeout(place, 50);  // after a narrow-screen tab switch (onStep) has rendered
    heading.current?.focus();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => { window.clearTimeout(again); window.removeEventListener("resize", place); window.removeEventListener("scroll", place, true); };
  }, [open, step]);

  if (!open) return null;
  const close = () => {
    markSeen();
    onClose();
    if (returnTo.current instanceof HTMLElement) returnTo.current.focus();
  };
  const last = step === STEPS.length - 1;
  const s = STEPS[step];
  const pad = 6;
  const below = rect ? rect.top + rect.height + 200 < window.innerHeight : true;
  const bubbleTop = rect ? (below ? rect.top + rect.height + pad + 8 : Math.max(8, rect.top - pad - 8 - 180)) : window.innerHeight / 2 - 90;
  const bubbleLeft = rect ? Math.min(Math.max(8, rect.left), window.innerWidth - 336) : window.innerWidth / 2 - 164;

  return (
    <>
      {rect && (
        <div aria-hidden="true" className="pointer-events-none fixed z-40 rounded-xl ring-2 ring-brand transition-all duration-200"
          style={{ top: rect.top - pad, left: rect.left - pad, width: rect.width + pad * 2, height: rect.height + pad * 2,
                   boxShadow: "0 0 0 9999px rgba(17,24,39,0.35)" }} />
      )}
      <div role="dialog" aria-modal="false" aria-labelledby="tour-title" aria-describedby="tour-text" data-testid="tour"
        className="fixed z-50 w-[328px] rounded-xl bg-white p-4 shadow-modal"
        style={{ top: bubbleTop, left: bubbleLeft }}
        onKeyDown={(e) => { if (e.key === "Escape") close(); }}>
        <p className="text-xs text-muted" aria-live="polite">Step {step + 1} of {STEPS.length}</p>
        <h2 id="tour-title" ref={heading} tabIndex={-1} className="mt-1 text-base font-semibold text-ink outline-none">{s.title}</h2>
        <p id="tour-text" className="mt-1 text-sm leading-relaxed text-secondary">{s.text}</p>
        <div className="mt-3 flex items-center justify-between">
          <button type="button" onClick={close} className="text-sm text-muted hover:text-ink">Skip</button>
          <span className="flex gap-2">
            {step > 0 && <button type="button" onClick={() => setStep(step - 1)} className="rounded-[10px] border border-strong px-3 py-1.5 text-sm">Back</button>}
            <button type="button" onClick={() => (last ? close() : setStep(step + 1))}
              className="rounded-[10px] bg-brand px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-hover">{last ? "Done" : "Next"}</button>
          </span>
        </div>
      </div>
    </>
  );
}
