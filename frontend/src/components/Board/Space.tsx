import type { SpacePosition } from "../../api/boardData";

interface Props {
  space: SpacePosition;
  cardCount: number;
  isHighlighted: boolean;
  onClick?: () => void;
}

const TYPE_COLORS: Record<string, string> = {
  hallway: "#2a2a3a",
  room: "#1a3a5c",
  code_room: "#5c1a3a",
  escape_pod: "#3a5c1a",
  bio_vat: "#5c3a1a",
  airlock: "#3a1a5c",
};

const TYPE_STROKE: Record<string, string> = {
  hallway: "#3a3a5a",
  room: "#2a5a8a",
  code_room: "#8a2a5a",
  escape_pod: "#5a8a2a",
  bio_vat: "#8a5a2a",
  airlock: "#5a2a8a",
};

export function Space({ space, cardCount, isHighlighted, onClick }: Props) {
  const fill = TYPE_COLORS[space.type] || "#2a2a3a";
  const stroke = isHighlighted ? "#00ff88" : (TYPE_STROKE[space.type] || "#3a3a5a");
  const strokeWidth = isHighlighted ? 3 : 1.5;
  const isSpecial = space.type !== "hallway";
  const radius = isSpecial ? 22 : 16;
  const isNumbered = !space.id.includes("_");
  const showName = isSpecial || !isNumbered;

  // For named numbered rooms, show name
  const isNamedRoom = [
    "7", "11", "13", "17", "21", "22", "23", "25", "26", "29", "32",
  ].includes(space.id);

  return (
    <g
      className={isHighlighted ? "space-reachable" : ""}
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
    >
      {/* Space shape */}
      {isSpecial ? (
        <rect
          x={space.x - radius}
          y={space.y - radius}
          width={radius * 2}
          height={radius * 2}
          rx={6}
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeWidth}
        />
      ) : (
        <circle
          cx={space.x}
          cy={space.y}
          r={radius}
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeWidth}
        />
      )}

      {/* Highlight glow */}
      {isHighlighted && (
        isSpecial ? (
          <rect
            x={space.x - radius - 3}
            y={space.y - radius - 3}
            width={(radius + 3) * 2}
            height={(radius + 3) * 2}
            rx={8}
            fill="none"
            stroke="#00ff88"
            strokeWidth={1}
            opacity={0.4}
          />
        ) : (
          <circle
            cx={space.x}
            cy={space.y}
            r={radius + 3}
            fill="none"
            stroke="#00ff88"
            strokeWidth={1}
            opacity={0.4}
          />
        )
      )}

      {/* Space number */}
      {isNumbered && (
        <text
          x={space.x}
          y={space.y + 1}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#c0c0d0"
          fontSize={isNamedRoom ? 9 : 10}
          fontWeight="600"
          style={{ pointerEvents: "none" }}
        >
          {space.id}
        </text>
      )}

      {/* Special space label */}
      {!isNumbered && (
        <text
          x={space.x}
          y={space.y + 1}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#e0e0e0"
          fontSize={7}
          fontWeight="700"
          style={{ pointerEvents: "none" }}
        >
          {space.type === "escape_pod" ? "POD" :
           space.type === "bio_vat" ? "VAT" :
           space.type === "airlock" ? "AIR" :
           space.type === "code_room" ? "CR" + space.id.slice(-1) : "?"}
        </text>
      )}

      {/* Room name below for named rooms */}
      {(isNamedRoom || showName) && (
        <text
          x={space.x}
          y={space.y + radius + 10}
          textAnchor="middle"
          fill="#8080a0"
          fontSize={7}
          style={{ pointerEvents: "none" }}
        >
          {space.name}
        </text>
      )}

      {/* Card count indicator */}
      {cardCount > 0 && (
        <g>
          <circle
            cx={space.x + radius - 4}
            cy={space.y - radius + 4}
            r={7}
            fill="#ffcc00"
            stroke="#0a0a1a"
            strokeWidth={1}
          />
          <text
            x={space.x + radius - 4}
            y={space.y - radius + 5}
            textAnchor="middle"
            dominantBaseline="central"
            fill="#0a0a1a"
            fontSize={8}
            fontWeight="800"
            style={{ pointerEvents: "none" }}
          >
            {cardCount}
          </text>
        </g>
      )}
    </g>
  );
}
