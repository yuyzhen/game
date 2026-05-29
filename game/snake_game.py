import pygame
import random
import sys
import math
from collections import deque

# ─── 初始化 ───
pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_W = WIDTH // GRID_SIZE
GRID_H = HEIGHT // GRID_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("贪吃蛇")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 22)

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

# ─── 调色板 ───
# 深空风格
BG = (15, 15, 25)
GRID_LINE = (30, 30, 50)
BORDER = (50, 50, 80)

# 蛇身渐变（青→绿）
SNAKE_COLORS = [
    (0, 220, 180),   # 头 - 青绿
    (0, 200, 160),
    (0, 180, 140),
    (0, 160, 120),
    (0, 140, 100),   # 尾 - 深绿
]

# 食物
FOOD_COLOR = (255, 60, 60)
FOOD_GLOW = (255, 120, 80)

# 文字
TEXT_WHITE = (220, 220, 230)
TEXT_DIM = (140, 140, 160)
WHITE = (255, 255, 255)
OVERLAY = (0, 0, 0, 160)

# ─── 食物粒子缓存 ───
food_particles = []


def add_eat_particles(x, y):
    for _ in range(20):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        food_particles.append({
            'x': x * GRID_SIZE + GRID_SIZE / 2,
            'y': y * GRID_SIZE + GRID_SIZE / 2,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': 30,
            'max_life': 30,
            'color': random.choice([FOOD_COLOR, FOOD_GLOW, (255, 200, 100)]),
        })


