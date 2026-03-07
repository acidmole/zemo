import { useState, useCallback } from "react";
import { useGameState } from "./hooks/useGameState";
import type { GameState, ActionRequest, MoveRequest, DropCardsRequest } from "./api/types";
import { api, ApiError } from "./api/client";
import { GameSetup } from "./components/Setup/GameSetup";
import { Board } from "./components/Board/Board";
import { HealthTrack } from "./components/HUD/HealthTrack";
import { PlayerInfo } from "./components/HUD/PlayerInfo";
import { TurnIndicator } from "./components/HUD/TurnIndicator";
import { ActionBar } from "./components/Actions/ActionBar";
import { MovementUI } from "./components/Actions/MovementUI";
import { FightDialog } from "./components/Actions/FightDialog";
import { CardInspect } from "./components/Actions/CardInspect";
import { CodeSelect } from "./components/Actions/CodeSelect";

type AppScreen = "setup" | "playing" | "game_over";

export default function App() {
  const { gameState, setGameState, currentPlayer, error, clearError } = useGameState();
  const [screen, setScreen] = useState<AppScreen>("setup");
  const [gameId, setGameId] = useState<string>("");
  const [highlightedSpaces, setHighlightedSpaces] = useState<string[]>([]);
  const [movementRoll, setMovementRoll] = useState<number | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  // Dialog states
  const [showFight, setShowFight] = useState(false);
  const [fightResult, setFightResult] = useState<Record<string, unknown> | null>(null);
  const [showCardInspect, setShowCardInspect] = useState(false);
  const [pickResult, setPickResult] = useState<Record<string, unknown> | null>(null);
  const [showCodeSelect, setShowCodeSelect] = useState(false);

  const displayError = localError || error;

  const handleGameCreated = useCallback((id: string, state: GameState) => {
    setGameId(id);
    setGameState(state);
    setScreen("playing");
  }, [setGameState]);

  const handleStateUpdate = useCallback((state: GameState) => {
    setGameState(state);
    if (state.phase === "game_over") {
      setScreen("game_over");
    }
    // If there's a pending movement roll in the state, use it
    if (state.pending_movement_roll !== null && state.pending_movement_roll !== undefined) {
      setMovementRoll(state.pending_movement_roll);
      setHighlightedSpaces(state.pending_reachable_spaces || []);
    }
  }, [setGameState]);

  const handleRollMovement = useCallback(async () => {
    if (!gameId || !currentPlayer) return;
    try {
      setLocalError(null);
      const resp = await api.rollMovement(gameId, currentPlayer.id);
      setMovementRoll(resp.roll);
      setHighlightedSpaces(resp.reachable_spaces);
      handleStateUpdate(resp.state);
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.detail : "Failed to roll movement");
    }
  }, [gameId, currentPlayer, handleStateUpdate]);

  const handleMoveToSpace = useCallback(async (spaceId: string) => {
    if (!gameId || !currentPlayer) return;
    try {
      setLocalError(null);
      const req: MoveRequest = { character_id: currentPlayer.id, target_space_id: spaceId };
      const resp = await api.move(gameId, req);
      setHighlightedSpaces([]);
      setMovementRoll(null);
      handleStateUpdate(resp.state);
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.detail : "Failed to move");
    }
  }, [gameId, currentPlayer, handleStateUpdate]);

  const handleStay = useCallback(async () => {
    if (!gameId || !currentPlayer) return;
    try {
      setLocalError(null);
      const req: MoveRequest = { character_id: currentPlayer.id, target_space_id: currentPlayer.position };
      const resp = await api.move(gameId, req);
      setHighlightedSpaces([]);
      setMovementRoll(null);
      handleStateUpdate(resp.state);
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.detail : "Failed to stay");
    }
  }, [gameId, currentPlayer, handleStateUpdate]);

  const handleAction = useCallback(async (req: ActionRequest) => {
    if (!gameId) return;
    try {
      setLocalError(null);
      const resp = await api.action(gameId, req);
      handleStateUpdate(resp.state);
      return resp.result;
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.detail : "Failed to perform action");
      return null;
    }
  }, [gameId, handleStateUpdate]);

  const handleFight = useCallback(async (targetId: string, weaponCardId?: string) => {
    if (!currentPlayer) return;
    const result = await handleAction({
      character_id: currentPlayer.id,
      action_type: "fight",
      target_character_id: targetId,
      weapon_card_id: weaponCardId,
    });
    if (result) {
      setFightResult(result);
      setShowFight(true);
    }
  }, [currentPlayer, handleAction]);

  const handleShoot = useCallback(async (targetId: string, weaponCardId: string) => {
    if (!currentPlayer) return;
    const result = await handleAction({
      character_id: currentPlayer.id,
      action_type: "shoot",
      target_character_id: targetId,
      weapon_card_id: weaponCardId,
    });
    if (result) {
      setFightResult(result);
      setShowFight(true);
    }
  }, [currentPlayer, handleAction]);

  const handlePick = useCallback(async (cardIds?: string[]) => {
    if (!currentPlayer) return;
    const result = await handleAction({
      character_id: currentPlayer.id,
      action_type: "pick",
      card_ids_to_pick: cardIds,
    });
    if (result) {
      setPickResult(result);
      setShowCardInspect(true);
    }
  }, [currentPlayer, handleAction]);

  const handlePush = useCallback(async () => {
    setShowCodeSelect(true);
  }, []);

  const handleCodePush = useCallback(async (codeValue?: "A" | "B") => {
    if (!currentPlayer) return;
    await handleAction({
      character_id: currentPlayer.id,
      action_type: "push",
      code_value: codeValue,
    });
    setShowCodeSelect(false);
  }, [currentPlayer, handleAction]);

  const handleHeal = useCallback(async () => {
    if (!currentPlayer) return;
    await handleAction({
      character_id: currentPlayer.id,
      action_type: "heal",
    });
  }, [currentPlayer, handleAction]);

  const handlePass = useCallback(async () => {
    if (!currentPlayer) return;
    await handleAction({
      character_id: currentPlayer.id,
      action_type: "pass",
    });
  }, [currentPlayer, handleAction]);

  const handleDropCards = useCallback(async (cardIds: string[]) => {
    if (!gameId || !currentPlayer) return;
    try {
      setLocalError(null);
      const req: DropCardsRequest = { character_id: currentPlayer.id, card_ids: cardIds };
      const resp = await api.dropCards(gameId, req);
      handleStateUpdate(resp.state);
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.detail : "Failed to drop cards");
    }
  }, [gameId, currentPlayer, handleStateUpdate]);

  const handleNewGame = useCallback(() => {
    setScreen("setup");
    setGameId("");
    setHighlightedSpaces([]);
    setMovementRoll(null);
    setLocalError(null);
  }, []);

  // ===== SETUP SCREEN =====
  if (screen === "setup") {
    return <GameSetup onGameCreated={handleGameCreated} />;
  }

  // ===== GAME OVER SCREEN =====
  if (screen === "game_over" && gameState) {
    const winner = gameState.players.find((p) => p.id === gameState.winner);
    return (
      <div className="game-over">
        <h1>GAME OVER</h1>
        <div className="winner-name">
          {winner ? `${winner.name} ESCAPES!` : "Nobody escaped..."}
        </div>
        <p style={{ color: "#9090b0" }}>
          {winner
            ? `${winner.name} successfully entered the correct escape code and reached the Escape Pod!`
            : "The station falls silent..."}
        </p>
        <button className="btn btn-primary btn-lg" onClick={handleNewGame}>
          New Game
        </button>
        <div className="panel" style={{ maxWidth: 600, width: "90%", maxHeight: 300, overflowY: "auto" }}>
          <div className="panel-title">Game Log</div>
          {gameState.game_log.slice(-30).map((entry, i) => (
            <div key={i} className="log-entry">{entry}</div>
          ))}
        </div>
      </div>
    );
  }

  // ===== PLAYING SCREEN =====
  if (!gameState) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <p style={{ color: "#9090b0" }}>Loading game state...</p>
      </div>
    );
  }

  const isMovementPhase = gameState.phase === "movement";
  const isActionPhase = gameState.phase === "action";

  // Check if current player needs to drop cards (over capacity)
  const currentWeight = currentPlayer
    ? currentPlayer.hand.reduce((sum, c) => sum + c.weight, 0)
    : 0;
  const needsDrop = currentPlayer ? currentWeight > currentPlayer.capacity : false;

  return (
    <div className="game-layout">
      {/* Header */}
      <div className="game-header">
        <TurnIndicator gameState={gameState} currentPlayer={currentPlayer} />
        {displayError && (
          <div className="error-banner">
            <span>{displayError}</span>
            <button onClick={() => { clearError(); setLocalError(null); }}>X</button>
          </div>
        )}
      </div>

      {/* Left sidebar: Health Track */}
      <div className="game-health">
        <HealthTrack players={gameState.players} currentPlayerId={currentPlayer?.id} />
      </div>

      {/* Center: Board */}
      <div className="game-board">
        <Board
          gameState={gameState}
          highlightedSpaces={highlightedSpaces}
          onSpaceClick={isMovementPhase && movementRoll !== null ? handleMoveToSpace : undefined}
          currentPlayerId={currentPlayer?.id}
        />
      </div>

      {/* Right sidebar: Player Info */}
      <div className="game-info">
        <PlayerInfo
          player={currentPlayer}
          onDropCards={needsDrop ? handleDropCards : undefined}
        />
      </div>

      {/* Bottom: Actions / Movement */}
      <div className="game-actions">
        {isMovementPhase && (
          <MovementUI
            roll={movementRoll}
            reachableCount={highlightedSpaces.length}
            onRoll={handleRollMovement}
            onStay={handleStay}
            hasRolled={movementRoll !== null}
            hasMoved={currentPlayer?.has_moved_this_turn ?? false}
          />
        )}
        {isActionPhase && (
          <ActionBar
            availableActions={gameState.available_actions}
            currentPlayer={currentPlayer}
            gameState={gameState}
            onPick={handlePick}
            onFight={handleFight}
            onShoot={handleShoot}
            onPush={handlePush}
            onHeal={handleHeal}
            onPass={handlePass}
          />
        )}
        {!isMovementPhase && !isActionPhase && gameState.phase === "round_end" && (
          <div className="action-bar">
            <span style={{ color: "#ffcc00" }}>Round {gameState.round_number} ending... Waiting for server.</span>
          </div>
        )}
      </div>

      {/* Bottom: Game Log */}
      <div className="game-log">
        <div className="log-container">
          {gameState.game_log.slice(-20).map((entry, i) => (
            <div key={i} className="log-entry">{entry}</div>
          ))}
          {gameState.game_log.length === 0 && (
            <div className="log-entry" style={{ color: "#606080" }}>Game started. Good luck!</div>
          )}
        </div>
      </div>

      {/* Dialogs */}
      {showFight && fightResult && (
        <FightDialog
          result={fightResult}
          gameState={gameState}
          onClose={() => { setShowFight(false); setFightResult(null); }}
          onContinue={async (continueF) => {
            if (!currentPlayer) return;
            if (continueF) {
              const result = await handleAction({
                character_id: currentPlayer.id,
                action_type: "fight",
                continue_fighting: true,
              });
              if (result) {
                setFightResult(result);
              } else {
                setShowFight(false);
                setFightResult(null);
              }
            } else {
              setShowFight(false);
              setFightResult(null);
            }
          }}
        />
      )}

      {showCardInspect && pickResult && (
        <CardInspect
          result={pickResult}
          gameState={gameState}
          onClose={() => { setShowCardInspect(false); setPickResult(null); }}
        />
      )}

      {showCodeSelect && (
        <CodeSelect
          gameState={gameState}
          onPush={handleCodePush}
          onClose={() => setShowCodeSelect(false)}
        />
      )}
    </div>
  );
}
