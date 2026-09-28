import { useMemo } from "react";
import type { GameState } from "../../api/types";
import { useBoard } from "../../api/board";
import type { BoardSpace } from "../../api/board";
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
  const board = useBoard();
  const highlightedSet = useMemo(() => new Set(highlightedSpaces), [highlightedSpaces]);

  const spaceMap = useMemo(() => {
    const map: Record<string, BoardSpace> = {};
    for (const space of board?.spaces ?? []) map[space.id] = space;
    return map;
  }, [board]);

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

  if (!board) {
    return <div className="board-loading">Loading board...</div>;
  }

  const { width, height, src } = board.image;

  return (
    <svg
      className="board-svg"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <image href={src} x={0} y={0} width={width} height={height} />

      {/* Spaces: invisible until reachable, then highlighted and clickable */}
      {board.spaces.map((space) => {
        const isHighlighted = highlightedSet.has(space.id);
        return (
          <Space
            key={space.id}
            space={space}
            cardCount={gameState.spaces[space.id]?.cards?.length ?? 0}
            isHighlighted={isHighlighted}
            onClick={isHighlighted && onSpaceClick ? () => onSpaceClick(space.id) : undefined}
          />
        );
      })}

      {/* Code Room status indicators */}
      {gameState.code_rooms.map((cr) => {
        const space = spaceMap[`code_room_${cr.room_number}`];
        if (!space || space.shape.kind !== "circle") return null;
        return (
          <CodeRoom
            key={cr.room_number}
            value={cr.value}
            x={space.x}
            y={space.y}
            radius={space.shape.r}
          />
        );
      })}

      {/* Tokens (characters on the board) */}
      {Object.entries(charactersBySpace).map(([spaceId, chars]) => {
        const space = spaceMap[spaceId];
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
    </svg>
  );
}
