// Pastel palette from design guidelines for calendar blocks
export const CALENDAR_COLORS = [
  { bg: "#FEF08A", text: "#854D0E", border: "#FDE047" },
  { bg: "#A7F3D0", text: "#065F46", border: "#6EE7B7" },
  { bg: "#BFDBFE", text: "#1E3A8A", border: "#93C5FD" },
  { bg: "#DDD6FE", text: "#5B21B6", border: "#C4B5FD" },
  { bg: "#FECACA", text: "#991B1B", border: "#FCA5A5" },
  { bg: "#FED7AA", text: "#9A3412", border: "#FDBA74" },
  { bg: "#FBCFE8", text: "#9D174D", border: "#F9A8D4" },
];

// Deterministic color for a given key (e.g. materia nombre)
export function colorForKey(key) {
  if (!key) return CALENDAR_COLORS[0];
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) | 0;
  }
  const idx = Math.abs(hash) % CALENDAR_COLORS.length;
  return CALENDAR_COLORS[idx];
}
