import type { CharacterState } from "../../api/types";

interface Props {
  character: CharacterState;
  x: number;
  y: number;
  offset: number;
  total: number;
  isCurrent: boolean;
}

export function Token({ character, x, y, offset, total, isCurrent }: Props) {
  // Offset tokens if multiple characters on the same space
  const angle = total > 1 ? (offset * (2 * Math.PI)) / total - Math.PI / 2 : 0;
  const offsetDist = total > 1 ? 14 : 0;
  const tx = x + Math.cos(angle) * offsetDist;
  const ty = y + Math.sin(angle) * offsetDist;

  const initial = character.name.charAt(0).toUpperCase();
  const isDead = character.is_permanently_dead;
  const isInVat = character.is_in_bio_vat;

  const fillColor = isDead ? "#333" : character.color;
  const opacity = isDead ? 0.4 : isInVat ? 0.6 : 1;

  return (
    <g
      className={isCurrent ? "token-current" : ""}
      style={{ color: character.color }}
      opacity={opacity}
    >
      {/* Token circle */}
      <circle
        cx={tx}
        cy={ty}
        r={10}
        fill={fillColor}
        stroke={isCurrent ? "#ffffff" : "#0a0a1a"}
        strokeWidth={isCurrent ? 2.5 : 1.5}
      />

      {/* Character initial */}
      <text
        x={tx}
        y={ty + 1}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#ffffff"
        fontSize={10}
        fontWeight="800"
        style={{ pointerEvents: "none" }}
      >
        {isDead ? "X" : initial}
      </text>

      {/* Bio-vat indicator */}
      {isInVat && (
        <circle
          cx={tx}
          cy={ty}
          r={12}
          fill="none"
          stroke="#ff8800"
          strokeWidth={1}
          strokeDasharray="3 2"
        />
      )}
    </g>
  );
}
