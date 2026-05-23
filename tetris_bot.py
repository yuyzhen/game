import copy
import random
from dataclasses import dataclass

import pygame


COLS = 10
ROWS = 20
CELL = 30
SIDE = 220
WIDTH = COLS * CELL + SIDE
HEIGHT = ROWS * CELL
FPS = 60

EMPTY = 0
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

COLORS = {
    EMPTY: (20, 24, 31),
    "I": (44, 196, 255),
    "O": (255, 213, 79),
    "T": (181, 126, 255),
    "S": (83, 214, 104),
    "Z": (255, 92, 92),
    "J": (82, 133, 255),
    "L": (255, 159, 67),
}


@dataclass
class Piece:
    kind: str
    matrix: list
    x: int
    y: int


def rotate_matrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def rotations(matrix):
    seen = []
    current = matrix
    for _ in range(4):
        key = tuple(tuple(row) for row in current)
        if key not in seen:
            seen.append(key)
        current = rotate_matrix(current)
    return [[list(row) for row in key] for key in seen]


def new_piece(kind=None):
    kind = kind or random.choice(list(SHAPES))
    matrix = copy.deepcopy(SHAPES[kind])
    return Piece(kind, matrix, COLS // 2 - len(matrix[0]) // 2, 0)


def make_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def collides(board, piece, dx=0, dy=0, matrix=None):
    matrix = matrix or piece.matrix
    for r, row in enumerate(matrix):
        for c, cell in enumerate(row):
            if not cell:
                continue
            x = piece.x + c + dx
            y = piece.y + r + dy
            if x < 0 or x >= COLS or y >= ROWS:
                return True
            if y >= 0 and board[y][x] != EMPTY:
                return True
    return False


def merge(board, piece):
    for r, row in enumerate(piece.matrix):
        for c, cell in enumerate(row):
            if cell:
                y = piece.y + r
                x = piece.x + c
                if 0 <= y < ROWS:
                    board[y][x] = piece.kind


def clear_lines(board):
    kept = [row for row in board if any(cell == EMPTY for cell in row)]
    cleared = ROWS - len(kept)
    for _ in range(cleared):
        kept.insert(0, [EMPTY for _ in range(COLS)])
    board[:] = kept
    return cleared


def drop_y(board, piece):
    probe = copy.deepcopy(piece)
    while not collides(board, probe, dy=1):
        probe.y += 1
    return probe.y


def column_heights(board):
    heights = []
    for x in range(COLS):
        h = 0
        for y in range(ROWS):
            if board[y][x] != EMPTY:
                h = ROWS - y
                break
        heights.append(h)
    return heights


def count_holes(board):
    holes = 0
    for x in range(COLS):
        seen_block = False
        for y in range(ROWS):
            if board[y][x] != EMPTY:
                seen_block = True
            elif seen_block:
                holes += 1
    return holes


def bumpiness(heights):
    return sum(abs(heights[i] - heights[i + 1]) for i in range(COLS - 1))


def wells(board, heights):
    total = 0
    for x, h in enumerate(heights):
        left = heights[x - 1] if x > 0 else ROWS
        right = heights[x + 1] if x < COLS - 1 else ROWS
        depth = min(left, right) - h
        if depth > 1:
            total += depth
    return total


def score_board(board, lines):
    heights = column_heights(board)
    return (
        lines * 4.6
        - sum(heights) * 0.51
        - count_holes(board) * 3.2
        - bumpiness(heights) * 0.42
        + wells(board, heights) * 0.18
    )


def best_move(board, piece):
    best = None
    best_score = float("-inf")
    for rot_index, matrix in enumerate(rotations(SHAPES[piece.kind])):
        width = len(matrix[0])
        for x in range(-2, COLS - width + 3):
            test_piece = Piece(piece.kind, copy.deepcopy(matrix), x, 0)
            if collides(board, test_piece):
                continue
            test_piece.y = drop_y(board, test_piece)
            test_board = copy.deepcopy(board)
            merge(test_board, test_piece)
            lines = clear_lines(test_board)
            score = score_board(test_board, lines)
            if score > best_score:
                best_score = score
                best = (rot_index, x)
    return best or (0, piece.x)


class Game:
    def __init__(self):
        self.board = make_board()
        self.current = new_piece()
        self.next_kind = random.choice(list(SHAPES))
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.auto = True
        self.fast = False
        self.drop_timer = 0
        self.bot_timer = 0
        self.bot_target = None

    def reset(self):
        self.__init__()

    def spawn(self):
        self.current = new_piece(self.next_kind)
        self.next_kind = random.choice(list(SHAPES))
        self.bot_target = None
        if collides(self.board, self.current):
            self.game_over = True

    def lock(self):
        merge(self.board, self.current)
        cleared = clear_lines(self.board)
        self.lines += cleared
        self.score += [0, 100, 300, 500, 800][cleared] * self.level
        self.level = 1 + self.lines // 10
        self.spawn()

    def move(self, dx):
        if not collides(self.board, self.current, dx=dx):
            self.current.x += dx

    def rotate(self):
        matrix = rotate_matrix(self.current.matrix)
        old_x = self.current.x
        for kick in (0, -1, 1, -2, 2):
            self.current.x = old_x + kick
            if not collides(self.board, self.current, matrix=matrix):
                self.current.matrix = matrix
                return
        self.current.x = old_x

    def soft_drop(self):
        if collides(self.board, self.current, dy=1):
            self.lock()
        else:
            self.current.y += 1
            self.score += 1

    def hard_drop(self):
        if self.game_over:
            return
        self.current.y = drop_y(self.board, self.current)
        self.score += 2
        self.lock()

    def bot_step(self):
        if self.bot_target is None:
            self.bot_target = best_move(self.board, self.current)
        target_rot, target_x = self.bot_target
        current_rot = rotations(SHAPES[self.current.kind]).index(self.current.matrix)
        if current_rot != target_rot:
            self.rotate()
        elif self.current.x < target_x:
            self.move(1)
        elif self.current.x > target_x:
            self.move(-1)
        else:
            self.hard_drop()

    def tick(self, dt):
        if self.game_over:
            return
        if self.auto:
            self.bot_timer += dt
            delay = 260 if not self.fast else 45
            while self.bot_timer >= delay and not self.game_over:
                self.bot_timer -= delay
                self.bot_step()
            return
        self.drop_timer += dt
        speed = max(70, 550 - (self.level - 1) * 45)
        if self.fast:
            speed = 35
        if self.drop_timer >= speed:
            self.drop_timer = 0
            self.soft_drop()


def draw_text(surface, text, size, x, y, color=(232, 236, 244)):
    font = pygame.font.SysFont("consolas", size, bold=True)
    surface.blit(font.render(text, True, color), (x, y))


def draw_piece(surface, piece, ox=0, oy=0, ghost=False):
    color = COLORS[piece.kind]
    if ghost:
        color = tuple(max(30, int(v * 0.45)) for v in color)
    for r, row in enumerate(piece.matrix):
        for c, cell in enumerate(row):
            if not cell:
                continue
            rect = pygame.Rect(
                ox + (piece.x + c) * CELL,
                oy + (piece.y + r) * CELL,
                CELL,
                CELL,
            )
            pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=4)


