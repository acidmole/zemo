import type {
  GameConfig,
  CreateGameResponse,
  GameStateResponse,
  RollMovementResponse,
  MoveRequest,
  MoveResponse,
  ActionRequest,
  ActionResponse,
  DropCardsRequest,
  ListSavesResponse,
} from "./types";

const BASE_URL = "/api";

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

export const api = {
  createGame: (config: GameConfig) =>
    apiFetch<CreateGameResponse>("/game/create", {
      method: "POST",
      body: JSON.stringify({ config }),
    }),

  getState: (gameId: string) =>
    apiFetch<GameStateResponse>(`/game/${gameId}/state`),

  rollMovement: (gameId: string, characterId: string) =>
    apiFetch<RollMovementResponse>(`/game/${gameId}/roll-movement`, {
      method: "POST",
      body: JSON.stringify({ character_id: characterId }),
    }),

  move: (gameId: string, req: MoveRequest) =>
    apiFetch<MoveResponse>(`/game/${gameId}/move`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  action: (gameId: string, req: ActionRequest) =>
    apiFetch<ActionResponse>(`/game/${gameId}/action`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  dropCards: (gameId: string, req: DropCardsRequest) =>
    apiFetch<GameStateResponse>(`/game/${gameId}/drop-cards`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  listSaves: () => apiFetch<ListSavesResponse>("/saves/"),

  restoreGame: (gameId: string) =>
    apiFetch<CreateGameResponse>(`/saves/restore/${gameId}`, {
      method: "POST",
    }),

  deleteSave: (gameId: string) =>
    apiFetch<{ deleted: boolean; game_id: string }>(`/saves/${gameId}`, {
      method: "DELETE",
    }),
};

export { ApiError };
