const COLS = 10;
const ROWS = 20;
const CELL = 30;
const EMPTY = 0;

const SHAPES = {
  I: [[1, 1, 1, 1]],
  O: [
    [1, 1],
    [1, 1],
  ],
  T: [
    [0, 1, 0],
    [1, 1, 1],
  ],
  S: [
    [0, 1, 1],
    [1, 1, 0],
  ],
  Z: [
    [1, 1, 0],
    [0, 1, 1],
  ],
  J: [
    [1, 0, 0],
    [1, 1, 1],
  ],
  L: [
    [0, 0, 1],
    [1, 1, 1],
  ],
};

const COLORS = {
  0: "#151b26",
  I: "#2cc4ff",
  O: "#ffd54f",
  T: "#b57eff",
  S: "#53d668",
  Z: "#ff5c5c",
  J: "#5285ff",
  L: "#ff9f43",
};

const boardCanvas = document.querySelector("#board");
const ctx = boardCanvas.getContext("2d");
const nextCanvas = document.querySelector("#next");
const nextCtx = nextCanvas.getContext("2d");
const scoreEl = document.querySelector("#score");
const linesEl = document.querySelector("#lines");
const levelEl = document.querySelector("#level");
const modeEl = document.querySelector("#mode");
const toggleBot = document.querySelector("#toggleBot");
const toggleSpeed = document.querySelector("#toggleSpeed");
const restart = document.querySelector("#restart");

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function rotate(matrix) {
  return matrix[0].map((_, index) => matrix.map((row) => row[index]).reverse());
}

function rotations(matrix) {
  const result = [];
  let current = clone(matrix);
  for (let i = 0; i < 4; i += 1) {
    const key = JSON.stringify(current);
    if (!result.some((item) => JSON.stringify(item) === key)) result.push(clone(current));
    current = rotate(current);
  }
  return result;
}

function makeBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(EMPTY));
}

function randomKind() {
  return Object.keys(SHAPES)[Math.floor(Math.random() * Object.keys(SHAPES).length)];
}

function newPiece(kind = randomKind()) {
  const matrix = clone(SHAPES[kind]);
  return { kind, matrix, x: Math.floor(COLS / 2) - Math.floor(matrix[0].length / 2), y: 0 };
}

function collides(board, piece, dx = 0, dy = 0, matrix = piece.matrix) {
  for (let r = 0; r < matrix.length; r += 1) {
    for (let c = 0; c < matrix[r].length; c += 1) {
      if (!matrix[r][c]) continue;
      const x = piece.x + c + dx;
      const y = piece.y + r + dy;
      if (x < 0 || x >= COLS || y >= ROWS) return true;
      if (y >= 0 && board[y][x] !== EMPTY) return true;
    }
  }
  return false;
}

function merge(board, piece) {
  piece.matrix.forEach((row, r) => {
    row.forEach((cell, c) => {
      if (cell && piece.y + r >= 0) board[piece.y + r][piece.x + c] = piece.kind;
    });
  });
}

function clearLines(board) {
  const kept = board.filter((row) => row.some((cell) => cell === EMPTY));
  const cleared = ROWS - kept.length;
  while (kept.length < ROWS) kept.unshift(Array(COLS).fill(EMPTY));
  board.splice(0, ROWS, ...kept);
  return cleared;
}

function dropY(board, piece) {
  const probe = clone(piece);
  while (!collides(board, probe, 0, 1)) probe.y += 1;
  return probe.y;
}

function heights(board) {
  return Array.from({ length: COLS }, (_, x) => {
    for (let y = 0; y < ROWS; y += 1) {
      if (board[y][x] !== EMPTY) return ROWS - y;
    }
    return 0;
  });
}

function holes(board) {
  let total = 0;
  for (let x = 0; x < COLS; x += 1) {
    let block = false;
    for (let y = 0; y < ROWS; y += 1) {
      if (board[y][x] !== EMPTY) block = true;
      else if (block) total += 1;
    }
  }
  return total;
}

