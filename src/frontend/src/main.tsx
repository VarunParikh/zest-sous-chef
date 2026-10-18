import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

function Hello() {
  return <h1 className="p-6 text-brand font-display text-xl font-bold">Zest</h1>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Hello />
  </StrictMode>,
);
