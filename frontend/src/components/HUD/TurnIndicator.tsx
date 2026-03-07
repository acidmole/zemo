import type { GameState, CharacterState } from "../../api/types";

interface Props {
  gameState: GameState;
  currentPlayer: CharacterState | null;
}

export function TurnIndicator({ gameState, currentPlayer }: Props) {
  const phaseName = gameState.phase.toUpperCase().replace("_", " ");

  return (
    <div className="turn-indicator">
      <div className="turn-round">
        Round {gameState.round_number}
      </div>
      <div className="turn-player" style={{ color: currentPlayer?.color || "#e0e0e0" }}>
        {currentPlayer?.name || "---"}
      </div>
      <div className={`turn-phase ${gameState.phase}`}>
        {phaseName}
      </div>
    </div>
  );
}
