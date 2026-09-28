# Space Station Zemo - Digital Board Game

A digital adaptation of the "Space Station Zemo" board game (originally from InQuest magazine). 2-4 players compete to escape a doomed space station by setting code rooms and boarding the escape pod — or by being the last one standing.

## Quick Start

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open the Game

Navigate to **http://localhost:5173** in your browser.

### Alternative: Docker

**Development** (hot-reload for both backend and frontend):

```bash
docker compose up
```

Open **http://localhost:5173**. Source changes in `backend/app/` and `frontend/src/` are reflected immediately.

**Production** (nginx serves static frontend, proxies API to backend):

```bash
docker compose -f docker-compose.prod.yml up --build
```

Open **http://localhost:80**.

---

## How to Play (Testing Guide)

### Game Setup

1. Open the app — you'll see the **Game Setup** wizard
2. Choose **number of players** (2-4)
3. Each player **picks a character** from the 5 available:
   - **Chuckie the Zombie** (HP 20, +2 combat) — the tank
   - **Mush the Abomination** (HP 19, +2 combat) — another brawler
   - **Floyd the Droid** (HP 18) — balanced
   - **Pete the Cook** (HP 13, 2 actions/turn) — versatile commando
   - **The Rats** (HP 9) — fragile but scrappy
4. Enter **player names** and secretly pick an **escape code** (AAA through BBB)
5. Click **Start Game** — each character starts in a random numbered room (2d6 multiplied)

### Movement Phase

Each round starts with all players moving in order (highest HP first):

1. Click **Roll Dice** to roll 2d6 + movement modifier
2. **Reachable spaces glow green** on the board — click one to move there
3. Or click **Stay Here** to remain in place
4. Rules: each hallway square or room entered costs one step; rooms are entered through their doors. You cannot enter/pass through a **hallway square** occupied by another character; **rooms** allow multiple occupants and can be passed through

### Action Phase

After all players move, each player gets 1 action (Pete gets 2 different ones):

- **Pick** — Pick up face-down card(s) at your space. Traps trigger immediately!
- **Fight** — Melee combat with a character in your space or an adjacent space. Select a target and optionally a weapon. Both sides roll 2d6 + combat mod + weapon bonus. Loser takes damage = difference. Winner can choose to continue fighting.
- **Push Code** — In a Code Room, roll 1d6 to set the code to A or B (need 4+, Pod ATM Card gives +3)
- **Heal** — In the Bio-Vat only. Roll 2d6 to regain HP (capped at starting max)
- **Pass** — Do nothing

### Winning

- **Escape Pod Win**: All 3 code rooms match your secret code + you're in the Escape Pod + you have a Pod ATM Card
- **Last Survivor**: All other players are permanently dead

### Death & Bio-Vat

- Reaching 0 HP sends you to the **Bio-Vat** (your items drop at your death location)
- In the Bio-Vat, use **Heal** action to roll 2d6 and regain HP
- Once HP > 0, you can leave during the next movement phase
- A "Get Out of Bio-Vat Free" card instantly restores you to max HP on death
- Once **all characters have been regrown at least once**, the Bio-Vat shuts down — future deaths are **permanent**!

---

## Working Features (Phase 1 MVP)

### Backend (Python/FastAPI)
- [x] Complete game state machine with turn flow
- [x] 2-4 player game creation with character selection
- [x] Secret escape code selection (8 codes: AAA through BBB)
- [x] 36-card deck: shuffled and dealt (one to each of rooms 1-32, 4 to recycling bin)
- [x] 2d6 x multiply starting room rolls
- [x] Turn order by health (highest first), recalculated each round
- [x] Two-phase rounds: Movement then Actions
- [x] Movement: 2d6 + modifier, BFS pathfinding with hallway blocking
- [x] Pick action: reveal cards, trigger traps (Banana Peel, Bucket of Anti-Matter)
- [x] Fight action: melee combat with 2d6 + combat mod + weapon bonus, damage = difference
- [x] Push action: roll 1d6 in Code Room to set A/B (4+ success, Pod ATM Card +3 bonus)
- [x] Heal action: roll 2d6 in Bio-Vat to regain HP
- [x] Pass action
- [x] Pete the Cook: 2 different actions per turn (Commando Training)
- [x] Pete gets +2 combat in Kitchen
- [x] Reactor Room: 1 HP radiation damage at start of action phase
- [x] Carry capacity (weight 5), drop cards when over
- [x] Death -> Bio-Vat, drop items, Get Out of Bio-Vat Free card
- [x] Bio-Vat shutdown after all characters regrown
- [x] Permanent elimination after Bio-Vat shutdown
- [x] Win condition: Escape Pod (codes match + in pod + have Pod ATM Card)
- [x] Win condition: Last Survivor
- [x] Full card deck with all item stats (weapons, movement bonuses, code bonuses, etc.)
- [x] Game event log
- [x] Save/restore via event sourcing (JSONL event log with RNG state capture)
- [x] Deterministic replay — restore any game to its exact state
- [x] REST endpoints for listing, restoring, and deleting saves

