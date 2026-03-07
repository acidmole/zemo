import { useState, useCallback, useMemo } from "react";
import type { GameState, CharacterState } from "../api/types";
import { api } from "../api/client";

export interface UseGameStateReturn {
  gameState: GameState | null;
  setGameState: (state: GameState) => void;
  refreshState: (gameId: string) => Promise<void>;
  currentPlayer: CharacterState | null;
  error: string | null;
  clearError: () => void;
}

export function useGameState(): UseGameStateReturn {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshState = useCallback(async (gameId: string) => {
    try {
      const resp = await api.getState(gameId);
      setGameState(resp.state);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch game state";
      setError(message);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const currentPlayer = useMemo(() => {
    if (!gameState) return null;
    const currentCharId = gameState.turn_order[gameState.current_player_index];
    return gameState.players.find((p) => p.id === currentCharId) ?? null;
  }, [gameState]);

  return {
    gameState,
    setGameState,
    refreshState,
    currentPlayer,
    error,
    clearError,
  };
}
