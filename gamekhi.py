import pygame
import math
import random
import sys

# Initialize pygame
pygame.init()

TILE_SIZE = 32
MAP_COLS = 19
MAP_ROWS = 19
CANVAS_WIDTH = 608
CANVAS_HEIGHT = 608
UI_HEIGHT = 70
SIDEBAR_WIDTH = 250
BASE_WIDTH = CANVAS_WIDTH + SIDEBAR_WIDTH
BASE_HEIGHT = CANVAS_HEIGHT + UI_HEIGHT
SCREEN_WIDTH = BASE_WIDTH
SCREEN_HEIGHT = BASE_HEIGHT

# --- USER: ĐIỀN TÊN FILE ẢNH VÀO ĐÂY ---
# Hãy thay các tên file dưới đây bằng tên file thật của ông (ví dụ: "tuong1.png")
IMG_WALL_1 = "tuong1.png"
IMG_WALL_2 = "tuong2.png"
IMG_ROAD_1 = "duong1.png"
IMG_ROAD_2 = "duong2.png"
IMG_ROAD_3 = "duong.png"
IMG_MENU_BG = "anhnen.png" # <-- Hãy đổi tên thành file ảnh nền của ông (858x678)
# ---------------------------------------

def load_tile_img(path, color_fallback):
    try:
        return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (TILE_SIZE, TILE_SIZE))
    except Exception as e:
        print(f"Lỗi load ảnh {path}: {e}. Đang dùng màu dự phòng.")
        img = pygame.Surface((TILE_SIZE, TILE_SIZE))
        img.fill(color_fallback)
        return img

