# Tetris Bot

A small pygame Tetris implementation with a built-in heuristic bot.

## Run the desktop version

```powershell
python tetris_bot.py
```

## Run the web version

Open `index.html` in a browser, or serve the folder:

```powershell
python -m http.server 8000
```

## Controls

- `B`: toggle bot/manual mode
- `F`: toggle fast mode
- `R`: restart
- Arrow keys: move and rotate in manual mode
- `Space`: hard drop
- `Esc`: quit

The bot evaluates all legal placements for the current piece and chooses the
best board state using line clears, stack height, holes, bumpiness, and wells.