def draw(game, screen):
    screen.fill((13, 17, 23))
    board_rect = pygame.Rect(0, 0, COLS * CELL, ROWS * CELL)
    pygame.draw.rect(screen, (16, 21, 29), board_rect)

    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, (33, 40, 51), rect, 1)
            cell = game.board[y][x]
            if cell != EMPTY:
                pygame.draw.rect(screen, COLORS[cell], rect.inflate(-2, -2), border_radius=4)

    if not game.game_over:
        ghost = copy.deepcopy(game.current)
        ghost.y = drop_y(game.board, ghost)
        draw_piece(screen, ghost, ghost=True)
        draw_piece(screen, game.current)

    panel_x = COLS * CELL + 22
    pygame.draw.rect(screen, (19, 24, 32), (COLS * CELL, 0, SIDE, HEIGHT))
    draw_text(screen, "TETRIS BOT", 24, panel_x, 24)
    draw_text(screen, f"Score {game.score}", 18, panel_x, 78)
    draw_text(screen, f"Lines {game.lines}", 18, panel_x, 108)
    draw_text(screen, f"Level {game.level}", 18, panel_x, 138)
    draw_text(screen, f"Mode  {'BOT' if game.auto else 'MANUAL'}", 18, panel_x, 184)
    draw_text(screen, f"Speed {'FAST' if game.fast else 'NORMAL'}", 18, panel_x, 214)

    draw_text(screen, "Next", 18, panel_x, 270)
    preview = Piece(game.next_kind, SHAPES[game.next_kind], 0, 0)
    for r, row in enumerate(preview.matrix):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(panel_x + c * 26, 305 + r * 26, 24, 24)
                pygame.draw.rect(screen, COLORS[game.next_kind], rect, border_radius=4)

    hints = [
        "B  toggle bot",
        "F  fast mode",
        "R  restart",
        "Arrows move",
        "Up rotate",
        "Space drop",
    ]
    for i, hint in enumerate(hints):
        draw_text(screen, hint, 14, panel_x, 415 + i * 24, (172, 183, 199))

    if game.game_over:
        overlay = pygame.Surface((COLS * CELL, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "GAME OVER", 32, 50, 250, (255, 235, 160))
        draw_text(screen, "Press R", 20, 100, 300)

    pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption("Tetris Bot")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_b:
                    game.auto = not game.auto
                    game.bot_target = None
                elif event.key == pygame.K_f:
                    game.fast = not game.fast
                elif not game.auto and not game.game_over:
                    if event.key == pygame.K_LEFT:
                        game.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1)
                    elif event.key == pygame.K_DOWN:
                        game.soft_drop()
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()

        game.tick(dt)
        draw(game, screen)

    pygame.quit()


if __name__ == "__main__":
    main()