function bumpiness(values) {
  let total = 0;
  for (let i = 0; i < values.length - 1; i += 1) total += Math.abs(values[i] - values[i + 1]);
  return total;
}

function wells(values) {
  let total = 0;
  values.forEach((height, x) => {
    const left = x > 0 ? values[x - 1] : ROWS;
    const right = x < COLS - 1 ? values[x + 1] : ROWS;
    const depth = Math.min(left, right) - height;
    if (depth > 1) total += depth;
  });
  return total;
}

function scoreBoard(board, lines) {
  const h = heights(board);
  return lines * 4.6 - h.reduce((a, b) => a + b, 0) * 0.51 - holes(board) * 3.2 - bumpiness(h) * 0.42 + wells(h) * 0.18;
}

function bestMove(board, piece) {
  let best = null;
  let bestScore = -Infinity;
  rotations(SHAPES[piece.kind]).forEach((matrix, rotationIndex) => {
    for (let x = -2; x <= COLS - matrix[0].length + 2; x += 1) {
      const testPiece = { kind: piece.kind, matrix: clone(matrix), x, y: 0 };
      if (collides(board, testPiece)) continue;
      testPiece.y = dropY(board, testPiece);
      const testBoard = clone(board);
      merge(testBoard, testPiece);
      const lines = clearLines(testBoard);
      const score = scoreBoard(testBoard, lines);
      if (score > bestScore) {
        bestScore = score;
        best = { rotationIndex, x };
      }
    }
  });
  return best || { rotationIndex: 0, x: piece.x };
}

const game = {
  board: makeBoard(),
  current: newPiece(),
  nextKind: randomKind(),
  score: 0,
  lines: 0,
  level: 1,
  auto: true,
  fast: false,
  over: false,
  dropTimer: 0,
  botTimer: 0,
  botTarget: null,
};

function reset() {
  Object.assign(game, {
    board: makeBoard(),
    current: newPiece(),
    nextKind: randomKind(),
    score: 0,
    lines: 0,
    level: 1,
    auto: true,
    fast: false,
    over: false,
    dropTimer: 0,
    botTimer: 0,
    botTarget: null,
  });
}

function spawn() {
  game.current = newPiece(game.nextKind);
  game.nextKind = randomKind();
  game.botTarget = null;
  if (collides(game.board, game.current)) game.over = true;
}

function lock() {
  merge(game.board, game.current);
  const cleared = clearLines(game.board);
  game.lines += cleared;
  game.score += [0, 100, 300, 500, 800][cleared] * game.level;
  game.level = 1 + Math.floor(game.lines / 10);
  spawn();
}

function move(dx) {
  if (!collides(game.board, game.current, dx, 0)) game.current.x += dx;
}

function rotateCurrent() {
  const matrix = rotate(game.current.matrix);
  const oldX = game.current.x;
  for (const kick of [0, -1, 1, -2, 2]) {
    game.current.x = oldX + kick;
    if (!collides(game.board, game.current, 0, 0, matrix)) {
      game.current.matrix = matrix;
      return;
    }
  }
  game.current.x = oldX;
}

function softDrop() {
  if (collides(game.board, game.current, 0, 1)) lock();
  else {
    game.current.y += 1;
    game.score += 1;
  }
}

function hardDrop() {
  game.current.y = dropY(game.board, game.current);
  game.score += 2;
  lock();
}

function botStep() {
  if (!game.botTarget) game.botTarget = bestMove(game.board, game.current);
  const rotationIndex = rotations(SHAPES[game.current.kind]).findIndex((item) => JSON.stringify(item) === JSON.stringify(game.current.matrix));
  if (rotationIndex !== game.botTarget.rotationIndex) rotateCurrent();
  else if (game.current.x < game.botTarget.x) move(1);
  else if (game.current.x > game.botTarget.x) move(-1);
  else hardDrop();
}

