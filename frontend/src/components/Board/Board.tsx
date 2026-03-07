import { useMemo } from "react";
import type { GameState } from "../../api/types";
import { BOARD_SPACES, BOARD_EDGES, SPACE_MAP } from "../../api/boardData";
import { Space } from "./Space";
import { Token } from "./Token";
import { CodeRoom } from "./CodeRoom";

interface Props {
  gameState: GameState;
  highlightedSpaces: string[];
  onSpaceClick?: (spaceId: string) => void;
  currentPlayerId?: string;
}

export function Board({ gameState, highlightedSpaces, onSpaceClick, currentPlayerId }: Props) {
  const highlightedSet = useMemo(() => new Set(highlightedSpaces), [highlightedSpaces]);

  // Build a map of space_id -> character states for token placement
  const charactersBySpace = useMemo(() => {
    const map: Record<string, typeof gameState.players> = {};
    for (const player of gameState.players) {
      if (!player.is_permanently_dead || player.is_in_bio_vat) {
        if (!map[player.position]) map[player.position] = [];
        map[player.position].push(player);
      }
    }
    return map;
  }, [gameState.players]);

  // Star field background
  const stars = useMemo(() => {
    const s = [];
    for (let i = 0; i < 80; i++) {
      s.push({
        cx: Math.random() * 920,
        cy: Math.random() * 860,
        r: Math.random() * 1.2 + 0.3,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }
    return s;
  }, []);

  return (
    <svg
      className="board-svg"
      viewBox="0 0 920 860"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Dark starfield background */}
      <rect x="0" y="0" width="920" height="860" fill="#060614" rx="12" />
      {stars.map((star, i) => (
        <circle key={i} cx={star.cx} cy={star.cy} r={star.r} fill="#ffffff" opacity={star.opacity} />
      ))}

      {/* Title */}
      <text x="460" y="28" textAnchor="middle" fill="#00aaff" fontSize="14" fontWeight="700" opacity="0.6">
        SPACE STATION ZEMO
      </text>

      {/* Edges (connections between spaces) */}
      {BOARD_EDGES.map((edge, i) => {
        const from = SPACE_MAP[edge.from];
        const to = SPACE_MAP[edge.to];
        if (!from || !to) return null;
        const isInterior =
          edge.from.includes("_") || edge.to.includes("_");
        return (
          <line
            key={i}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            className={`board-edge ${isInterior ? "interior" : ""}`}
          />
        );
      })}

      {/* Spaces */}
      {BOARD_SPACES.map((space) => {
        const spaceState = gameState.spaces[space.id];
        const cardCount = spaceState?.cards?.length ?? 0;
        const isHighlighted = highlightedSet.has(space.id);
        return (
          <Space
            key={space.id}
            space={space}
            cardCount={cardCount}
            isHighlighted={isHighlighted}
            onClick={isHighlighted && onSpaceClick ? () => onSpaceClick(space.id) : undefined}
          />
        );
      })}

      {/* Tokens (characters on the board) */}
      {Object.entries(charactersBySpace).map(([spaceId, chars]) => {
        const space = SPACE_MAP[spaceId];
        if (!space) return null;
        return chars.map((char, idx) => (
          <Token
            key={char.id}
            character={char}
            x={space.x}
            y={space.y}
            offset={idx}
            total={chars.length}
            isCurrent={char.id === currentPlayerId}
          />
        ));
      })}

      {/* Code Room status indicators */}
      {gameState.code_rooms.map((cr) => {
        const spaceId = `code_room_${cr.room_number}`;
        const space = SPACE_MAP[spaceId];
        if (!space) return null;
        return (
          <CodeRoom
            key={cr.room_number}
            roomNumber={cr.room_number}
            value={cr.value}
            x={space.x}
            y={space.y}
          />
        );
      })}
    </svg>
  );
}
