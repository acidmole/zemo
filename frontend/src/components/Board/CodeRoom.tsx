import type { CodeValue } from "../../api/types";

interface Props {
  roomNumber: number;
  value: CodeValue;
  x: number;
  y: number;
}

export function CodeRoom({ roomNumber, value, x, y }: Props) {
  const displayValue = value === "UNSET" ? "?" : value;
  const color = value === "A" ? "#00ff88" : value === "B" ? "#ff3355" : "#ffcc00";

  return (
    <g>
      {/* Status badge positioned above/below the space */}
      <rect
        x={x - 12}
        y={y - radius(roomNumber) - 18}
        width={24}
        height={14}
        rx={3}
        fill="#0a0a1a"
        stroke={color}
        strokeWidth={1}
      />
      <text
        x={x}
        y={y - radius(roomNumber) - 10}
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize={9}
        fontWeight="800"
        style={{ pointerEvents: "none" }}
      >
        {displayValue}
      </text>
    </g>
  );
}

function radius(_roomNumber: number): number {
  return 22; // special spaces have radius 22
}