### Frontend (React/TypeScript/Vite)
- [x] Game setup wizard (player count, character selection, names, escape codes)
- [x] Saved games panel on setup screen (list, restore, delete)
- [x] Board built from the original printed board: the artwork is the background, with 112 hallway squares, rooms 1-32, 6 special rooms and their doors traced on top
- [x] Hallway squares, rooms and doors match the printed board, including the diagonal corridors, striped belts and the ring around the Escape Pod
- [x] Character tokens on board with color and initials
- [x] Multiple tokens on same space (offset rendering)
- [x] Current player pulse animation
- [x] Reachable spaces highlighted during movement
- [x] Click-to-move on highlighted spaces
- [x] Dice roll animation
- [x] Health track sidebar (all characters)
- [x] Player info panel (cards in hand, stats, carry weight)
- [x] Escape code display (click to reveal)
- [x] Turn indicator (round, player, phase)
- [x] Action bar with available actions
- [x] Fight dialog (target selection, weapon choice, roll results, continue/stop)
- [x] Card pickup display (items found, traps triggered)
- [x] Code room push dialog (A/B selection)
- [x] Over-capacity card drop UI
- [x] Game log (scrollable, last 20 events)
- [x] Game over screen with winner display
- [x] Dark space theme with neon accents
- [x] Card count indicators on rooms
- [x] Code room A/B/? status badges

---

## Not Yet Implemented (Future Phases)