class SnakeGame:
    def __init__(self):
        self.reset_game()
        self.ai_mode = False
        self.tick = 0
        self.food_phase = 0.0

    def reset_game(self):
        mid_x, mid_y = GRID_W // 2, GRID_H // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = (1, 0)
        self.food = self.generate_food()
        self.score = 0
        self.speed = 10
        self.game_over = False
        self.food_eat_pulse = 0

    def generate_food(self):
        snake_set = set(self.snake)
        while True:
            pos = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
            if pos not in snake_set:
                return pos

    # ─── BFS ───
    def bfs(self, start, goal, obstacles):
        if start == goal:
            return [start]
        if start in obstacles or goal in obstacles:
            return None
        q = deque([[start]])
        seen = {start}
        while q:
            path = q.popleft()
            x, y = path[-1]
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                nb = (nx, ny)
                if nb == goal:
                    return path + [nb]
                if 0 <= nx < GRID_W and 0 <= ny < GRID_H and nb not in seen and nb not in obstacles:
                    seen.add(nb)
                    q.append(path + [nb])
        return None

    # ─── AI ───
    def ai_decision(self):
        head = self.snake[0]
        tail = self.snake[-1]
        food = self.food
        body_set = set(self.snake)

        path = self.bfs(head, food, body_set)
        if path and len(path) > 1:
            first_step = path[1]
            virt = list(path) + self.snake[1:]
            virt_head = virt[0]
            virt_tail = virt[-1]
            virt_body = set(virt[1:])
            if self.bfs(virt_head, virt_tail, virt_body) is not None:
                dx = first_step[0] - head[0]
                dy = first_step[1] - head[1]
                return (dx, dy)

        best_dir = None
        best_score = -999999

        for dx, dy in DIRS:
            nx, ny = head[0] + dx, head[1] + dy
            nxt = (nx, ny)
            if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
                continue
            if nxt in body_set:
                continue

            new_body = [nxt] + self.snake[:-1]
            new_tail = new_body[-1]
            new_body_set = set(new_body)
            tail_path = self.bfs(nxt, new_tail, new_body_set)
            if tail_path is None:
                continue

            tail_len = len(tail_path)
            toward_food = 0
            if (food[0] - head[0]) * dx > 0:
                toward_food += 3
            if (food[1] - head[1]) * dy > 0:
                toward_food += 3
            dist = abs(nx - food[0]) + abs(ny - food[1])
            bonus = max(0, 20 - dist) * 0.5
            score = toward_food + bonus - tail_len * 2
            if score > best_score:
                best_score = score
                best_dir = (dx, dy)

        if best_dir is not None:
            return best_dir

        safe = []
        for dx, dy in DIRS:
            nx, ny = head[0] + dx, head[1] + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and (nx, ny) not in body_set:
                safe.append((dx, dy))
        if safe:
            return min(safe, key=lambda d: abs(head[0] + d[0] - food[0]) + abs(head[1] + d[1] - food[1]))
        return self.direction

    # ─── 更新 ───
    def update(self):
        global food_particles
        self.tick += 1
        self.food_phase += 0.06

        # 更新粒子
        for p in food_particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.15
            p['life'] -= 1
            if p['life'] <= 0:
                food_particles.remove(p)

        if self.game_over:
            return

        if self.ai_mode:
            self.direction = self.ai_decision()

        hx, hy = self.snake[0]
        dx, dy = self.direction
        nh = (hx + dx, hy + dy)

        if (nh[0] < 0 or nh[0] >= GRID_W or nh[1] < 0 or nh[1] >= GRID_H or nh in self.snake):
            self.game_over = True
            return

        self.snake.insert(0, nh)

        if nh == self.food:
            self.score += 10
            add_eat_particles(self.food[0], self.food[1])
            self.food_eat_pulse = 8
            self.food = self.generate_food()
            if self.speed < 20:
                self.speed += 0.3
        else:
            self.snake.pop()

    # ─── 绘制 ───
    def draw(self):
        # ─ 背景 ─
        screen.fill(BG)

        # ─ 网格 ─
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE, (0, y), (WIDTH, y))

        # ─ 边框 ─
        pygame.draw.rect(screen, BORDER, (0, 0, WIDTH, HEIGHT), 2)

        # ─ 食物 glow ─
        fx = self.food[0] * GRID_SIZE + GRID_SIZE // 2
        fy = self.food[1] * GRID_SIZE + GRID_SIZE // 2
        pulse = abs(math.sin(self.food_phase * 2)) * 0.3 + 0.7
        glow_radius = 22 + int(math.sin(self.food_phase) * 4)
        for r in range(glow_radius, 0, -4):
            alpha = int((1 - r / glow_radius) * 120 * pulse)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            c = (*FOOD_GLOW, alpha)
            pygame.draw.circle(surf, c, (r, r), r)
            screen.blit(surf, (fx - r, fy - r))

        # ─ 食物 ─
        food_size = max(6, int(GRID_SIZE // 2 * (0.9 + math.sin(self.food_phase) * 0.1)))
        pygame.draw.circle(screen, FOOD_COLOR, (fx, fy), food_size)
        # 食物高光
        hl = max(2, food_size // 3)
        pygame.draw.circle(screen, (255, 200, 150), (fx - 3, fy - 3), hl)

        # ─ 粒子 ─
        for p in food_particles:
            alpha = int(255 * p['life'] / p['max_life'])
            size = max(1, int(p['life'] / p['max_life'] * 4))
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            c = (*p['color'], alpha)
            pygame.draw.circle(surf, c, (size, size), size)
            screen.blit(surf, (p['x'] - size, p['y'] - size))

        # ─ 蛇 ─
        n = len(self.snake)
        for i, seg in enumerate(self.snake):
            t = i / max(n - 1, 1)  # 0=头, 1=尾
            ci = min(int(t * (len(SNAKE_COLORS) - 1)), len(SNAKE_COLORS) - 2)
            frac = (t * (len(SNAKE_COLORS) - 1)) - ci
            c1 = SNAKE_COLORS[ci]
            c2 = SNAKE_COLORS[min(ci + 1, len(SNAKE_COLORS) - 1)]
            color = (
                int(c1[0] + (c2[0] - c1[0]) * frac),
                int(c1[1] + (c2[1] - c1[1]) * frac),
                int(c1[2] + (c2[2] - c1[2]) * frac),
            )

            rect = (seg[0] * GRID_SIZE + 1, seg[1] * GRID_SIZE + 1, GRID_SIZE - 2, GRID_SIZE - 2)
            # 圆角效果（画圆角矩形 ≈ 画个圆角效果）
            radius = 4 if n > 1 else GRID_SIZE // 2
            pygame.draw.rect(screen, color, rect, border_radius=radius)

            # ─ 蛇头 ─
            if i == 0:
                # 荧光
                glow_surf = pygame.Surface((GRID_SIZE + 6, GRID_SIZE + 6), pygame.SRCALPHA)
                for g in range(6, 0, -2):
                    alpha = int((1 - g / 6) * 60)
                    pygame.draw.rect(glow_surf, (*SNAKE_COLORS[0], alpha),
                                     (3 - g, 3 - g, GRID_SIZE + g * 2, GRID_SIZE + g * 2), border_radius=radius + g)
                screen.blit(glow_surf, (seg[0] * GRID_SIZE - 3, seg[1] * GRID_SIZE - 3))

                # 眼睛（朝方向看）
                dx, dy = self.direction
                ex1 = seg[0] * GRID_SIZE + GRID_SIZE // 2
                ey1 = seg[1] * GRID_SIZE + GRID_SIZE // 2
                off = 4
                if dx == 1:
                    ex1 += off
                elif dx == -1:
                    ex1 -= off
                if dy == 1:
                    ey1 += off
                elif dy == -1:
                    ey1 -= off

                # 两只眼睛位置
                if dx != 0:
                    offsets = [(0, -3), (0, 3)]
                else:
                    offsets = [(-3, 0), (3, 0)]

                for ox, oy in offsets:
                    ex = ex1 + ox
                    ey2 = ey1 + oy
                    # 眼白
                    pygame.draw.circle(screen, WHITE, (ex, ey2), 4)
                    # 瞳孔（朝方向偏移）
                    pygame.draw.circle(screen, (20, 20, 30), (ex + dx, ey2 + dy), 2)

            # ─ 蛇尾渐变收窄（可选：用三角形） ─
            if i == n - 1 and n > 2:
                # 尾部小圆点
                pygame.draw.circle(screen, color,
                                   (seg[0] * GRID_SIZE + GRID_SIZE // 2,
                                    seg[1] * GRID_SIZE + GRID_SIZE // 2),
                                   GRID_SIZE // 3)

        # ─ UI ─
        # 分数面板
        panel_rect = pygame.Rect(10, 10, 160, 44)
        panel_surf = pygame.Surface((160, 44), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 120))
        screen.blit(panel_surf, (10, 10))
        pygame.draw.rect(screen, BORDER, panel_rect, 1, border_radius=4)

        score_display = font.render(f"{self.score}", True, TEXT_WHITE)
        screen.blit(score_display, (20, 14))

        # 模式
        mode_color = (0, 220, 180) if self.ai_mode else TEXT_DIM
        mt = small_font.render(f"{'AI' if self.ai_mode else '手动'}  |  A 切换", True, mode_color)
        screen.blit(mt, (WIDTH - 140, 14))

        # 蛇长
        lt = small_font.render(f"长度: {len(self.snake)}", True, TEXT_DIM)
        screen.blit(lt, (WIDTH - 140, 36))

        # ─ Game Over ─
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            go = font.render("GAME OVER", True, FOOD_COLOR)
            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 50))
            sub = small_font.render(f"得分: {self.score}  |  按 R 重新开始", True, TEXT_WHITE)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                if not self.ai_mode:
                    k = event.key
                    cur = self.direction
                    if k == pygame.K_UP and cur != (0, 1):
                        self.direction = (0, -1)
                    elif k == pygame.K_DOWN and cur != (0, -1):
                        self.direction = (0, 1)
                    elif k == pygame.K_LEFT and cur != (1, 0):
                        self.direction = (-1, 0)
                    elif k == pygame.K_RIGHT and cur != (-1, 0):
                        self.direction = (1, 0)
                if event.key == pygame.K_a:
                    self.ai_mode = not self.ai_mode

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            clock.tick(self.speed)


if __name__ == "__main__":
    g = SnakeGame()
    print("A 切换 AI | R 重新开始")
    g.run()
