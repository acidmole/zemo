import { useState, useCallback } from "react";
import type { GameState, GameConfig } from "../../api/types";
import { api, ApiError } from "../../api/client";
import { CHARACTER_TEMPLATES, ESCAPE_CODES } from "../../api/boardData";
import type { CharacterTemplate } from "../../api/boardData";
import { SavedGames } from "./SavedGames";

interface Props {
  onGameCreated: (gameId: string, state: GameState) => void;
}

interface PlayerSetup {
  name: string;
  characterId: string;
  escapeCode: string;
}

type Step = "player_count" | "character_select" | "names_codes" | "confirm";

export function GameSetup({ onGameCreated }: Props) {
  const [step, setStep] = useState<Step>("player_count");
  const [playerCount, setPlayerCount] = useState(2);
  const [players, setPlayers] = useState<PlayerSetup[]>([]);
  const [currentSelectingPlayer, setCurrentSelectingPlayer] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Initialize player data when count is confirmed
  const handleCountConfirm = useCallback(() => {
    const initial: PlayerSetup[] = [];
    for (let i = 0; i < playerCount; i++) {
      initial.push({ name: `Player ${i + 1}`, characterId: "", escapeCode: "" });
    }
    setPlayers(initial);
    setCurrentSelectingPlayer(0);
    setStep("character_select");
  }, [playerCount]);

  // Character selection
  const selectedCharacterIds = players.map((p) => p.characterId).filter(Boolean);

  const handleCharacterSelect = useCallback((charId: string) => {
    if (selectedCharacterIds.includes(charId)) return;
    setPlayers((prev) => {
      const updated = [...prev];
      updated[currentSelectingPlayer] = {
        ...updated[currentSelectingPlayer],
        characterId: charId,
      };
      return updated;
    });
  }, [currentSelectingPlayer, selectedCharacterIds]);

  const handleNextCharacterSelect = useCallback(() => {
    if (!players[currentSelectingPlayer]?.characterId) return;
    if (currentSelectingPlayer < playerCount - 1) {
      setCurrentSelectingPlayer((p) => p + 1);
    } else {
      setStep("names_codes");
    }
  }, [currentSelectingPlayer, playerCount, players]);

  const handlePrevCharacterSelect = useCallback(() => {
    if (currentSelectingPlayer > 0) {
      setCurrentSelectingPlayer((p) => p - 1);
    } else {
      setStep("player_count");
    }
  }, [currentSelectingPlayer]);

  // Name/code updates
  const updatePlayer = useCallback((index: number, field: keyof PlayerSetup, value: string) => {
    setPlayers((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  }, []);

  // Validation
  const allReady =
    players.length > 0 &&
    players.every((p) => p.characterId && p.name.trim() && p.escapeCode);

  // Start game
  const handleStartGame = useCallback(async () => {
    if (!allReady) return;
    setLoading(true);
    setError(null);
    try {
      const config: GameConfig = {
        player_characters: players.map((p) => p.characterId),
        player_codes: players.map((p) => p.escapeCode),
        player_names: players.map((p) => p.name.trim()),
      };
      const resp = await api.createGame(config);
      onGameCreated(resp.game_id, resp.state);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create game. Is the server running?");
    } finally {
      setLoading(false);
    }
  }, [allReady, players, onGameCreated]);

  return (
    <div className="setup-container">
      <h1 className="setup-title">SPACE STATION ZEMO</h1>
      <p className="setup-subtitle">A digital board game of treachery, traps, and escape codes</p>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>X</button>
        </div>
      )}

      {/* Step 1: Player Count */}
      {step === "player_count" && (
        <div className="setup-step">
          <h3>How many players?</h3>
          <div className="panel" style={{ textAlign: "center", padding: 24 }}>
            <div className="num-stepper" style={{ justifyContent: "center" }}>
              <button
                className="btn"
                onClick={() => setPlayerCount((c) => Math.max(2, c - 1))}
                disabled={playerCount <= 2}
              >
                -
              </button>
              <span className="num-value">{playerCount}</span>
              <button
                className="btn"
                onClick={() => setPlayerCount((c) => Math.min(4, c + 1))}
                disabled={playerCount >= 4}
              >
                +
              </button>
            </div>
            <p style={{ color: "#9090b0", marginTop: 12, fontSize: "0.85rem" }}>
              2 to 4 players (hot-seat multiplayer)
            </p>
            <button className="btn btn-primary btn-lg" onClick={handleCountConfirm} style={{ marginTop: 16 }}>
              Continue
            </button>
          </div>
          <SavedGames onGameRestored={onGameCreated} />
        </div>
      )}

      {/* Step 2: Character Selection */}
      {step === "character_select" && (
        <div className="setup-step">
          <h3>
            Player {currentSelectingPlayer + 1}: Choose your character
            <span style={{ color: "#606080", fontSize: "0.8rem", marginLeft: 8 }}>
              ({currentSelectingPlayer + 1} of {playerCount})
            </span>
          </h3>
          <div className="character-grid">
            {CHARACTER_TEMPLATES.map((char: CharacterTemplate) => {
              const isTaken =
                selectedCharacterIds.includes(char.id) &&
                players[currentSelectingPlayer]?.characterId !== char.id;
              const isSelected = players[currentSelectingPlayer]?.characterId === char.id;
              return (
                <div
                  key={char.id}
                  className={`character-card ${isSelected ? "selected" : ""} ${isTaken ? "taken" : ""}`}
                  onClick={() => !isTaken && handleCharacterSelect(char.id)}
                >
                  <div className="char-portrait" style={{ backgroundColor: char.color }}>
                    {char.name.charAt(0)}
                  </div>
                  <div style={{ fontWeight: 700, marginBottom: 4 }}>{char.name}</div>
                  <div className="char-stats">
                    <span>HP: {char.maxHealth}</span>
                    {char.combatMod > 0 && <span>Combat: +{char.combatMod}</span>}
                    {char.actionsPerTurn > 1 && <span>Actions: {char.actionsPerTurn}</span>}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#aa00ff", marginTop: 4 }}>
                    {char.special}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#9090b0", marginTop: 4 }}>
                    {char.description}
                  </div>
                  {isTaken && (
                    <div style={{ fontSize: "0.7rem", color: "#ff3355", marginTop: 4 }}>
                      Already chosen
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
            <button className="btn" onClick={handlePrevCharacterSelect}>
              Back
            </button>
            <button
              className="btn btn-primary"
              onClick={handleNextCharacterSelect}
              disabled={!players[currentSelectingPlayer]?.characterId}
            >
              {currentSelectingPlayer < playerCount - 1 ? "Next Player" : "Continue"}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Names & Escape Codes */}
      {step === "names_codes" && (
        <div className="setup-step">
          <h3>Player Names & Escape Codes</h3>
          <p style={{ fontSize: "0.8rem", color: "#9090b0", marginBottom: 12 }}>
            Each player enters their name and secretly chooses an escape code.
            The escape code is your winning combination -- keep it secret!
          </p>
          {players.map((player, idx) => {
            const char = CHARACTER_TEMPLATES.find((c) => c.id === player.characterId);
            return (
              <div key={idx} className="player-setup-row">
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    backgroundColor: char?.color || "#888",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "0.9rem",
                    color: "#fff",
                    flexShrink: 0,
                  }}
                >
                  {char?.name.charAt(0) || "?"}
                </div>
                <div style={{ fontSize: "0.8rem", color: char?.color, fontWeight: 600, minWidth: 80, flexShrink: 0 }}>
                  {char?.name || "???"}
                </div>
                <input
                  type="text"
                  placeholder={`Player ${idx + 1} name`}
                  value={player.name}
                  onChange={(e) => updatePlayer(idx, "name", e.target.value)}
                  style={{ flex: 1 }}
                  maxLength={20}
                />
                <div className="code-input">
                  <select
                    value={player.escapeCode}
                    onChange={(e) => updatePlayer(idx, "escapeCode", e.target.value)}
                  >
                    <option value="">-- Code --</option>
                    {ESCAPE_CODES.map((code) => (
                      <option key={code} value={code}>{code}</option>
                    ))}
                  </select>
                  <span className="code-hint">Secret!</span>
                </div>
              </div>
            );
          })}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
            <button className="btn" onClick={() => { setCurrentSelectingPlayer(playerCount - 1); setStep("character_select"); }}>
              Back
            </button>
            <button className="btn btn-primary" onClick={() => setStep("confirm")} disabled={!allReady}>
              Review
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Confirm */}
      {step === "confirm" && (
        <div className="setup-step">
          <h3>Ready to Launch?</h3>
          <div className="panel" style={{ marginBottom: 16 }}>
            {players.map((player, idx) => {
              const char = CHARACTER_TEMPLATES.find((c) => c.id === player.characterId);
              return (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: 12, padding: "6px 0", borderBottom: "1px solid #2a2a4a" }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: "50%",
                      backgroundColor: char?.color || "#888",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: "0.8rem",
                      color: "#fff",
                    }}
                  >
                    {char?.name.charAt(0)}
                  </div>
                  <span style={{ fontWeight: 600 }}>{player.name}</span>
                  <span style={{ color: char?.color, fontSize: "0.85rem" }}>{char?.name}</span>
                  <span style={{ color: "#606080", fontSize: "0.75rem", marginLeft: "auto" }}>
                    Code: ***
                  </span>
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <button className="btn" onClick={() => setStep("names_codes")}>
              Back
            </button>
            <button
              className="btn btn-success btn-lg"
              onClick={handleStartGame}
              disabled={loading}
            >
              {loading ? "Creating Game..." : "Launch Game!"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