# Tạo bản đồ biến thể để mỗi ô dùng 1 ảnh cố định trong suốt trận đấu
tileVariants = [[random.randint(0, 100) for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

window_width = BASE_WIDTH
window_height = BASE_HEIGHT
screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
render_surf = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

# --- LOAD ẢNH (Phải gọi SAU khi đã set_mode) ---
wall_imgs = [
    load_tile_img(IMG_WALL_1, (93, 64, 55)),
    load_tile_img(IMG_WALL_2, (62, 39, 35))
]
road_imgs = [
    load_tile_img(IMG_ROAD_1, (45, 90, 35)),
    load_tile_img(IMG_ROAD_2, (39, 78, 19)),
    load_tile_img(IMG_ROAD_3, (27, 58, 22))
]

# --- LOAD ẢNH NỀN MENU ---
try:
    menu_bg_img = pygame.transform.scale(pygame.image.load(IMG_MENU_BG).convert(), (BASE_WIDTH, BASE_HEIGHT))
except Exception as e:
    print(f"Lỗi load ảnh nền {IMG_MENU_BG}: {e}. Dùng màu mặc định.")
    menu_bg_img = None

pygame.display.set_caption("Monkey Mayhem - Trận Chiến Người Tuyết (V2) - Python Port")
clock = pygame.time.Clock()

# Track loading status for on-screen warning
missing_assets = []
for path in [IMG_WALL_1, IMG_WALL_2, IMG_ROAD_1, IMG_ROAD_2, IMG_ROAD_3]:
    try:
        pygame.image.load(path)
    except:
        missing_assets.append(path)

# Fonts
try:
    font_large = pygame.font.SysFont('Segoe UI', 60, bold=True)
    font_medium = pygame.font.SysFont('Segoe UI', 30, bold=True)
    font_small = pygame.font.SysFont('Segoe UI', 18, bold=True)
    font_tiny = pygame.font.SysFont('Segoe UI', 14, bold=True)
except:
    font_large = pygame.font.Font(None, 80)
    font_medium = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 24)
    font_tiny = pygame.font.Font(None, 18)

# Game State
game_mode = 'pvp' # 'pvp', 'pve', 'eve'
bot_difficulty = 'normal' # 'easy', 'normal', 'hard'
game_state = 'menu' # 'menu', 'playing', 'paused', 'gameover', 'victory'
winner_text = ""
player_rankings = [] # Store sorted players for victory screen

# CHỈNH SỬA BẢN ĐỒ TẠI ĐÂY (DẠNG MA TRẬN 19x19):
# 0 = Đường 1 (IMG_ROAD_1)
# 2 = Đường 2 (IMG_ROAD_2)
# 3 = Đường 3 (IMG_ROAD_3)
# 1 = Tường loại 1 (Nằm trên đường 1)
# 11 = Tường loại 2 (Hộp quà/Tường 2)
# BẢN ĐỒ CHIẾN THUẬT 4 NGƯỜI CHƠI (19x19)
# 0+1 = Cây | 2+11 = Hộp quà | 3 = Đường đi | 11 bao quanh = Tường cứng


# Key states
keys_held = {
    pygame.K_w: False, pygame.K_a: False, pygame.K_s: False, pygame.K_d: False, pygame.K_e: False,
    pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False, pygame.K_KP0: False, pygame.K_0: False
}
# BẢN ĐỒ CHIẾN THUẬT MẬT ĐỘ CAO - ĐỐI XỨNG 4 GÓC (19x19)
# 0+1: Cây | 2+11: Hộp quà | 3: Đường trơn | 11 bao quanh: Tường cứng

# BẢN ĐỒ CHIẾN THUẬT SIÊU ZIC-ZAC (19x19)
# 0+1 = Cây | 2+11 = Hộp quà | 3 = Đường trơn | 11 bao quanh = Tường cứng

mapLayout = [
    [11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11], # R0: Tường trên
    [11,  3,  3,  3,  2,  2,  3,  3,  2,  2,  2,  3,  3,  2,  2,  3,  3,  3, 11], # R1: Spawn P1 & P2
    [11,  3,  3,  3, 11, 11,  3,  3, 11, 11, 11,  3,  3, 11, 11,  3,  3,  3, 11], # R2: Chân vật cản
    [11,  3,  3,  0,  3,  3,  2,  0,  3,  2,  3,  0,  2,  3,  3,  0,  3,  3, 11], # R3: Ngọn
    [11,  3,  3,  1,  3,  3, 11,  1,  3, 11,  3,  1, 11,  3,  3,  1,  3,  3, 11], # R4: Chân
    [11,  3,  2,  3,  0,  2,  3,  3,  0,  2,  0,  3,  3,  2,  0,  3,  2,  3, 11], # R5: Ngọn
    [11,  3, 11,  3,  1, 11,  3,  3,  1, 11,  1,  3,  3, 11,  1,  3, 11,  3, 11], # R6: Chân
    [11,  0,  3,  2,  3,  3,  0,  2,  3,  0,  3,  2,  0,  3,  3,  2,  3,  0, 11], # R7: Ngọn - Chặn đường dọc
    [11,  1,  3, 11,  3,  3,  1, 11,  3,  1,  3, 11,  1,  3,  3, 11,  3,  1, 11], # R8: Chân
    [11,  3,  0,  3,  2,  0,  3,  3,  2,  3,  2,  3,  3,  0,  2,  3,  0,  3, 11], # R9: Trung tâm bản đồ
    [11,  3,  1,  3, 11,  1,  3,  3, 11,  3, 11,  3,  3,  1, 11,  3,  1,  3, 11], # R10: Chân
    [11,  0,  3,  2,  3,  3,  0,  2,  3,  0,  3,  2,  0,  3,  3,  2,  3,  0, 11], # R11: Ngọn - Chặn đường dọc
    [11,  1,  3, 11,  3,  3,  1, 11,  3,  1,  3, 11,  1,  3,  3, 11,  3,  1, 11], # R12: Chân
    [11,  3,  2,  3,  0,  2,  3,  3,  0,  2,  0,  3,  3,  2,  0,  3,  2,  3, 11], # R13: Ngọn
    [11,  3, 11,  3,  1, 11,  3,  3,  1, 11,  1,  3,  3, 11,  1,  3, 11,  3, 11], # R14: Chân
    [11,  3,  3,  3,  3,  3,  2,  0,  3,  2,  3,  0,  2,  3,  3,  3,  3,  3, 11], # R15: Ngọn
    [11,  3,  3,  3,  3,  3, 11,  1,  3, 11,  3,  1, 11,  3,  3,  3,  3,  3, 11], # R16: Chân
    [11,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3, 11], # R17: Spawn P3 & P4
    [11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11]  # R18: Tường dưới
]

# Đảm bảo 4 góc spawn (1,1), (1,17), (17,1), (17,17) và lân cận luôn trống
for r in [1, 2, 16, 17]:
    for c in [1, 2, 3, 15, 16, 17]:
        mapLayout[r][c] = 3
def draw_text_centered(surf, text, font, color, y, shadow_color=None):
    if shadow_color:
        txt_surf_shadow = font.render(text, True, shadow_color)
        txt_rect_shadow = txt_surf_shadow.get_rect(center=(SCREEN_WIDTH//2 + 3, y + 3))
        surf.blit(txt_surf_shadow, txt_rect_shadow)
        
        txt_surf_shadow2 = font.render(text, True, shadow_color)
        txt_rect_shadow2 = txt_surf_shadow2.get_rect(center=(SCREEN_WIDTH//2 - 1, y - 1))
        surf.blit(txt_surf_shadow2, txt_rect_shadow2)

    txt_surf = font.render(text, True, color)
    txt_rect = txt_surf.get_rect(center=(SCREEN_WIDTH//2, y))
    surf.blit(txt_surf, txt_rect)

class Player:
    def __init__(self, pid, startX, startY, color, controls):
        self.id = pid
        self.startX = startX
        self.startY = startY
        self.x = startX
        self.y = startY
        self.size = 26
        self.speed = 1.8 # Slightly slower for humans
        self.color = color
        self.controls = controls
        self.facing = 'down'
        self.ammo = 0
        self.score = 0
        self.canShoot = True
        self.lastShotTime = 0
        self.walkAnim = 0.0
        self.isMoving = False
        self.hasShield = False
        self.smiling = True
        
        # Bot variables
        self.isBot = False
        self.bot_diff = 'normal'
        self.bot_logic_timer = random.randint(0, 30)
        self.logic_interval_offset = random.randint(0, 4)
        self.target_timer = 0
        self.target_player_id = None
        self.target_item = None 
        self.personality = 'hunter'
        self.target_tile = None
        self.move_dx = 0
        self.move_dy = 0
        self.vx = 0 # Current velocity X
        self.vy = 0 # Current velocity Y
        self.stuckTimer = 0
        self.stuckKey = None
        self.oldX = startX
        self.oldY = startY
        self.current_path = [] # Optimized: cache path

    def respawn(self):
        self.x = self.startX
        self.y = self.startY
        self.ammo = 0
        self.facing = 'down' if self.id == 1 else 'left'
        self.isMoving = False
        self.hasShield = False
        self.stuckTimer = 0
        self.bot_logic_timer = random.randint(0, 30)
        self.target_timer = 0
        self.target_player_id = None
        self.target_item = None
        self.move_dx = 0
        self.move_dy = 0
        self.vx = 0
        self.vy = 0

    def get_key(self, ctrl_name):
        k = self.controls.get(ctrl_name)
        return keys_held.get(k, False) if k is not None else False

    def update(self):
        if self.isBot:
            self.update_bot_movement()
            return

        dx = 0
        dy = 0
        if self.get_key('up'):
            dy -= self.speed
            self.facing = 'up'
        elif self.get_key('down'):
            dy += self.speed
            self.facing = 'down'

        if self.get_key('left'):
            dx -= self.speed
            self.facing = 'left'
        elif self.get_key('right'):
            dx += self.speed
            self.facing = 'right'

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.isMoving = (dx != 0 or dy != 0)
        if self.isMoving:
            self.walkAnim += 0.2
        else:
            self.walkAnim = 0

        self.move(dx, dy)
        self.check_shoot_input()

    def update_bot_movement(self):
        # target velocity
        tx, ty = self.move_dx, self.move_dy
        mag = math.hypot(tx, ty)
        if mag > 0:
            tx, ty = (tx / mag) * self.speed, (ty / mag) * self.speed
        
        # Smooth transition to target velocity (Momentum)
        lerp_val = 0.15 # Higher = snappier, Lower = smoother
        self.vx += (tx - self.vx) * lerp_val
        self.vy += (ty - self.vy) * lerp_val
        
        # Final speed normalization to prevent overshoot
        v_mag = math.hypot(self.vx, self.vy)
        if v_mag > self.speed:
            self.vx, self.vy = (self.vx / v_mag) * self.speed, (self.vy / v_mag) * self.speed
            
        self.isMoving = (v_mag > 0.1)
        if self.isMoving:
            self.walkAnim += 0.2
            if math.fabs(self.vx) > math.fabs(self.vy):
                self.facing = 'right' if self.vx > 0 else 'left'
            else:
                self.facing = 'down' if self.vy > 0 else 'up'
        else:
            self.walkAnim = 0

        self.move(self.vx, self.vy)
        self.check_shoot_input()

    def check_shoot_input(self):
        current_time = pygame.time.get_ticks()
        shoot_key_pressed = self.get_key('shoot')
        if getattr(self, 'controls', {}).get('shoot2'): # support both numpad 0 and normal 0
            if keys_held.get(self.controls['shoot2'], False):
                shoot_key_pressed = True

        if shoot_key_pressed and self.canShoot and self.ammo > 0 and (current_time - self.lastShotTime > 500):
            self.shoot()
            self.lastShotTime = current_time
        elif not shoot_key_pressed:
            self.canShoot = True

    def performBotLogic(self):
        # Logic implementation placeholder
        pass

    def move(self, dx, dy):
        box = {'width': self.size, 'height': self.size}

        if dx != 0:
            if not self.checkCollision(self.x + dx, self.y, box):
                self.x += dx
            else:
                if not self.checkCollision(self.x + dx, self.y - 3, box): self.y -= 3
                elif not self.checkCollision(self.x + dx, self.y + 3, box): self.y += 3
        if dy != 0:
            if not self.checkCollision(self.x, self.y + dy, box):
                self.y += dy
            else:
                if not self.checkCollision(self.x - 3, self.y + dy, box): self.x -= 3
                elif not self.checkCollision(self.x + 3, self.y + dy, box): self.x += 3

        if self.x < 0: self.x = 0
        if self.y < 0: self.y = 0
        if self.x + self.size > CANVAS_WIDTH: self.x = CANVAS_WIDTH - self.size
        if self.y + self.size > CANVAS_HEIGHT: self.y = CANVAS_HEIGHT - self.size

    def checkCollision(self, nx, ny, box):
        padding = 2
        left = int((nx + padding) // TILE_SIZE)
        right = int((nx + box['width'] - padding) // TILE_SIZE)
        top = int((ny + padding) // TILE_SIZE)
        bottom = int((ny + box['height'] - padding) // TILE_SIZE)

        if left < 0 or right >= MAP_COLS or top < 0 or bottom >= MAP_ROWS: return True

        if mapLayout[top][left] not in [0, 2, 3] or mapLayout[top][right] not in [0, 2, 3] or \
           mapLayout[bottom][left] not in [0, 2, 3] or mapLayout[bottom][right] not in [0, 2, 3]:
            return True
        return False

    def shoot(self):
        self.canShoot = False
        self.ammo -= 1

        projX = self.x + self.size / 2
        projY = self.y + self.size / 2
        vx = 0
        vy = 0
        projSpeed = 8.0

        if self.facing == 'up': vy = -projSpeed
        if self.facing == 'down': vy = projSpeed
        if self.facing == 'left': vx = -projSpeed
        if self.facing == 'right': vx = projSpeed

        projX += vx * 2

        projectiles.append(Projectile(projX, projY, vx, vy, self.id))

    def draw(self, surf):
        s = self.size
        bounce = math.fabs(math.sin(self.walkAnim)) * 4 if self.isMoving else 0
        drawX = self.x + s/2
        drawY = self.y + s/2 - bounce

        pygame.draw.ellipse(surf, (0,0,0,76), (self.x - s*0.2, self.y + s - 6, s*1.4, s//2.5))

        main_c = self.color
        dark_c = (max(0, main_c[0]-40), max(0, main_c[1]-40), max(0, main_c[2]-40))
        light_c = (min(255, main_c[0]+60), min(255, main_c[1]+60), min(255, main_c[2]+60))
        peach = (255, 218, 185)
        pink_blush = (235, 150, 150)
        black = (20, 25, 30)

        swing = math.sin(self.walkAnim) * (s * 0.3) if self.isMoving else 0
        is_shooting = hasattr(self, 'lastShotTime') and (pygame.time.get_ticks() - self.lastShotTime < 150)

        head_r = int(s * 0.4)
        head_cx = int(drawX)
        head_cy = int(drawY - s*0.15)
        
        body_w = int(s * 0.6)
        body_h = int(s * 0.5)
        body_x = int(drawX - body_w/2)
        body_y = int(drawY + s*0.1)

        def draw_striped_ellipse(rect, base_col, stripe_col):
            # Optimized: Draw base then stripes with clipping
            pygame.draw.ellipse(surf, base_col, rect)
            # Simple stripes without new surface creation
            for i in range(1, 4):
                sy = rect[1] + i * (rect[3] // 4)
                pygame.draw.line(surf, stripe_col, (rect[0]+2, sy), (rect[0]+rect[2]-2, sy), 2)
            pygame.draw.ellipse(surf, black, rect, 1)

        def draw_limb(x1, y1, x2, y2, is_leg):
            pygame.draw.line(surf, black, (x1, y1), (x2, y2), 6)
            pygame.draw.line(surf, main_c, (x1, y1), (x2, y2), 4)
            if is_leg:
                pygame.draw.ellipse(surf, black, (x2-5, y2-2.5, 10, 5))
                pygame.draw.ellipse(surf, peach, (x2-4, y2-1.5, 8, 3))
            else:
                pygame.draw.circle(surf, black, (int(x2), int(y2)), 3)
                pygame.draw.circle(surf, peach, (int(x2), int(y2)), 2)

        if self.facing in ['right', 'left']:
            dir_m = 1 if self.facing == 'right' else -1
            tail_x = drawX - dir_m * s*0.2
            tail_y = body_y + body_h - s*0.1
            points = [
                (tail_x, tail_y),
                (tail_x - dir_m * s*0.3, tail_y + s*0.1),
                (tail_x - dir_m * s*0.5, tail_y + s*0.05),
                (tail_x - dir_m * s*0.5, tail_y - s*0.1),
                (tail_x - dir_m * s*0.35, tail_y - s*0.15)
            ]
            if len(points) > 1:
                pygame.draw.lines(surf, black, False, points, 4)
                pygame.draw.lines(surf, main_c, False, points, 2)
            
            draw_limb(drawX, body_y + body_h*0.5, drawX - dir_m * swing, drawY + s*0.78, True)
            draw_limb(drawX, body_y + s*0.25, drawX + dir_m * swing, drawY + s*0.65, False)

        elif self.facing == 'up':
            tail_x = drawX
            tail_y = body_y + body_h - 2
            t_swing = swing*0.5
            points = [
                (tail_x, tail_y),
                (tail_x + t_swing, tail_y + s*0.2),
                (tail_x + t_swing + 4, tail_y + s*0.35),
                (tail_x + t_swing - 4, tail_y + s*0.45)
            ]
            if len(points) > 1:
                pygame.draw.lines(surf, black, False, points, 4)
                pygame.draw.lines(surf, main_c, False, points, 2)

            draw_limb(drawX - s*0.15, body_y + body_h*0.5, drawX - s*0.15, drawY + s*0.78 + swing, True)
            draw_limb(drawX + s*0.15, body_y + body_h*0.5, drawX + s*0.15, drawY + s*0.78 - swing, True)
            if is_shooting:
                draw_limb(drawX - s*0.25, body_y + s*0.25, drawX - s*0.35, drawY - s*0.1, False)
                draw_limb(drawX + s*0.25, body_y + s*0.25, drawX + s*0.35, drawY - s*0.1, False)
            else:
                draw_limb(drawX - s*0.25, body_y + s*0.25, drawX - s*0.35, drawY + s*0.5 - swing, False)
                draw_limb(drawX + s*0.25, body_y + s*0.25, drawX + s*0.35, drawY + s*0.5 + swing, False)
            
        elif self.facing == 'down':
            draw_limb(drawX - s*0.15, body_y + body_h*0.5, drawX - s*0.15, drawY + s*0.78 - swing, True)
            draw_limb(drawX + s*0.15, body_y + body_h*0.5, drawX + s*0.15, drawY + s*0.78 + swing, True)

        draw_striped_ellipse((body_x, body_y, body_w, body_h), light_c, dark_c)

        ear_r = int(s * 0.28)
        ear_y = head_cy
        def draw_ear(cx, cy):
            pygame.draw.circle(surf, black, (cx, cy), ear_r + 1)
            pygame.draw.circle(surf, peach, (cx, cy), ear_r)
            pygame.draw.circle(surf, dark_c, (cx, cy), ear_r//2)

        if self.facing in ['down', 'up']:
            draw_ear(head_cx - head_r, ear_y)
            draw_ear(head_cx + head_r, ear_y)
        elif self.facing == 'right':
            draw_ear(head_cx - int(head_r*0.9), ear_y)
        elif self.facing == 'left':
            draw_ear(head_cx + int(head_r*0.9), ear_y)

        pygame.draw.circle(surf, black, (head_cx, head_cy), head_r + 1)
        pygame.draw.circle(surf, main_c, (head_cx, head_cy), head_r)
        
        tuft_y = head_cy - head_r
        pygame.draw.polygon(surf, black, [(head_cx-3, tuft_y+1), (head_cx+3, tuft_y+1), (head_cx, tuft_y-4)], 1)
        pygame.draw.polygon(surf, main_c, [(head_cx-2, tuft_y+1), (head_cx+2, tuft_y+1), (head_cx, tuft_y-3)])

        if self.facing != 'up':
            # Face Proportions
            face_w = int(head_r * 1.6)
            face_h = int(head_r * 1.3)
            face_x = head_cx - face_w // 2
            face_y = head_cy - int(head_r * 0.55)

            if self.facing == 'right': face_x += int(head_r * 0.35)
            if self.facing == 'left':  face_x -= int(head_r * 0.35)

            # Draw Muzzle Base (Upper and Lower)
            pygame.draw.ellipse(surf, peach, (face_x, face_y, face_w, face_h))
            pygame.draw.ellipse(surf, peach, (face_x - 2, face_y + face_h // 2, face_w + 4, face_h // 2))
            pygame.draw.ellipse(surf, black, (face_x, face_y, face_w, face_h), 1)

            eye_w, eye_h = 4, 8
            eye_y = face_y + int(face_h * 0.25)
            
            def draw_eye(ex, ey):
                # Black part
                pygame.draw.ellipse(surf, black, (ex, ey, eye_w, eye_h))
                # Sparkle 1 (Large)
                pygame.draw.circle(surf, (255, 255, 255), (int(ex + 1.5), int(ey + 2.5)), 1)
                # Sparkle 2 (Small)
                pygame.draw.circle(surf, (255, 255, 255), (int(ex + 2.5), int(ey + 5.5)), 0.5)

            def draw_blush(cx, cy):
                # Use pre-rendered blush surface
                surf.blit(blush_surf, (cx, cy))

            def draw_brow(bx, by):
                # Thin expressive brow
                pygame.draw.arc(surf, black, (bx, by, 8, 5), 0.4, 2.7, 1)

            if self.facing == 'down':
                # Eyes
                draw_eye(face_x + int(face_w * 0.22), eye_y)
                draw_eye(face_x + int(face_w * 0.72), eye_y)
                # Cheeks
                draw_blush(face_x + int(face_w * 0.1), eye_y + eye_h + 1)
                draw_blush(face_x + int(face_w * 0.75), eye_y + eye_h + 1)
                # Brows
                draw_brow(face_x + int(face_w * 0.18), eye_y - 6)
                draw_brow(face_x + int(face_w * 0.65), eye_y - 6)
                # Nose
                pygame.draw.ellipse(surf, (62, 39, 35), (head_cx - 2, eye_y + 4, 4, 3))
                # Smile is handled below
            elif self.facing == 'right':
                draw_eye(face_x + int(face_w * 0.7), eye_y)
                draw_blush(face_x + int(face_w * 0.75), eye_y + eye_h + 1)
                draw_brow(face_x + int(face_w * 0.65), eye_y - 6)
                pygame.draw.ellipse(surf, (62, 39, 35), (face_x + face_w * 0.88, eye_y + 4, 3, 2))
            elif self.facing == 'left':
                draw_eye(face_x + int(face_w * 0.22), eye_y)
                draw_blush(face_x + int(face_w * 0.05), eye_y + eye_h + 1)
                draw_brow(face_x + int(face_w * 0.15), eye_y - 6)
                pygame.draw.ellipse(surf, (62, 39, 35), (face_x + face_w * 0.05, eye_y + 4, 3, 2))

        if self.facing in ['right', 'left']:
            dir_m = 1 if self.facing == 'right' else -1
            draw_limb(drawX, body_y + body_h*0.5, drawX + dir_m * swing, drawY + s*0.7, True)
            if is_shooting:
                draw_limb(drawX, body_y + s*0.25, drawX + dir_m * s*0.4, drawY + s*0.1, False)
            else:
                draw_limb(drawX, body_y + s*0.25, drawX - dir_m * swing, drawY + s*0.55, False)
        elif self.facing == 'down':
            if is_shooting:
                draw_limb(drawX - s*0.25, body_y + s*0.25, drawX - s*0.35, drawY + s*0.2, False)
                draw_limb(drawX + s*0.25, body_y + s*0.25, drawX + s*0.35, drawY + s*0.2, False)
            else:
                draw_limb(drawX - s*0.25, body_y + s*0.25, drawX - s*0.35, drawY + s*0.55 + swing, False)
                draw_limb(drawX + s*0.25, body_y + s*0.25, drawX + s*0.35, drawY + s*0.55 - swing, False)

        # Shield
        if self.hasShield:
            # Draw shield directly on main surface efficiently
            pygame.draw.circle(surf, (52, 152, 219), (int(drawX), int(drawY)), int(s*0.8 + bounce), 2)
            # Subtle inner glow without heavy surface creation
            pygame.draw.circle(surf, (129, 236, 236), (int(drawX), int(drawY)), int(s*0.6 + bounce), 1)

# --- GLOBAL ASSETS FOR PERFORMANCE ---
# Pre-render small common surfaces to save FPS
blush_surf = pygame.Surface((8, 4), pygame.SRCALPHA)
pygame.draw.ellipse(blush_surf, (255, 100, 100, 120), (0, 0, 8, 4))

class Projectile:
    def __init__(self, x, y, vx, vy, ownerId):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ownerId = ownerId
        self.radius = 8
        self.active = True
        self.trail = []

    def update(self):
        self.trail.append({'x': self.x, 'y': self.y, 'alpha': 255})
        if len(self.trail) > 5:
            self.trail.pop(0)
        for t in self.trail:
            t['alpha'] -= 38
            if t['alpha'] < 0: t['alpha'] = 0

        self.x += self.vx
        self.y += self.vy

        rBoundary = self.radius
        hit = False
        for checkX in [self.x - rBoundary, self.x + rBoundary]:
            for checkY in [self.y - rBoundary, self.y + rBoundary]:
                c = int(checkX // TILE_SIZE)
                r = int(checkY // TILE_SIZE)
                if c < 0 or c >= MAP_COLS or r < 0 or r >= MAP_ROWS or mapLayout[r][c] not in [0, 2, 3]:
                    hit = True
                    break

        if hit:
            self.active = False
            spawnSplash(self.x - self.vx, self.y - self.vy, self.vx, self.vy)

    def draw(self, surf):
        for i, t in enumerate(self.trail):
            tsurf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(tsurf, (255, 255, 255, int(t['alpha'])), (self.radius, self.radius), int(self.radius * (i / len(self.trail))))
            surf.blit(tsurf, (int(t['x'] - self.radius), int(t['y'] - self.radius)))

        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (129, 236, 236), (int(self.x), int(self.y)), self.radius, 2)

class Item:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 18
        self.active = True
        self.offsetY = 0
        self.time = random.random() * 100
        self.type = 0 # 0: Ammo, 1: Shield

    def update(self):
        self.time += 0.1
        self.offsetY = math.sin(self.time) * 7 # Slightly more bobbing

    def draw(self, surf):
        if not self.active: return
        actY = self.y + self.offsetY
        s = self.size

        # Shadow
        pygame.draw.ellipse(surf, (0,0,0,76), (self.x, self.y + s - 4, s, s/2))

        if self.type == 0:
            # Blue Ice Crystal (Pha lê băng) - Sharp, Snow-themed design
            # Prism shape points
            pts = [
                (self.x + s/2, actY),             # Top
                (self.x + s*0.85, actY + s*0.45), # Right
                (self.x + s/2, actY + s),         # Bottom
                (self.x + s*0.15, actY + s*0.45)  # Left
            ]
            
            # Thick Deep Blue Outline (Visibility on both white and green)
            pygame.draw.polygon(surf, (0, 30, 100), pts, 3)
            # Glowing Cyan Body
            pygame.draw.polygon(surf, (0, 255, 255), pts)
            
            # Shimmer/Highlight (to make it look like ice)
            pygame.draw.line(surf, (255, 255, 255), pts[3], pts[1], 1)
            pygame.draw.line(surf, (255, 255, 255), pts[0], pts[2], 1)
            
            # Subtitle pulse glow
            inner_p = 2 + math.sin(self.time * 2) * 1.5
            pygame.draw.circle(surf, (255, 255, 255, 150), (int(self.x + s/2), int(actY + s/2)), int(inner_p))

        elif self.type == 1:
            # Golden Crest Shield (Khiên vàng) - Distinct shape and color
            # Heater Shield points
            pts = [
                (self.x + s*0.2, actY),            # Top-left
                (self.x + s*0.8, actY),            # Top-right
                (self.x + s*0.8, actY + s*0.5),    # Mid-right
                (self.x + s/2, actY + s),          # Bottom tip
                (self.x + s*0.2, actY + s*0.5)     # Mid-left
            ]
            
            # Thick Metallic Brown Outline
            pygame.draw.polygon(surf, (101, 67, 33), pts, 3)
            # Radiant Golden Body
            pygame.draw.polygon(surf, (255, 215, 0), pts)
            
            # Inner Lighter Gold Accent
            inner_pts = [
                (self.x + s*0.35, actY + 4),
                (self.x + s*0.65, actY + 4),
                (self.x + s*0.65, actY + s*0.45),
                (self.x + s/2, actY + s - 6),
                (self.x + s*0.35, actY + s*0.45)
            ]
            pygame.draw.polygon(surf, (255, 255, 100), inner_pts)
            
            # Shield light reflection
            pygame.draw.line(surf, (255, 255, 200), (self.x + s*0.42, actY + 6), (self.x + s*0.42, actY + s*0.4), 2)


class Bird:
    def __init__(self):
        dirX = 1 if random.random() > 0.5 else -1
        dirY = (random.random() - 0.5) * 2.0
        speed = random.random() * 1.2 + 1.2
        self.vx = dirX * speed
        self.vy = dirY * speed

        if random.random() < 0.5:
            self.x = -60 if dirX == 1 else CANVAS_WIDTH + 60
            self.y = random.random() * CANVAS_HEIGHT
        else:
            self.x = random.random() * CANVAS_WIDTH
            self.y = -60 if dirY > 0 else CANVAS_HEIGHT + 60

        self.wingAnim = random.random() * math.pi * 2
        self.active = True

    def update(self):
        if random.random() < 0.06:
            self.vx += (random.random() - 0.5) * 1.8
            self.vy += (random.random() - 0.5) * 1.8

            speed = math.hypot(self.vx, self.vy)
            if speed > 4.5:
                self.vx = (self.vx / speed) * 4.5
                self.vy = (self.vy / speed) * 4.5
            elif speed < 1.0:
                self.vx = (self.vx / speed) * 1.0
                self.vy = (self.vy / speed) * 1.0

        self.x += self.vx
        self.y += self.vy
        self.wingAnim += 0.15 + random.random() * 0.1

        if self.x < -150 or self.x > SCREEN_WIDTH + 150 or self.y < -150 or self.y > CANVAS_HEIGHT + 150:
            self.active = False

    def draw(self, surf):
        # We simplify bird drawing in Pygame
        myAngle = math.degrees(math.atan2(-self.vy, self.vx))
        
        bsurf = pygame.Surface((40, 40), pygame.SRCALPHA)
        center = (20, 20)
        
        # Body
        pygame.draw.ellipse(bsurf, (255,255,255), (center[0]-9, center[1]-3, 18, 7))
        pygame.draw.ellipse(bsurf, (189,195,199), (center[0]-9, center[1]-3, 18, 7), 1)
        
        # Wings
        flap = math.cos(self.wingAnim)
        wing_y = int(8 * flap)
        pygame.draw.polygon(bsurf, (255,255,255), [(center[0]+5, center[1]-1), (center[0]-4, center[1]-10-wing_y), (center[0]-1, center[1]-2)])
        pygame.draw.polygon(bsurf, (255,255,255), [(center[0]+5, center[1]+1), (center[0]-4, center[1]+10+wing_y), (center[0]-1, center[1]+2)])
        
        rotated_bird = pygame.transform.rotate(bsurf, myAngle)
        new_rect = rotated_bird.get_rect(center=(int(self.x), int(self.y)))
        
        # Shadow roughly
        shadow_rect = rotated_bird.get_rect(center=(int(self.x), int(self.y) + 25))
        shadow_surf = pygame.Surface(rotated_bird.get_size(), pygame.SRCALPHA)
        shadow_mask = pygame.mask.from_surface(rotated_bird)
        for pt in shadow_mask.outline():
            shadow_surf.set_at(pt, (0,0,0,100))
            
        surf.blit(shadow_surf, shadow_rect)
        surf.blit(rotated_bird, new_rect)


# Players list will be populated in resetGame
players = []

projectiles = []
items = []
birds = []
splashes = []

class Confetti:
    def __init__(self):
        self.reset()
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-500, 0)
        self.s = random.randint(6, 12)
        self.c = random.choice([(231, 76, 60), (46, 204, 113), (52, 152, 219), (241, 196, 15), (155, 89, 182), (26, 188, 156)])
        self.vx = (random.random() - 0.5) * 5
        self.vy = random.random() * 3 + 2
        self.a = random.random() * 360
        self.av = random.random() * 10 - 5
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.a += self.av
        if self.y > SCREEN_HEIGHT: self.reset()
    def draw(self, surf):
        # Optimized confetti draw
        cs = pygame.Surface((self.s, self.s), pygame.SRCALPHA)
        cs.fill(self.c)
        rs = pygame.transform.rotate(cs, self.a)
        surf.blit(rs, (self.x, self.y))

confetti_particles = [Confetti() for _ in range(80)]
victory_time = 0

def spawnSplash(x, y, impactVx=0, impactVy=0):
    for i in range(15):
        if impactVx != 0 or impactVy != 0:
            angle = math.atan2(-impactVy, -impactVx) + (random.random() - 0.5) * math.pi * 1.4
            speed = random.random() * 4 + 1.5
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
        else:
            vx = (random.random() - 0.5) * 6
            vy = (random.random() - 0.5) * 6

        splashes.append({
            'x': x, 'y': y, 'vx': vx, 'vy': vy, 'radius': random.random() * 3.5 + 1.5, 'life': 1.0
        })

def rectIntersect(x1, y1, w1, h1, x2, y2, w2, h2):
    return x2 < x1 + w1 and x2 + w2 > x1 and y2 < y1 + h1 and y2 + h2 > y1

def checkHits():
    global game_state, winner_text
    for p in projectiles:
        if not p.active: continue
        
        shooter = next((pl for pl in players if pl.id == p.ownerId), None)
        if not shooter: continue

        for target in players:
            if target.id == p.ownerId: continue # Don't hit yourself
            
            if p.x > target.x and p.x < target.x + target.size and \
               p.y > target.y and p.y < target.y + target.size:
                
                p.active = False
                spawnSplash(p.x, p.y, p.vx, p.vy)

                if target.hasShield:
                    target.hasShield = False
                else:
                    shooter.score += 1
                    if shooter.score >= 10:
                        endGame(shooter)
                    else:
                        target.respawn()
                break # Projectile destroyed

    for i in items:
        if not i.active: continue
        for p in players:
            if rectIntersect(p.x, p.y, p.size, p.size, i.x, i.y, i.size, i.size):
                i.active = False
                if i.type == 0:
                    p.ammo += 1
                    if p.ammo > 2: p.ammo = 2
                else:
                    p.hasShield = True
                spawnItem()
                break

def spawnItem():
    global items
    items = [i for i in items if i.active]
    if len(items) >= 12: return
    
    emptyTiles = []
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if mapLayout[r][c] in [0, 2, 3]:
                emptyTiles.append((c, r))
    if not emptyTiles: return

    spot = random.choice(emptyTiles)
    cx = spot[0] * TILE_SIZE + TILE_SIZE / 2 - 14 + (random.random() * 8 - 4)
    cy = spot[1] * TILE_SIZE + TILE_SIZE / 2 - 14 + (random.random() * 8 - 4)

    overlap = False
    for i in items:
        if rectIntersect(i.x, i.y, i.size, i.size, cx, cy, 28, 28):
            overlap = True
            break
            
    if not overlap:
        shieldCount = sum(1 for i in items if i.type == 1)
        itype = 0
        if shieldCount < 4 and random.random() < 0.3: itype = 1
        newItem = Item(cx, cy)
        newItem.type = itype
        items.append(newItem)

def endGame(winner_player):
    global game_state, winner_text, player_rankings
    game_state = 'victory'
    player_rankings = sorted(players, key=lambda p: p.score, reverse=True)
    name = f"PLAYER {winner_player.id}"
    if getattr(winner_player, 'isBot', False):
        name = f"BOT {winner_player.id}"
    winner_text = f"{name} THẮNG!"

def resetGame():
    global projectiles, items, splashes, birds, game_state, players, victory_time
    victory_time = 0
    projectiles.clear()
    items.clear()
    splashes.clear()
    birds.clear()
    players.clear()
    
    # Define spawn points
    spawns = [(1,1), (17,17), (17,1), (1,17)]
    colors = [(52, 152, 219), (231, 76, 60), (46, 204, 113), (241, 196, 15)]
    p1_ctrl = {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d, 'shoot': pygame.K_e}
    p2_ctrl = {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'shoot': pygame.K_KP0, 'shoot2': pygame.K_0}
    
    bot_configs = []
    if game_mode == '1p':
        players.append(Player(1, spawns[0][0]*TILE_SIZE+7, spawns[0][1]*TILE_SIZE+7, colors[0], p1_ctrl))
        players[-1].isBot = False
        if bot_difficulty == 'easy': bot_configs = ['easy', 'easy', 'normal']
        elif bot_difficulty == 'normal': bot_configs = ['normal', 'normal', 'normal']
        elif bot_difficulty == 'hard': bot_configs = ['hard', 'normal', 'normal']
    elif game_mode == '2p':
        players.append(Player(1, spawns[0][0]*TILE_SIZE+7, spawns[0][1]*TILE_SIZE+7, colors[0], p1_ctrl))
        players[-1].isBot = False
        players.append(Player(2, spawns[1][0]*TILE_SIZE+7, spawns[1][1]*TILE_SIZE+7, colors[1], p2_ctrl))
        players[-1].isBot = False
        if bot_difficulty == 'easy': bot_configs = ['easy', 'easy']
        elif bot_difficulty == 'normal': bot_configs = ['normal', 'normal']
        elif bot_difficulty == 'hard': bot_configs = ['hard', 'normal']
    elif game_mode == '1v1':
        players.append(Player(1, spawns[0][0]*TILE_SIZE+7, spawns[0][1]*TILE_SIZE+7, colors[0], p1_ctrl))
        players[-1].isBot = False
        players.append(Player(2, spawns[1][0]*TILE_SIZE+7, spawns[1][1]*TILE_SIZE+7, colors[1], p2_ctrl))
        players[-1].isBot = False
        bot_configs = [] # Không có bot trong chế độ đối kháng 1vs1

    personalities = ['hunter', 'collector', 'sniper', 'scout', 'ninja']
    random.shuffle(personalities)
    
    for i, diff in enumerate(bot_configs):
        idx = len(players)
        # Each bot gets unique negative virtual keys to stay independent
        base_k = -10 * (idx + 1)
        bot_ctrl = {
            'up': base_k - 1, 'down': base_k - 2, 
            'left': base_k - 3, 'right': base_k - 4, 
            'shoot': base_k - 5
        }
        
        p = Player(idx+1, spawns[idx][0]*TILE_SIZE+7, spawns[idx][1]*TILE_SIZE+7, colors[idx], bot_ctrl)
        p.isBot = True
        p.bot_diff = diff
        p.personality = personalities[i % len(personalities)]
        players.append(p)
    
    game_state = 'playing'
    for _ in range(8): spawnItem()

last_item_spawn = 0

def drawMap(surf):
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE

            tile = mapLayout[r][c]
            
            if tile == 1:
                # Tường 1 (1) nằm trên đường 1 (index 0)
                surf.blit(road_imgs[0], (x, y))
                surf.blit(wall_imgs[0], (x, y))
            elif tile == 11:
                # Tường 2 (11)
                surf.blit(wall_imgs[1], (x, y))
            elif tile == 2:
                # Đường 2
                surf.blit(road_imgs[1], (x, y))
            elif tile == 3:
                # Đường 3
                surf.blit(road_imgs[2], (x, y))
            else:
                # Mặc định là Đường 1
                surf.blit(road_imgs[0], (x, y))

def updateParticles(surf):
    global splashes
    for p in splashes:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 0.035

        c = int(p['x'] // TILE_SIZE)
        r = int(p['y'] // TILE_SIZE)
        if 0 <= c < MAP_COLS and 0 <= r < MAP_ROWS:
            if mapLayout[r][c] == 1:
                p['life'] = 0

        if p['life'] > 0:
            surf_p = pygame.Surface((p['radius']*2, p['radius']*2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (255, 255, 255, int(255 * p['life'])), (p['radius'], p['radius']), p['radius'])
            surf.blit(surf_p, (p['x'] - p['radius'], p['y'] - p['radius']))
    splashes = [p for p in splashes if p['life'] > 0]

def findBotPath(bot, tC, tR):
    startC = int((bot.x + bot.size / 2) // TILE_SIZE)
    startR = int((bot.y + bot.size / 2) // TILE_SIZE)

    tC = max(0, min(MAP_COLS - 1, tC))
    tR = max(0, min(MAP_ROWS - 1, tR))

    # 1. If target is blocked, find nearest reachable tile
    if mapLayout[tR][tC] in [1, 11]:
        q = [(tC, tR)]
        v = set([(tC, tR)])
        found = False
        while q:
            curr = q.pop(0)
            if mapLayout[curr[1]][curr[0]] not in [1, 11]:
                tC, tR = curr
                found = True
                break
            for dc, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nc, nr = curr[0] + dc, curr[1] + dr
                if 0 <= nc < MAP_COLS and 0 <= nr < MAP_ROWS and (nc, nr) not in v:
                    v.add((nc, nr))
                    q.append((nc, nr))
        if not found: return None

    # 2. Optimized BFS using Parent Map
    queue = [(startC, startR)]
    visited = set([(startC, startR)])
    parent = {}

    target_found = False
    while queue:
        curr = queue.pop(0)
        currC, currR = curr
        if currC == tC and currR == tR: 
            target_found = True
            break

        for dc, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nc, nr = currC + dc, currR + dr
            if 0 <= nc < MAP_COLS and 0 <= nr < MAP_ROWS:
                if (nc, nr) not in visited and mapLayout[nr][nc] not in [1, 11]:
                    visited.add((nc, nr))
                    parent[(nc, nr)] = (currC, currR)
                    queue.append((nc, nr))
    
    if target_found:
        # Reconstruct path from back to front
        path = []
        curr = (tC, tR)
        while curr != (startC, startR):
            path.append({'c': curr[0], 'r': curr[1]})
            curr = parent.get(curr)
            if curr is None: break
        path.reverse()
        return path
    return None

def performBotLogic(bot):
    bot.bot_logic_timer += 1
    bot.target_timer -= 1

    diff = getattr(bot, 'bot_diff', 'normal')
    pers = getattr(bot, 'personality', 'hunter')
    
    # Base params per personality
    logicInterval = 5
    shootChance = 0.2
    
    if pers == 'hunter': bot.speed = 2.6; logicInterval = 2; shootChance = 0.4
    elif pers == 'sniper': bot.speed = 1.8; logicInterval = 6; shootChance = 0.6
    elif pers == 'collector': bot.speed = 2.2; logicInterval = 4; shootChance = 0.1
    elif pers == 'scout': bot.speed = 2.0; logicInterval = 3; shootChance = 0.2
    elif pers == 'ninja': bot.speed = 1.6; logicInterval = 8; shootChance = 0.5
    else: bot.speed = 2.0

    # Difficulty modifiers
    if diff == 'easy': 
        bot.speed *= 0.7; shootChance *= 0.3; logicInterval *= 3
    elif diff == 'hard': 
        bot.speed *= 1.2; shootChance *= 2.0; logicInterval = max(1, logicInterval // 2)

    # Process High-Level Logic (Periodic Decisions)
    if bot.bot_logic_timer % (logicInterval + bot.logic_interval_offset) == 0:
        # 1. Target Selection (Players)
        if bot.target_timer <= 0 or bot.target_player_id is None:
            valid_targets = [p for p in players if p.id != bot.id]
            if valid_targets:
                bot.target_player_id = random.choice(valid_targets).id
                bot.target_timer = random.randint(150, 450)
            else:
                bot.target_player_id = None

        # 2. Item Selection (Coordinated)
        if bot.target_item and not bot.target_item.active: bot.target_item = None
        if not bot.target_item:
            active_items = [i for i in items if i.active]
            other_bot_targets = [p.target_item for p in players if p.isBot and p.id != bot.id and p.target_item]
            available_items = [i for i in active_items if i not in other_bot_targets]
            
            if not available_items and active_items: available_items = active_items # Fallback
            
            if available_items:
                # Decide if want item based on ammo and personality
                chance = 0.3
                if pers == 'collector': chance = 0.95
                elif bot.ammo == 0: chance = 0.98
                if random.random() < chance:
                    bot.target_item = random.choice(available_items)

    targetPlayer = next((p for p in players if p.id == bot.target_player_id), None)
    bx = bot.x + bot.size / 2; by = bot.y + bot.size / 2
    
    # 3. Stuck detection
    if hasattr(bot, 'oldX') and hasattr(bot, 'oldY') and bot.bot_logic_timer % 15 == 0:
        movedDist = math.hypot(bot.x - bot.oldX, bot.y - bot.oldY)
        if movedDist < 0.2 and bot.isMoving:
            bot.stuckTimer = 15
            choices = ['up', 'down', 'left', 'right']
            sd = random.choice(choices)
            bot.move_dx = 10 if sd == 'right' else -10 if sd == 'left' else 0
            bot.move_dy = 10 if sd == 'down' else -10 if sd == 'up' else 0
            bot.target_tile = None; bot.target_item = None
            return
        bot.oldX = bot.x; bot.oldY = bot.y

    if bot.stuckTimer > 0:
        bot.stuckTimer -= 1
        return

    # 4. Steering Vector Calculation
    targetX, targetY = bx, by
    if targetPlayer:
        px = targetPlayer.x + targetPlayer.size / 2; py = targetPlayer.y + targetPlayer.size / 2
        dist = math.hypot(px - bx, py - by)
        
        tC, tR = int(px // TILE_SIZE), int(py // TILE_SIZE) # Default target is the player
        
        # Override target if fleeing (Ammo == 0 and enemy close)
        if bot.ammo == 0 and dist < TILE_SIZE * 5:
            # Move away from player
            tC, tR = int((bx - (px - bx)) // TILE_SIZE), int((by - (py - by)) // TILE_SIZE)
        # Override target if seeking item
        elif bot.target_item:
            tC, tR = int((bot.target_item.x + bot.target_item.size/2) // TILE_SIZE), int((bot.target_item.y + bot.target_item.size/2) // TILE_SIZE)
        # Override if specialized personality behavior
        elif pers == 'sniper' and dist < TILE_SIZE * 6:
            tC, tR = int((bx - (px - bx)) // TILE_SIZE), int((by - (py - by)) // TILE_SIZE)
        elif pers == 'scout' or (pers == 'ninja' and dist > TILE_SIZE * 6):
            if not getattr(bot, 'target_tile', None) or random.random() < 0.05:
                bot.target_tile = (random.randint(2, MAP_COLS-3), random.randint(2, MAP_ROWS-3))
            tC, tR = bot.target_tile

        # 4. Optimized Pathfinding (Throttled)
        # Only recalculate path every 10 frames or if current path is empty
        if bot.bot_logic_timer % 10 == 0 or not getattr(bot, 'current_path', []):
            bot.current_path = findBotPath(bot, tC, tR) or []

        if bot.current_path:
            # Seek the next tile on path
            targetX, targetY = bot.current_path[0]['c'] * TILE_SIZE + TILE_SIZE/2, bot.current_path[0]['r'] * TILE_SIZE + TILE_SIZE/2
            # If we reached the first tile of the path, pop it
            if math.hypot(bx - targetX, by - targetY) < 10:
                bot.current_path.pop(0)
        else:
            targetX, targetY = px, py

        # Set Steering Vector
        bot.move_dx = targetX - bx
        bot.move_dy = targetY - by
    
    # 5. Soft Repulsion from other bots (Boids-like)
    for p in players:
        if p.id != bot.id and p.isBot:
            dist = math.hypot(bx - (p.x + p.size/2), by - (p.y + p.size/2))
            if 0 < dist < TILE_SIZE * 1.2:
                # Steer away softly
                weight = 1.5 if pers != 'hunter' else 0.5
                bot.move_dx += (bx - (p.x + p.size/2)) * weight
                bot.move_dy += (by - (p.y + p.size/2)) * weight

    # 6. Shooting Input Logic
    keys_held[bot.controls['shoot']] = False
    if targetPlayer and bot.ammo > 0 and random.random() < shootChance:
        px = targetPlayer.x + targetPlayer.size / 2; py = targetPlayer.y + targetPlayer.size / 2
        cB, rB = int(bx // TILE_SIZE), int(by // TILE_SIZE)
        cP, rP = int(px // TILE_SIZE), int(py // TILE_SIZE)
        
        if cB == cP or rB == rP:
            hasLOS = True
            if cB == cP:
                for r in range(min(rB, rP) + 1, max(rB, rP)):
                    if mapLayout[r][cB] in [1, 11]: hasLOS = False; break
            else:
                for c in range(min(cB, cP) + 1, max(cB, cP)):
                    if mapLayout[rB][c] in [1, 11]: hasLOS = False; break
            
            if hasLOS:
                tolerance = TILE_SIZE * (0.4 if pers == 'sniper' else 0.8)
                ax = px - bx; ay = py - by
                canShoot = False
                if bot.facing == 'up' and ay < 0 and math.fabs(ax) < tolerance: canShoot = True
                elif bot.facing == 'down' and ay > 0 and math.fabs(ax) < tolerance: canShoot = True
                elif bot.facing == 'left' and ax < 0 and math.fabs(ay) < tolerance: canShoot = True
                elif bot.facing == 'right' and ax > 0 and math.fabs(ay) < tolerance: canShoot = True
                if canShoot: keys_held[bot.controls['shoot']] = True



# Buttons
class Button:
    def __init__(self, x, y, w, h, text, color1, color2, action, mode, diff):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color1 = color1
        self.color2 = color2
        self.action = action
        self.mode = mode
        self.diff = diff
        self.hover = False

    def draw(self, surf):
        main_col = self.color1 if not self.hover else self.color2
        
        # tạo surface phụ hỗ trợ độ trong suốt (Alpha)
        alpha = 180 if not self.hover else 230
        btn_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (main_col[0], main_col[1], main_col[2], alpha), (0, 0, self.rect.width, self.rect.height), border_radius=15)
        surf.blit(btn_surf, self.rect)
        
        # Vẽ viền trắng
        pygame.draw.rect(surf, (255, 255, 255, 150), self.rect, 2, border_radius=15)
        
        txt = font_small.render(self.text, True, (255,255,255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txt_rect)

buttons = [
    Button(SCREEN_WIDTH//2 - 210, 210, 200, 50, "1 NGƯỜI (Bot Dễ)", (46, 204, 113), (39, 174, 96), 'start', '1p', 'easy'),
    Button(SCREEN_WIDTH//2 - 210, 270, 200, 50, "1 NGƯỜI (Bot Vừa)", (243, 156, 18), (211, 84, 0), 'start', '1p', 'normal'),
    Button(SCREEN_WIDTH//2 - 210, 330, 200, 50, "1 NGƯỜI (Bot Khó)", (231, 76, 60), (192, 57, 43), 'start', '1p', 'hard'),
    
    Button(SCREEN_WIDTH//2 + 10, 210, 200, 50, "2 NGƯỜI (Bot Dễ)", (46, 204, 113), (39, 174, 96), 'start', '2p', 'easy'),
    Button(SCREEN_WIDTH//2 + 10, 270, 200, 50, "2 NGƯỜI (Bot Vừa)", (243, 156, 18), (211, 84, 0), 'start', '2p', 'normal'),
    Button(SCREEN_WIDTH//2 + 10, 330, 200, 50, "2 NGƯỜI (Bot Khó)", (231, 76, 60), (192, 57, 43), 'start', '2p', 'hard'),

    Button(SCREEN_WIDTH//2 - 100, 390, 200, 50, "ĐỐI KHÁNG 1VS1", (155, 89, 182), (142, 68, 173), 'start', '1v1', ''),
    Button(SCREEN_WIDTH//2 - 100, 450, 200, 50, "HƯỚNG DẪN", (52, 152, 219), (41, 128, 185), 'how_to', '', ''),
]

# Snow effect
snowflakes = [{'x': random.randint(0, SCREEN_WIDTH), 'y': random.randint(0, SCREEN_HEIGHT), 's': random.randint(2,5)} for _ in range(100)]

def draw_sidebar(surf):
    sidebar_rect = pygame.Rect(0, UI_HEIGHT, SIDEBAR_WIDTH, CANVAS_HEIGHT)
    pygame.draw.rect(surf, (24, 34, 45), sidebar_rect)
    pygame.draw.line(surf, (255,255,255), (SIDEBAR_WIDTH, UI_HEIGHT), (SIDEBAR_WIDTH, SCREEN_HEIGHT), 2)
    
    # Một khung duy nhất cho toàn bộ bảng điểm
    margin = 15
    board_rect = pygame.Rect(margin, UI_HEIGHT + margin, SIDEBAR_WIDTH - 2*margin, CANVAS_HEIGHT - 2*margin)
    pygame.draw.rect(surf, (44, 62, 80), board_rect, border_radius=15)
    pygame.draw.rect(surf, (149, 165, 166), board_rect, 2, border_radius=15)
    
    # Tiêu đề bảng điểm
    title_txt = font_medium.render("THỐNG KÊ", True, (236, 240, 241))
    title_x = board_rect.x + (board_rect.width - title_txt.get_width()) // 2
    surf.blit(title_txt, (title_x, board_rect.y + 15))
    
    # Vẽ từng người chơi trong khung này
    if not players: return
    
    row_h = (board_rect.height - 60) // len(players)
    start_y = board_rect.y + 60
    
    for i, p in enumerate(players):
        y = start_y + i * row_h
        p_name = f"PLAYER {p.id}"
        if getattr(p, 'isBot', False):
            p_name = f"BOT {p.id}"
            
        # Tên người chơi và mini skin
        txt_name = font_small.render(p_name, True, p.color)
        surf.blit(txt_name, (board_rect.x + 20, y + 10))
        
        # Mini character drawing (fixed position in row)
        old_x, old_y, old_m, old_f = p.x, p.y, p.isMoving, p.facing
        p.x, p.y, p.isMoving, p.facing = board_rect.right - 40, y + 45, False, 'down'
        p.draw(surf)
        p.x, p.y, p.isMoving, p.facing = old_x, old_y, old_m, old_f
        
        # Thông số (Điểm, Đạn, Khiên)
        txt_score = font_tiny.render(f"Điểm: {p.score}/10", True, (255, 255, 255))
        surf.blit(txt_score, (board_rect.x + 30, y + 40))
        
        txt_ammo = font_tiny.render(f"Tuyết: {p.ammo}/2", True, (241, 196, 15))
        surf.blit(txt_ammo, (board_rect.x + 30, y + 65))
        
        shield_txt = "Khiên: CÓ" if p.hasShield else "Khiên: KHÔNG"
        txt_shield = font_tiny.render(shield_txt, True, (52, 152, 219) if p.hasShield else (149, 165, 166))
        surf.blit(txt_shield, (board_rect.x + 30, y + 90))
        
        # Đường kẻ chia giữa các người chơi
        if i < len(players) - 1:
            line_y = y + row_h - 5
            pygame.draw.line(surf, (24, 34, 45), (board_rect.x + 10, line_y), (board_rect.right - 10, line_y), 1)

def draw_victory_screen(surf):
    # Dynamic Gradient Background (shifting slightly)
    # Background: Festive Blue/Purple
    c1 = (4, 41, 64)
    c2 = (28, 12, 45)
    for i in range(SCREEN_HEIGHT):
        col = (
            int(c1[0] + (c2[0] - c1[0]) * (i / SCREEN_HEIGHT)),
            int(c1[1] + (c2[1] - c1[1]) * (i / SCREEN_HEIGHT)),
            int(c1[2] + (c2[2] - c1[2]) * (i / SCREEN_HEIGHT))
        )
        pygame.draw.line(surf, col, (0, i), (SCREEN_WIDTH, i))
    
    # Update and Draw Confetti
    for c in confetti_particles:
        c.update()
        c.draw(surf)

    # Title Banner with pulse
    pulse = math.sin(victory_time * 0.1) * 3
    draw_text_centered(surf, "CHIẾN THẮNG RỰC RỠ!", font_large, (255, 215, 0), 100 + pulse, shadow_color=(0, 0, 0))
    draw_text_centered(surf, "CHÚC MỪNG NHÀ VÔ ĐỊCH", font_medium, (255, 255, 255), 180 + pulse)
    
    # Title
    # Rankings: [0=Gold, 1=Silver, 2=Bronze, 3=Grey]
    podiums = [
        {'idx': 1, 'color': (189, 195, 199), 'h': 200, 'x': -180, 'label': '2'}, # Silver
        {'idx': 0, 'color': (241, 196, 15), 'h': 280, 'x': 0, 'label': '1'},    # Gold
        {'idx': 2, 'color': (211, 84, 0), 'h': 140, 'x': 180, 'label': '3'},    # Bronze
        {'idx': 3, 'color': (46, 204, 113), 'h': 80, 'x': 340, 'label': '4'}    # 4th
    ]

    base_y = 560
    center_x = BASE_WIDTH // 2
    
    for pod in podiums:
        rank_idx = pod['idx']
        if rank_idx >= len(player_rankings): continue
        
        p = player_rankings[rank_idx]
        px = center_x + pod['x']
        pw = 140
        ph = pod['h']
        
        # Draw Block
        rect = pygame.Rect(px - pw//2, base_y - ph, pw, ph)
        pygame.draw.rect(surf, pod['color'], rect, border_radius=15)
        pygame.draw.rect(surf, (255, 255, 255), rect, 3, border_radius=15)
        
        # Draw Rank Number
        txt_rank = font_large.render(pod['label'], True, (255, 255, 255))
        surf.blit(txt_rank, txt_rank.get_rect(center=(px, base_y - ph//2)))
        
        # Draw Monkey with Jump Animation
        old_x, old_y, old_m, old_f = p.x, p.y, p.isMoving, p.facing
        
        # Winner jumps high, others sway
        jump_y = 0
        if rank_idx == 0:
            jump_y = -abs(math.sin(victory_time * 0.15)) * 45
        else:
            jump_y = math.sin(victory_time * 0.1 + rank_idx) * 8
            
        p.x, p.y, p.isMoving, p.facing = px, base_y - ph - 25 + jump_y, False, 'down'
        p.draw(surf)
        p.x, p.y, p.isMoving, p.facing = old_x, old_y, old_m, old_f
        
        # Draw Trophy for Gold
        if rank_idx == 0:
            ty = base_y - ph - 100
            pygame.draw.rect(surf, (243, 156, 18), (px-15, ty, 30, 30)) # Body
            pygame.draw.circle(surf, (243, 156, 18), (px-15, ty+10), 10, 3) # Handle L
            pygame.draw.circle(surf, (243, 156, 18), (px+15, ty+10), 10, 3) # Handle R
            pygame.draw.circle(surf, (241, 196, 15), (px, ty), 15) # Cup

    # Buttons
    btn_again = Button(center_x - 210, 600, 200, 50, "CHƠI LẠI", (46, 204, 113), (39, 174, 96), 'again', '', '')
    btn_menu = Button(center_x + 10, 600, 200, 50, "VỀ MENU", (231, 76, 60), (192, 57, 43), 'menu_back', '', '')
    return btn_again, btn_menu

def draw_how_to_play(surf):
    # Nền tối mờ ảo (Glassmorphism effect roughly)
    surf.fill((4, 41, 64)) 
    
    # Tuyết rơi nhẹ trong menu hướng dẫn
    for s in snowflakes:
        s['y'] += s['s'] * 0.5
        if s['y'] > BASE_HEIGHT: s['y'] = 0
        pygame.draw.circle(surf, (255, 255, 255, 100), (s['x'], int(s['y'])), s['s'])

    draw_text_centered(surf, "HƯỚNG DẪN CHƠI", font_large, (255, 255, 255), 80, shadow_color=(0, 0, 0))
    
    y = 180
    line_h = 40
    
    # Player 1 Controls
    draw_text_centered(surf, "PLAYER 1: Dùng WASD để di chuyển, phím E để bắn", font_small, (52, 152, 219), y)
    y += line_h
    
    # Player 2 Controls
    draw_text_centered(surf, "PLAYER 2: Dùng PHÍM MŨI TÊN để di chuyển, phím 0 để bắn", font_small, (231, 76, 60), y)
    y += line_h + 30
    
    # Goal
    draw_text_centered(surf, "MỤC TIÊU: Bắn trúng đối thủ để ghi điểm. Ai đạt 10 điểm trước sẽ THẮNG!", font_small, (236, 240, 241), y)
    y += line_h + 30
    
    # Items
    draw_text_centered(surf, "VẬT PHẨM TRONG GAME:", font_medium, (241, 196, 15), y)
    y += line_h + 10
    draw_text_centered(surf, "- Hộp quà Cam: Nhận thêm đạn Tuyết (Tối đa dự trữ 2 viên)", font_small, (255, 255, 255), y)
    y += line_h
    draw_text_centered(surf, "- Khiên Xanh: Bảo vệ bạn khỏi 1 lần bị trúng đạn", font_small, (255, 255, 255), y)
    
    # Return a back button to be handled in main loop
    back_btn = Button(BASE_WIDTH // 2 - 100, BASE_HEIGHT - 100, 200, 50, "QUAY LẠI", (231, 76, 60), (192, 57, 43), 'menu_back', '', '')
    return back_btn

def draw_ui(surf):
    pygame.draw.rect(surf, (44, 62, 80), (0, 0, BASE_WIDTH, UI_HEIGHT))
    draw_text_centered(surf, "SONG KHỈ ĐẠI CHIẾN", font_large, (236, 240, 241), 35, shadow_color=(0,0,0))

def main():
    global game_state, game_mode, bot_difficulty, last_item_spawn, birds, projectiles, splashes, victory_time
    global window_width, window_height, screen, render_surf
    
    running = True
    while running:
        dt = clock.tick(60)

        scale_val = min(window_width / BASE_WIDTH, window_height / BASE_HEIGHT)
        offset_x = (window_width - int(BASE_WIDTH * scale_val)) // 2
        offset_y = (window_height - int(BASE_HEIGHT * scale_val)) // 2
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.VIDEORESIZE:
                window_width, window_height = event.w, event.h
                screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if game_state in ['playing', 'paused']:
                    if event.key in [pygame.K_p, pygame.K_ESCAPE]:
                        game_state = 'paused' if game_state == 'playing' else 'playing'
                        
                if game_state == 'paused' and event.key == pygame.K_q:
                    game_state = 'menu'
                
                if (game_state == 'gameover' or game_state == 'victory') and event.key == pygame.K_c:
                    resetGame()
                    
                if event.key in keys_held:
                    # Input logic for blocking modes
                    ignore = False
                    if game_mode == '1p' and event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_KP0, pygame.K_0]:
                        ignore = True
                    if not ignore:
                        keys_held[event.key] = True

            if event.type == pygame.KEYUP:
                if event.key in keys_held:
                    keys_held[event.key] = False
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                real_pos = pygame.mouse.get_pos()
                pos = ((real_pos[0] - offset_x) / scale_val, (real_pos[1] - offset_y) / scale_val)
                
                # Check Main Menu Buttons
                if game_state == 'menu':
                    for b in buttons:
                        if b.rect.collidepoint(pos):
                            if b.action == 'start':
                                game_mode = b.mode
                                bot_difficulty = b.diff
                                resetGame()
                            elif b.action == 'how_to':
                                game_state = 'how_to'
                                
                # Check Back Button in Instructions
                elif game_state == 'how_to':
                    back_btn = Button(BASE_WIDTH//2 - 100, BASE_HEIGHT - 100, 200, 50, "QUAY LẠI", (231, 76, 60), (192, 57, 43), 'menu_back', '', '')
                    if back_btn.rect.collidepoint(pos):
                        game_state = 'menu'
                
                # Check Victory Screen Buttons
                elif game_state == 'victory':
                    btn1, btn2 = draw_victory_screen(render_surf)
                    if btn1.rect.collidepoint(pos):
                        resetGame()
                    elif btn2.rect.collidepoint(pos):
                        game_state = 'menu'

        if game_state == 'menu':
            if menu_bg_img:
                render_surf.blit(menu_bg_img, (0, 0))
            else:
                render_surf.fill((4, 97, 159))
            
            # Snow
            for s in snowflakes:
                s['y'] += s['s']
                if s['y'] > BASE_HEIGHT:
                    s['y'] = 0
                    s['x'] = random.randint(0, BASE_WIDTH)
                pygame.draw.circle(render_surf, (255,255,255,150), (s['x'], int(s['y'])), s['s'])

            # Title removed as requested
            
            real_pos = pygame.mouse.get_pos()
            pos = ((real_pos[0] - offset_x) / scale_val, (real_pos[1] - offset_y) / scale_val)
            for b in buttons:
                b.hover = b.rect.collidepoint(pos)
                b.draw(render_surf)
            
            if missing_assets:
                warning = f"Thiếu: {', '.join(missing_assets)}"
                txt = font_tiny.render(warning, True, (231, 76, 60))
                render_surf.blit(txt, (20, BASE_HEIGHT - 30))
                
        elif game_state == 'how_to':
            back_btn = draw_how_to_play(render_surf)
            real_pos = pygame.mouse.get_pos()
            pos = ((real_pos[0] - offset_x) / scale_val, (real_pos[1] - offset_y) / scale_val)
            back_btn.hover = back_btn.rect.collidepoint(pos)
            back_btn.draw(render_surf)
            
        elif game_state == 'playing':
            for p in players:
                if getattr(p, 'isBot', False): performBotLogic(p)
                p.update()
            
            for i in items: i.update()
            for p in projectiles: p.update()
            
            if len(birds) < 5 and random.random() < 0.02: birds.append(Bird())
            for b in birds: b.update()
            birds = [b for b in birds if b.active]
            
            checkHits()
            projectiles = [p for p in projectiles if p.active]
            
            current_time = pygame.time.get_ticks()
            if current_time - last_item_spawn > 2500:
                spawnItem()
                last_item_spawn = current_time

            render_surf.fill((0,0,0))
            draw_ui(render_surf)
            
            game_surf = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
            drawMap(game_surf)
            
            for i in items: i.draw(game_surf)
            
            for p in sorted(players, key=lambda pl: pl.y):
                p.draw(game_surf)
                
            for p in projectiles: p.draw(game_surf)
            
            updateParticles(game_surf)
            render_surf.blit(game_surf, (SIDEBAR_WIDTH, UI_HEIGHT))
            draw_sidebar(render_surf)
            for b in birds: b.draw(render_surf)

        elif game_state == 'paused':
            overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            render_surf.blit(overlay, (0,0))
            draw_text_centered(render_surf, "TẠM DỪNG", font_large, (255,255,255), BASE_HEIGHT//2 - 50)
            draw_text_centered(render_surf, "Nhấn P để tiếp tục", font_medium, (255,255,255), BASE_HEIGHT//2 + 10)
            draw_text_centered(render_surf, "Nhấn Q để thoát (Về Menu)", font_medium, (231, 76, 60), BASE_HEIGHT//2 + 50)

        elif game_state == 'victory':
            global victory_time
            victory_time += 1
            btn_again, btn_menu = draw_victory_screen(render_surf)
            real_pos = pygame.mouse.get_pos()
            pos = ((real_pos[0] - offset_x) / scale_val, (real_pos[1] - offset_y) / scale_val)
            
            btn_again.hover = btn_again.rect.collidepoint(pos)
            btn_menu.hover = btn_menu.rect.collidepoint(pos)
            
            btn_again.draw(render_surf)
            btn_menu.draw(render_surf)

        scaled_surf = pygame.transform.smoothscale(render_surf, (int(BASE_WIDTH * scale_val), int(BASE_HEIGHT * scale_val)))
        screen.fill((0, 0, 0))
        screen.blit(scaled_surf, (offset_x, offset_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