### Phase 2: Full Card Effects
- [ ] Shooting combat (ranged weapons: Gadzooka, Machete Launcher, Atomic Stapler, etc.)
- [ ] Duck action (defend against shooting when you have no ranged weapon)
- [ ] ACME Rocket Skates movement bonus (card is defined but passive bonus not applied in movement)
- [ ] Implosion Belt (both fighters to 0 HP)
- [ ] Deluxe Moon Pie (+1d6 in fight, consumed after use)
- [ ] InQuest #0 (force card trade before fight)
- [ ] Lucky Lemming's Foot (auto-duck)
- [ ] Molecular Blender (move through walls)
- [ ] Particle Accelerator (extra 2d6 movement + 1d6 damage to self)
- [ ] Witless Relocation Program (teleport via 2d6 multiply)
- [ ] InfraX-Goggles (peek at face-down cards in adjacent space)
- [ ] Telepathy Helmet (look at another player's hand)
- [ ] Portable Black Hole (carry 1 item weightless, risk of destruction)
- [ ] Really Heavy Remote Control (change any Code Room remotely)
- [ ] Banana Peel "lose next action" effect (trap damage works, but action loss not tracked)

### Phase 3: Room Effects
- [ ] Security Room (roll 1d6: alarm, look at hand, open/close airlock)
- [ ] The Brig (cannot leave normally, must roll 4-6 to escape)
- [ ] The Armory (take a weapon from recycling bin)
- [ ] Vending Machines (roll 1d6 for random effect)
- [ ] Lavatory (discard cards to recycling bin)
- [ ] Lost and Found (roll 1d6 for recycling bin card)
- [ ] Casino (wager a card, roll to keep or lose)
- [ ] The Zemo Zoo (roll 1d6 for creature encounter)
- [ ] Command Control (roll 1d6 to adjust climate/gravity)

### Phase 4: Character Special Abilities
- [ ] Chuckie: Exploding Polyps (drop polyps to damage pursuers)
- [ ] Floyd: Transformer Chassis (reallocate stats between speed/combat/hauling)
- [ ] Mush: Der Blinkenteleporten (teleport instead of normal movement)
- [ ] Pete: Commando Training is implemented; Kitchen bonus is implemented
- [ ] The Rats: Rat Packs (split into two counters)
- [ ] Special/reactive actions (fight back or duck when attacked, for Chuckie/Rats/Floyd)

### Phase 5: AI Opponents
- [ ] Heuristic-based AI bots for single-player games
- [ ] AI difficulty levels

### Phase 6: Advanced Board Features
- [ ] Airlock mechanics (suck players toward airlock, death in space)
- [ ] Security Field (odd-roll restriction between Brig and Armory; the crossing is tagged `security_field` in the board data)
- [ ] X-Ray Zone (reveal cards when passing through; the two green ring sectors are tagged `x_ray`)
- [ ] Climate Control effects (gravity changes, life support)

### Phase 7: Polish & Multiplayer
- [ ] WebSocket real-time state push (currently uses REST polling)
- [ ] Online multiplayer (non-hot-seat)
- [x] ~~Persistent game storage~~ (implemented via event-sourced save/restore)
- [ ] Sound effects and music
- [ ] Card artwork/illustrations
- [ ] Character portraits
- [ ] Animated token movement along paths
- [ ] Dice roll 3D animation
- [ ] Mobile-responsive layout
- [ ] Tutorial/help overlay

---

## Tech Stack

| Layer    | Technology                  |
|----------|-----------------------------|
| Backend  | Python 3.12+, FastAPI, Pydantic, Uvicorn |
| Frontend | React 19, TypeScript, Vite 6 |
| Board    | Original board art + SVG overlay (no canvas) |
| State    | Server-side (all logic in Python) |
| API      | REST (JSON)                 |

## Project Structure

```
zemo/
  backend/
    app/
      main.py              # FastAPI app entry point
      models/
        game_state.py      # Pydantic models (GameState, Character, Card, etc.)
        actions.py         # Request/response models (incl. SaveInfo)
      engine/
        game.py            # Core game state machine
        board.py           # Board graph, BFS pathfinding
        combat.py          # Fight resolution
        dice.py            # Dice utilities
        rng.py             # RNG state capture/replay for deterministic saves
        event_log.py       # JSONL event logger and replayer
      data/
        board.json         # Traced board: spaces, shapes, doors (generated)
        board_layout.py    # Loads board.json into the movement graph
        characters.py      # 5 character stat blocks
        cards.py           # 36 card definitions
      routes/
        game_routes.py     # Game API endpoints
        save_routes.py     # Save/restore API endpoints
    saves/                 # Auto-created; JSONL save files per game
    requirements.txt
  frontend/
    src/
      api/
        client.ts          # Fetch wrapper for backend API
        types.ts           # TypeScript types matching Pydantic models
        board.ts           # Board data from GET /board, useBoard hook
        boardData.ts       # Character templates and escape codes
      components/
        Board/             # Board art with space highlights, tokens, code room badges
        HUD/               # Health track, player info, turn indicator
        Actions/           # Action bar, movement UI, fight dialog, card inspect
        Setup/             # Game setup wizard, dice roll, saved games panel
      hooks/
        useGameState.ts    # Game state management hook
      styles/
        global.css         # Dark space theme
      App.tsx              # Main app orchestration
      main.tsx             # Entry point
    public/
      board.webp           # Board image stitched from the PDF (generated)
    package.json
    vite.config.ts
  shared/                  # Original board game PDFs (reference)
  tools/
    build_board.py         # Stitches the PDF board tiles into board.webp
    board_trace.py         # Hand-traced board data; generates board.json
  README.md
```

## API Endpoints

| Method | Path                          | Description                 |
|--------|-------------------------------|-----------------------------|
| GET    | `/`                           | Health check                |
| GET    | `/board`                      | Board image, spaces and connections |
| POST   | `/game/create`                | Create a new game           |
| GET    | `/game/{id}/state`            | Get current game state      |
| POST   | `/game/{id}/roll-movement`    | Roll movement dice          |
| POST   | `/game/{id}/move`             | Move character to a space   |
| POST   | `/game/{id}/action`           | Perform an action           |
| POST   | `/game/{id}/drop-cards`       | Drop cards (carry capacity) |
| GET    | `/saves/`                     | List all saved games        |
| POST   | `/saves/restore/{id}`         | Restore a game from save    |
| DELETE | `/saves/{id}`                 | Delete a save file          |

## Board Data

The board comes from `shared/SSZemo_Stand_Ups-n-Board.pdf`, pages 2-10, which are nine tiles of one board. Two scripts in `tools/` produce the generated files:

```bash
uv run --with pillow python tools/build_board.py   # frontend/public/board.webp (needs pdftoppm)
python tools/board_trace.py                        # backend/app/data/board.json
```

All coordinates in `board_trace.py` are pixels in `board.webp`, so change the image build only together with the tracing. The straight hallways sit on a 22 x 13 grid. The diagonal corridors, striped belts, pod ring sectors, room anchors and doors are listed explicitly. Save files created before this board use the old space IDs and will not restore.

## Save/Restore System

Games are automatically saved as they are played. Every game-mutating action (create, roll, move, action, drop cards) is logged to a JSONL file in `backend/saves/` along with a snapshot of the Python RNG state at that moment. This enables **deterministic replay** — restoring a game replays every recorded event with the exact same random state, reproducing the identical game state.

- **Automatic**: no manual "save" button needed; every action is logged as it happens
- **Deterministic**: RNG state capture ensures shuffles, dice rolls, and combat resolve identically on replay
- **Resumable**: if the server restarts, saved games appear on the setup screen and can be restored with one click
- **Format**: one JSONL file per game at `backend/saves/game_<id>.jsonl`
