import type { CodeValue } from "../../api/types";

interface Props {
  value: CodeValue;
  x: number;
  y: number;
  radius: number;
}

/** Current code letter, shown as a badge in the upper part of the printed code room. */
export function CodeRoom({ value, x, y, radius }: Props) {
  const displayValue = value === "UNSET" ? "?" : value;
  const color = value === "A" ? "#00ff88" : value === "B" ? "#ff3355" : "#ffcc00";
  const cy = y - radius * 0.62;

  return (
    <g style={{ pointerEvents: "none" }}>
      <rect x={x - 36} y={cy - 28} width={72} height={56} rx={12} fill="#0a0a1a" fillOpacity={0.85} stroke={color} strokeWidth={4} />
      <text x={x} y={cy + 2} textAnchor="middle" dominantBaseline="central" fill={color} fontSize={40} fontWeight="800">
        {displayValue}
      </text>
    </g>
  );
}
