// Retrieval and scoring inspector (FR-115, US-39; DESIGN.md Tables).
import type { Inspector } from "../api/types";

const fmt = (v: number | null, d = 0) => (v === null || v === undefined ? "–" : d ? v.toFixed(d) : String(v));

export function InspectorTable({ inspector }: { inspector: Inspector | null }) {
  if (!inspector || inspector.rows.length === 0) return <p className="text-sm text-muted">No suggestion yet in this session.</p>;
  const shown = new Set(inspector.shown);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <caption className="sr-only">Candidate pool for the latest suggestion</caption>
        <thead className="bg-canvas text-muted">
          <tr>
            {["Fused", "Dish", "Lexical", "Vector", "Distance", "Eligible", "Score"].map((h) => (
              <th key={h} scope="col" className="h-[42px] px-2 font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {inspector.rows.map((r) => (
            <tr key={r.candidate_id} className={`h-[42px] border-t border-line hover:bg-[#F9FAFB] ${shown.has(r.candidate_id) ? "font-semibold text-brand" : ""}`}>
              <td className="px-2 font-mono">{r.fused_rank}</td>
              <td className="px-2">{r.name}{shown.has(r.candidate_id) && <span className="sr-only"> (shown)</span>}</td>
              <td className="px-2 font-mono">{fmt(r.lexical_rank)}</td>
              <td className="px-2 font-mono">{fmt(r.vector_rank)}</td>
              <td className="px-2 font-mono">{fmt(r.vector_distance, 3)}</td>
              <td className="px-2">{r.eligible ? "Yes" : <span className="text-err">No: {r.filtered_by.join(", ")}</span>}</td>
              <td className="px-2 font-mono">{r.final.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
