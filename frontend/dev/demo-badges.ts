import type { Deal } from "../lib/api";

export function getDemoBadge(deal: Deal): string | null {
  const condition = (deal.condition || "").toLowerCase();
  if (deal.price === 0 && condition in { good: true, great: true, excellent: true }) {
    return "Likely good deal";
  }
  if (deal.deal_score >= 80) {
    return "Likely good deal";
  }
  return null;
}
