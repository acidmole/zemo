import { useState, useEffect, useCallback } from "react";
import type { SaveInfo, GameState } from "../../api/types";
import { api, ApiError } from "../../api/client";

interface Props {
  onGameRestored: (gameId: string, state: GameState) => void;
}

export function SavedGames({ onGameRestored }: Props) {
  const [saves, setSaves] = useState<SaveInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSaves = useCallback(async () => {
    try {
      const resp = await api.listSaves();
      setSaves(resp.saves);
    } catch {
      // Silently ignore — saves endpoint may not be available
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSaves();
  }, [fetchSaves]);

  const handleRestore = useCallback(
    async (gameId: string) => {
      setRestoring(gameId);
      setError(null);
      try {
        const resp = await api.restoreGame(gameId);
        onGameRestored(resp.game_id, resp.state);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.detail : "Failed to restore game."
        );
        setRestoring(null);
      }
    },
    [onGameRestored]
  );

  const handleDelete = useCallback(
    async (gameId: string) => {
      try {
        await api.deleteSave(gameId);
        setSaves((prev) => prev.filter((s) => s.game_id !== gameId));
      } catch {
        // ignore
      }
    },
    []
  );

  if (loading) return null;
  if (saves.length === 0) return null;

  return (
    <div className="panel" style={{ marginTop: 20 }}>
      <h4 style={{ margin: "0 0 12px 0", fontSize: "0.95rem" }}>
        Saved Games
      </h4>
      {error && (
        <div
          style={{
            color: "#ff3355",
            fontSize: "0.8rem",
            marginBottom: 8,
          }}
        >
          {error}
        </div>
      )}
      {saves.map((save) => {
        const date = save.last_activity
          ? new Date(save.last_activity).toLocaleString()
          : "Unknown";
        return (
          <div
            key={save.game_id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "8px 0",
              borderBottom: "1px solid #2a2a4a",
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: "0.85rem",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {save.player_names.join(", ")}
              </div>
              <div style={{ fontSize: "0.7rem", color: "#9090b0" }}>
                {save.event_count} events &middot; {date}
              </div>
            </div>
            <button
              className="btn btn-primary"
              style={{ fontSize: "0.75rem", padding: "4px 12px" }}
              onClick={() => handleRestore(save.game_id)}
              disabled={restoring !== null}
            >
              {restoring === save.game_id ? "Restoring..." : "Restore"}
            </button>
            <button
              className="btn"
              style={{
                fontSize: "0.7rem",
                padding: "4px 8px",
                color: "#ff3355",
              }}
              onClick={() => handleDelete(save.game_id)}
              disabled={restoring !== null}
            >
              X
            </button>
          </div>
        );
      })}
    </div>
  );
}