function update(dt) {
  if (game.over) return;
  if (game.auto) {
    game.botTimer += dt;
    const delay = game.fast ? 45 : 260;
    while (game.botTimer >= delay && !game.over) {
      game.botTimer -= delay;
      botStep();
    }
    return;
  }
  game.dropTimer += dt;
  const speed = game.fast ? 35 : Math.max(70, 550 - (game.level - 1) * 45);
  if (game.dropTimer >= speed) {
    game.dropTimer = 0;
    softDrop();
  }
}

function drawCell(context, x, y, color, size = CELL) {
  context.fillStyle = color;
  context.fillRect(x * size + 1, y * size + 1, size - 2, size - 2);
}

function drawPiece(context, piece, ghost = false) {
  context.globalAlpha = ghost ? 0.36 : 1;
  piece.matrix.forEach((row, r) => {
    row.forEach((cell, c) => {
      if (cell) drawCell(context, piece.x + c, piece.y + r, COLORS[piece.kind]);
    });
  });
  context.globalAlpha = 1;
}

function render() {
  ctx.fillStyle = "#151b26";
  ctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  ctx.strokeStyle = "#273142";
  for (let x = 0; x <= COLS; x += 1) {
    ctx.beginPath();
    ctx.moveTo(x * CELL, 0);
    ctx.lineTo(x * CELL, ROWS * CELL);
    ctx.stroke();
  }
  for (let y = 0; y <= ROWS; y += 1) {
    ctx.beginPath();
    ctx.moveTo(0, y * CELL);
    ctx.lineTo(COLS * CELL, y * CELL);
    ctx.stroke();
  }
  game.board.forEach((row, y) => row.forEach((cell, x) => cell !== EMPTY && drawCell(ctx, x, y, COLORS[cell])));
  if (!game.over) {
    const ghost = clone(game.current);
    ghost.y = dropY(game.board, ghost);
    drawPiece(ctx, ghost, true);
    drawPiece(ctx, game.current);
  } else {
    ctx.fillStyle = "rgba(0, 0, 0, 0.62)";
    ctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
    ctx.fillStyle = "#ffeaa7";
    ctx.font = "700 30px Inter, sans-serif";
    ctx.fillText("GAME OVER", 50, 280);
  }

  nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
  const shape = SHAPES[game.nextKind];
  shape.forEach((row, y) => row.forEach((cell, x) => cell && drawCell(nextCtx, x + 1, y + 1, COLORS[game.nextKind], 24)));

  scoreEl.textContent = game.score;
  linesEl.textContent = game.lines;
  levelEl.textContent = game.level;
  modeEl.textContent = game.auto ? "BOT" : "MANUAL";
  toggleBot.textContent = game.auto ? "Bot" : "Manual";
  toggleSpeed.textContent = game.fast ? "Fast" : "Normal";
}

let last = performance.now();
function loop(now) {
  update(now - last);
  last = now;
  render();
  requestAnimationFrame(loop);
}

document.addEventListener("keydown", (event) => {
  if (event.code === "KeyR") reset();
  if (event.code === "KeyB") {
    game.auto = !game.auto;
    game.botTarget = null;
  }
  if (event.code === "KeyF") game.fast = !game.fast;
  if (game.auto || game.over) return;
  if (event.code === "ArrowLeft") move(-1);
  if (event.code === "ArrowRight") move(1);
  if (event.code === "ArrowDown") softDrop();
  if (event.code === "ArrowUp") rotateCurrent();
  if (event.code === "Space") {
    event.preventDefault();
    hardDrop();
  }
});

toggleBot.addEventListener("click", () => {
  game.auto = !game.auto;
  game.botTarget = null;
});
toggleSpeed.addEventListener("click", () => {
  game.fast = !game.fast;
});
restart.addEventListener("click", reset);

requestAnimationFrame(loop);
