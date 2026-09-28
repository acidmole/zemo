import { useState } from "react";
import type { CharacterState } from "../../api/types";
import { spaceLabel, useBoard } from "../../api/board";

interface Props {
  player: CharacterState | null;
  onDropCards?: (cardIds: string[]) => void;
}

export function PlayerInfo({ player, onDropCards }: Props) {
  const board = useBoard();
  const [showCode, setShowCode] = useState(false);
  const [selectedDrop, setSelectedDrop] = useState<Set<string>>(new Set());

  if (!player) {
    return (
      <div className="panel" style={{ height: "100%" }}>
        <div className="panel-title">Player Info</div>
        <p style={{ color: "#606080", fontSize: "0.8rem" }}>No player selected</p>
      </div>
    );
  }

  const totalWeight = player.hand.reduce((sum, c) => sum + c.weight, 0);
  const isOverCapacity = totalWeight > player.capacity;

  const toggleDrop = (cardId: string) => {
    setSelectedDrop((prev) => {
      const next = new Set(prev);
      if (next.has(cardId)) next.delete(cardId);
      else next.add(cardId);
      return next;
    });
  };

  const handleDrop = () => {
    if (onDropCards && selectedDrop.size > 0) {
      onDropCards(Array.from(selectedDrop));
      setSelectedDrop(new Set());
    }
  };

  return (
    <div className="panel" style={{ height: "100%" }}>
      <div className="panel-title">Current Player</div>

      {/* Character portrait / header */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: "50%",
            backgroundColor: player.color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 800,
            fontSize: "1rem",
            color: "#fff",
            flexShrink: 0,
          }}
        >
          {player.name.charAt(0)}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.85rem", color: player.color }}>
            {player.name}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#9090b0" }}>
            Player {player.player_id + 1}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ fontSize: "0.75rem", marginBottom: 6 }}>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
          <span style={{ color: "#9090b0" }}>Health</span>
          <span style={{ color: player.health <= 3 ? "#ff3355" : "#e0e0e0", fontFamily: "monospace" }}>
            {player.health} / {player.max_health}
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
          <span style={{ color: "#9090b0" }}>Position</span>
          <span>{spaceLabel(board, player.position)}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
          <span style={{ color: "#9090b0" }}>Weight</span>
          <span style={{ color: isOverCapacity ? "#ff3355" : "#e0e0e0", fontFamily: "monospace" }}>
            {totalWeight} / {player.capacity}
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
          <span style={{ color: "#9090b0" }}>Actions</span>
          <span style={{ fontFamily: "monospace" }}>
            {player.actions_taken_this_turn} / {player.actions_per_turn}
          </span>
        </div>
        {player.combat_mod !== 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
            <span style={{ color: "#9090b0" }}>Combat Mod</span>
            <span style={{ fontFamily: "monospace", color: "#00ff88" }}>+{player.combat_mod}</span>
          </div>
        )}
      </div>

      {/* Escape Code (hidden) */}
      <div
        style={{
          fontSize: "0.75rem",
          padding: "4px 6px",
          background: "#111128",
          borderRadius: 4,
          marginBottom: 8,
          cursor: "pointer",
          border: "1px solid #2a2a4a",
        }}
        onClick={() => setShowCode(!showCode)}
      >
        <span style={{ color: "#9090b0" }}>Escape Code: </span>
        <span style={{ color: "#aa00ff", fontFamily: "monospace", fontWeight: 700 }}>
          {showCode ? player.escape_code : "***"}
        </span>
        <span style={{ color: "#606080", fontSize: "0.6rem", marginLeft: 4 }}>
          (click to {showCode ? "hide" : "reveal"})
        </span>
      </div>

      {/* Hand */}
      <div style={{ fontSize: "0.7rem", color: "#00aaff", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Hand ({player.hand.length} cards)
      </div>
      {player.hand.length === 0 && (
        <p style={{ color: "#606080", fontSize: "0.75rem" }}>No cards</p>
      )}
      {player.hand.map((card) => (
        <div
          key={card.id}
          className={`card-item ${card.card_type === "trap" ? "trap" : ""}`}
          style={onDropCards ? { cursor: "pointer" } : undefined}
          onClick={onDropCards ? () => toggleDrop(card.id) : undefined}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="card-name">{card.name}</span>
            {onDropCards && (
              <input
                type="checkbox"
                checked={selectedDrop.has(card.id)}
                onChange={() => toggleDrop(card.id)}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: "#ff3355" }}
              />
            )}
          </div>
          <div className="card-desc">{card.description}</div>
          <div className="card-weight">Weight: {card.weight}</div>
        </div>
      ))}

      {/* Drop cards UI */}
      {onDropCards && isOverCapacity && (
        <div style={{ marginTop: 6 }}>
          <div style={{ fontSize: "0.7rem", color: "#ff3355", marginBottom: 4 }}>
            Over capacity! Select cards to drop.
          </div>
          <button
            className="btn btn-danger btn-sm"
            onClick={handleDrop}
            disabled={selectedDrop.size === 0}
          >
            Drop {selectedDrop.size} card(s)
          </button>
        </div>
      )}
    </div>
  );
}
