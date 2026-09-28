/**
 * Board layout served by the backend (GET /board), traced from the original board art.
 * Coordinates are pixels in the board image.
 */

import { useEffect, useState } from "react";
import { api } from "./client";

export type SpaceType = "hallway" | "room" | "code_room" | "escape_pod" | "bio_vat" | "airlock";

export type SpaceShape =
  | { kind: "rect"; w: number; h: number; angle: number }
  | { kind: "circle"; r: number }
  | { kind: "polygon"; points: [number, number][] };

export interface BoardSpace {
  id: string;
  type: SpaceType;
  name: string;
  x: number;
  y: number;
  shape: SpaceShape;
  tags?: string[];
}

export interface BoardEdge {
  a: string;
  b: string;
  door?: boolean;
  tags?: string[];
}

export interface BoardData {
  image: { src: string; width: number; height: number };
  spaces: BoardSpace[];
  edges: BoardEdge[];
}

// The board never changes while the app runs, so fetch it once
let boardPromise: Promise<BoardData> | null = null;

function loadBoard(): Promise<BoardData> {
  if (!boardPromise) {
    boardPromise = api.getBoard().catch((err) => {
      boardPromise = null;
      throw err;
    });
  }
  return boardPromise;
}

export function useBoard(): BoardData | null {
  const [board, setBoard] = useState<BoardData | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadBoard()
      .then((data) => { if (!cancelled) setBoard(data); })
      .catch(() => { /* the board component shows a loading state */ });
    return () => { cancelled = true; };
  }, []);

  return board;
}

/** Human-readable name for a space ID, e.g. "Kitchen", "Room 5" or "Hallway". */
export function spaceLabel(board: BoardData | null, spaceId: string): string {
  return board?.spaces.find((s) => s.id === spaceId)?.name ?? spaceId;
}
