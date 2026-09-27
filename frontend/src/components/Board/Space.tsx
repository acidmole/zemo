import type { BoardSpace } from "../../api/board";

interface Props {
  space: BoardSpace;
  cardCount: number;
  isHighlighted: boolean;
  onClick?: () => void;
}

function Shape({ space, className }: { space: BoardSpace; className: string }) {
  const { shape, x, y } = space;
  switch (shape.kind) {
    case "rect":
      return (
        <rect
          className={className}
          x={x - shape.w / 2}
          y={y - shape.h / 2}
          width={shape.w}
          height={shape.h}
          rx={8}
          transform={shape.angle ? `rotate(${shape.angle} ${x} ${y})` : undefined}
        />
      );
    case "circle":
      return <circle className={className} cx={x} cy={y} r={shape.r} />;
    case "polygon":
      return <polygon className={className} points={shape.points.map((p) => p.join(",")).join(" ")} />;
  }
}

export function Space({ space, cardCount, isHighlighted, onClick }: Props) {
  // Card badge sits on the upper-right of a room's circle
  const badgeOffset = space.shape.kind === "circle" ? space.shape.r * 0.72 : 0;

  return (
    <g
      className={isHighlighted ? "space-reachable" : undefined}
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
    >
      <title>{space.name}</title>
      <Shape space={space} className={isHighlighted ? "space-shape highlighted" : "space-shape"} />

      {cardCount > 0 && (
        <g className="card-badge">
          <circle cx={space.x + badgeOffset} cy={space.y - badgeOffset} r={22} />
          <text x={space.x + badgeOffset} y={space.y - badgeOffset + 1} textAnchor="middle" dominantBaseline="central">
            {cardCount}
          </text>
        </g>
      )}
    </g>
  );
}
