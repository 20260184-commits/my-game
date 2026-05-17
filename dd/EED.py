import pygame
import sys
import os
import random
import math

# --- [1. Global Constants & Spec Data] ---
FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCALE_FACTOR = 4 
TOP_CROP = 20 

GRAVITY = 0.8
WALK_SPEED = 8
BACK_WALK_SPEED = 3
JUMP_FORCE = -20
GROUND_Y = 550

DASH_SPEED = 16
DASH_DURATION = 12
DASH_COOLDOWN = 30
DOUBLE_TAP_TIME = 250
BUFFER_WINDOW = 30

# [Spec] 가상 벽 거리 (화면 너비의 80%)
VIRTUAL_WALL_DIST = SCREEN_WIDTH * 0.8
# [Spec] 콤보 윈도우 (0.5초)
COMBO_WINDOW_MS = 500

HIT_STOP_LIGHT = 4
HIT_STOP_HEAVY = 12
PLAYER_MAX_HP = 100
ENEMY_MAX_HP = 50
DASH_CANCEL_STUN_BONUS = 60

KNOCKBACK_HIT = 12
KNOCKBACK_GUARD = 10

# [Spec] 콤보 스케일링 (데미지 및 경직 보정)
COMBO_SCALING = {
    1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6,
}
MIN_SCALING = 0.4

HITBOX_CONFIG = {
    "LIGHT": {"offset": 0, "w": 80, "h": 30, "y_off": 0, "start": 3, "end": 6},
    "HEAVY": {"offset": 35, "w": 50, "h": 120, "y_off": 0, "start": 6, "end": 12}
}

CHAR_DATA = {
     "A1": {
        "IDLE": ("Idle", 4, None), "RUN": ("Run", 8, None),
        "ATK1": ("Attack1", 4, 3), "ATK2": ("Attack2", 4, 3),
        "JUMP": ("Jump", 2, None), "FALL": ("Fall", 2, None),
        "HIT": ("Take Hit", 3, None), "DEATH": ("Death", 7, None),
    },
    "B1": {
        "IDLE": ("Idle", 9, None), "RUN": ("Run", 9, None),
        "ATK1": ("Attack1", 16, 12), "HIT": ("Take Hit", 3, None), "DEATH": ("Death", 8, None),
    },
}

class PixelGuard:
    def __init__(self):
        self.pixel_scale = SCALE_FACTOR
        self.width, self.height = 32, 64
        self.particles = []

    def draw(self, surface, cx, cy, facing, y_offset=100):
        small_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            dy = y - (self.height // 2)
            base_x = 22 - (dy * dy * 0.015) 
            noise = random.randint(-1, 1)
            if random.random() < 0.1: noise = random.randint(-3, 3)
            x = int(base_x + noise)
            if 0 <= x < self.width:
                pygame.draw.rect(small_surf, (0, 100, 255, 150), (x - 8, y, 10, 1))
                pygame.draw.rect(small_surf, (150, 255, 255, 255), (x - 3, y, 4, 1))
                if random.random() < 0.5: small_surf.set_at((x, y), (255, 255, 255, 255))
        if random.random() < 0.4: self.particles.append([random.randint(10, 25), self.height, random.uniform(1, 3)])
        for p in self.particles[:]:
            p[1] -= p[2]
            if p[1] < 0: self.particles.remove(p)
            else: small_surf.set_at((int(p[0]), int(p[1])), (0, 200, 255, 255))
        scaled_surf = pygame.transform.scale(small_surf, (self.width * self.pixel_scale, self.height * self.pixel_scale))
        if facing == -1:
            scaled_surf = pygame.transform.flip(scaled_surf, True, False)
            offset_x = -70 - (scaled_surf.get_width() // 2)
        else:
            offset_x = 70 - (scaled_surf.get_width() // 2)
        surface.blit(scaled_surf, (cx + offset_x, cy - (scaled_surf.get_height() // 2) + y_offset))

class ComboDisplay:
    def __init__(self):
        self.font = pygame.font.SysFont("impact", 60, bold=True)
        self.timer, self.active, self.combo_count = 0, False, 0

    def trigger(self, count):
        self.combo_count, self.timer, self.active = count, 20, True

    def update(self):
        if self.timer > 0: self.timer -= 1
        else: self.active = False

    def draw(self, surface, player_rect, cam_x):
        if not self.active or self.combo_count <= 1: return
        scale = 1.0 + (math.sin((self.timer / 20) * 3.14) * 0.5)
        text_surf = self.font.render(f"{self.combo_count} HIT!", True, (255, 200, 0))
        shadow_surf = self.font.render(f"{self.combo_count} HIT!", True, (0, 0, 0))
        w, h = text_surf.get_size()
        text_surf = pygame.transform.scale(text_surf, (int(w * scale), int(h * scale)))
        shadow_surf = pygame.transform.scale(shadow_surf, (int(w * scale), int(h * scale)))
        pos_x, pos_y = player_rect.centerx + 60 - cam_x, player_rect.bottom - 300 - (text_surf.get_height() // 2)
        surface.blit(shadow_surf, (pos_x + 4, pos_y + 4))
        surface.blit(text_surf, (pos_x, pos_y))

def load_sprite_sheet(filename, frame_count):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
        sw, sh = sheet.get_size()
        fw = sw // frame_count
        frames = []
        for i in range(frame_count):
            frame = sheet.subsurface(pygame.Rect(i * fw, 0, fw, sh))
            if TOP_CROP > 0: frame = frame.subsurface(pygame.Rect(0, TOP_CROP, fw, sh - TOP_CROP))
            frames.append(pygame.transform.scale(frame, (frame.get_width() * SCALE_FACTOR, frame.get_height() * SCALE_FACTOR)))
        return frames
    except:
        dummy = pygame.Surface((100 * SCALE_FACTOR, 100 * SCALE_FACTOR))
        dummy.fill((255, 0, 0))
        return [dummy] * frame_count

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, char_id, hp):
        super().__init__()
        self.char_id, self.state, self.timer, self.frame_index = char_id, "IDLE", 0, 0
        self.facing_right, self.vel_x, self.vel_y, self.is_grounded = True, 0, 0, True
        self.hit_gauge, self.dash_charges, self.dash_timer, self.dash_cooldown_timer = 0, 1, 0, 0
        self.input_buffer, self.buffer_timer, self.guard_effect_timer = None, 0, 0
        self.guard_effect, self.recovery_timer, self.ghosts, self.is_cancel_dash = PixelGuard(), 0, [], False
        self.god_mode, self.is_guarding, self.hp, self.max_hp = False, False, hp, hp
        # [Spec] 콤보 윈도우 추적용 타임스탬프
        self.last_hit_time = 0 
        
        self.animations = {}
        data = CHAR_DATA.get(char_id, CHAR_DATA["A1"])
        for state, (suffix, count, hit_idx) in data.items(): 
            self.animations[state] = load_sprite_sheet(os.path.join("dd\\assets", f"{self.char_id}_{suffix}.png"), count)

        self.image = self.animations["IDLE"][0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.is_attacking, self.has_hit, self.combo_step = False, False, 0
        if char_id == "A1": self.hurtbox_w, self.hurtbox_h = 60, 100
        elif char_id == "B1": self.hurtbox_w, self.hurtbox_h = 70, 40
        else: self.hurtbox_w, self.hurtbox_h = 60, 80
        self.hurtbox = pygame.Rect(0, 0, 0, 0)

    def take_damage(self, amount, attacker, attack_type):
        if self.state == "DEATH": return False
        
        # [Spec] 방향성 가드 구현 (적을 등지고 입력 시)
        is_guarding = self.is_guarding 
        if self.char_id == "A1":
            keys = pygame.key.get_pressed()
            is_guarding = (self.facing_right and keys[pygame.K_a]) or (not self.facing_right and keys[pygame.K_d])

        # [Spec] 콤보 스케일링 적용 (데미지/경직 감쇄)
        combo_count = attacker.combo_step if hasattr(attacker, 'combo_step') else 1
        scaling = COMBO_SCALING.get(combo_count, MIN_SCALING)
        
        if attack_type == "LIGHT": base_stun, base_recovery = (7, 12) if is_guarding else (12, 10)
        else: base_stun, base_recovery = (10, 20) if is_guarding else (20, 15)

        final_damage = amount * scaling * (0.5 if is_guarding else 1.0)
        final_stun = base_stun * scaling
        base_knockback = KNOCKBACK_GUARD if is_guarding else KNOCKBACK_HIT

        if not self.god_mode: self.hp -= final_damage
        self.hit_stun_timer = final_stun 
        self.state = "HIT"
        attacker.recovery_frames = base_recovery 
    
        if self.hp <= 0:
            self.hp = 0
            if self.state != "DEATH": self.state, self.timer = "DEATH", 0
        else:
            self.vel_x = -base_knockback if self.facing_right else base_knockback
        
        if is_guarding: self.guard_effect_timer = 10
        return True

    def apply_physics(self, target):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y; self.vel_y = 0; self.is_grounded = True
        else: self.is_grounded = False

        friction = 1.0 if self.state == "DASH" else (0.98 if self.state == "HIT" else 0.92)
        self.vel_x *= friction
        if abs(self.vel_x) < 0.1: self.vel_x = 0
        self.rect.x += self.vel_x

        # [Spec] 다이나믹 가상 벽 구현
        dist = self.rect.centerx - target.rect.centerx
        if dist > VIRTUAL_WALL_DIST:
            self.rect.centerx = target.rect.centerx + VIRTUAL_WALL_DIST
            self.vel_x = 0
        elif dist < -VIRTUAL_WALL_DIST:
            self.rect.centerx = target.rect.centerx - VIRTUAL_WALL_DIST
            self.vel_x = 0

    def update(self):
        if self.buffer_timer > 0:
            self.buffer_timer -= 1
            if self.input_buffer in ["LIGHT", "HEAVY"]:
                can_cancel = (self.state == "RECOVERY" and self.combo_step > 0) or \
                             (self.is_attacking and self.has_hit and self.timer > 10) # 간략화된 캔슬 체크
                if can_cancel: self.execute_buffer()
        else: self.input_buffer = None
            
        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= 1
        if hasattr(self, 'guard_effect_timer') and self.guard_effect_timer > 0: self.guard_effect_timer -= 1
        if hasattr(self, 'hit_stun_timer') and self.hit_stun_timer > 0:
            self.hit_stun_timer -= 1
            if self.hit_stun_timer <= 0 and self.state == "HIT": self.state = "IDLE"

        if self.state == "DASH":
            self.dash_timer -= 1
            frames = self.animations["RUN"]
            self.frame_index = (pygame.time.get_ticks() // 50) % len(frames)
            self.image = frames[self.frame_index]
            if self.dash_timer <= 0: self.state = "IDLE"; self.vel_x = 0; self.execute_buffer()

        elif self.is_attacking:
            atk_type = "LIGHT" if self.state == "ATK1" else "HEAVY"
            total_f = 14 if atk_type == "LIGHT" else 22
            cfg = HITBOX_CONFIG[atk_type]
            self.timer += 1
            frames = self.animations[self.state]
            self.frame_index = min(int((self.timer / total_f) * len(frames)), len(frames) - 1)
            self.image = frames[self.frame_index]

            state_info = CHAR_DATA[self.char_id].get(self.state)
            if state_info and state_info[2] is not None:
                dur = total_f / state_info[1]
                if state_info[2] * dur <= self.timer <= (state_info[2] + 1) * dur:
                    off, w, h = cfg["offset"] * SCALE_FACTOR, cfg["w"] * SCALE_FACTOR, cfg["h"] * SCALE_FACTOR
                    hy = self.rect.bottom - (cfg["y_off"] * SCALE_FACTOR) - h
                    hx = self.rect.centerx + off if self.facing_right else self.rect.centerx - off - w
                    self.hitbox = pygame.Rect(hx, hy, w, h)
                else: self.hitbox = pygame.Rect(0, 0, 0, 0)
            else: self.hitbox = pygame.Rect(0, 0, 0, 0)

            if self.timer >= total_f:
                if not self.has_hit:
                    self.combo_step = 0
                    self.recovery_timer = 10 if atk_type == "LIGHT" else 15
                else:
                    # [Spec] 소프트 리커버리 (콤보 비례 후딜 증가)
                    base_rec = 10 if atk_type == "LIGHT" else 15
                    penalty = self.combo_step * (1 if atk_type == "LIGHT" else 2)
                    self.recovery_timer = base_rec + penalty
                    if hasattr(self, 'recovery_frames'): self.recovery_timer = self.recovery_frames; del self.recovery_frames

                self.state = "RECOVERY" if self.recovery_timer > 0 else "IDLE"
                self.timer, self.is_attacking = 0, False
                self.execute_buffer()

        elif self.state == "HIT":
            self.image = self.animations.get("HIT", self.animations["IDLE"])[0]
            self.hitbox = pygame.Rect(0, 0, 0, 0)
        elif self.state == "RECOVERY":
            self.recovery_timer -= 1
            self.image = self.animations["IDLE"][0]
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            if self.recovery_timer <= 0: self.state = "IDLE"
        elif self.state == "DEATH":
            frames = self.animations.get("DEATH", self.animations["IDLE"])
            self.timer += 1; self.frame_index = min(self.timer // 10, len(frames) - 1)
            self.image = frames[self.frame_index]; self.hitbox = pygame.Rect(0, 0, 0, 0); self.vel_x = 0
        else: 
            if not self.is_grounded: self.state = "JUMP" if self.vel_y < 0 else "FALL"
            elif abs(self.vel_x) > 0.1: self.state = "RUN"
            else: self.state = "IDLE"
            frames = self.animations.get(self.state, self.animations["IDLE"])
            self.frame_index = (pygame.time.get_ticks() // (100 if self.state=="RUN" else 200)) % len(frames)
            self.image = frames[self.frame_index]; self.hitbox = pygame.Rect(0, 0, 0, 0)

        if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
        self.hurtbox = pygame.Rect(self.rect.centerx - self.hurtbox_w // 2, self.rect.bottom - self.hurtbox_h, self.hurtbox_w, self.hurtbox_h)
        if self.state in ["DASH", "HIT"] or self.is_attacking:
            if pygame.time.get_ticks() % 6 == 0: self.ghosts.append([self.image.copy(), self.rect.copy(), 100])
        for g in self.ghosts[:]:
            g[2] -= 25
            if g[2] <= 0: self.ghosts.remove(g)

    def draw_ghosts(self, surface, cam_x):
        for img, rect, alpha in self.ghosts:
            ghost_img = img.copy(); ghost_img.set_alpha(alpha)
            ghost_img.fill((150, 200, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(ghost_img, (rect.x - cam_x, rect.y))

    def trigger_dash(self, is_forward):
        if self.dash_cooldown_timer <= 0:
            if self.is_attacking:
                if self.dash_charges > 0: self.dash_charges -= 1; self.is_cancel_dash = True
                else: return False
            else: self.is_cancel_dash = False
            self.hitbox = pygame.Rect(0, 0, 0, 0); self.state, self.is_attacking, self.hit_gauge, self.timer = "DASH", False, 0, 0
            self.dash_timer, self.dash_cooldown_timer = DASH_DURATION, DASH_COOLDOWN
            self.vel_x = (DASH_SPEED if self.facing_right else -DASH_SPEED) if is_forward else (-DASH_SPEED if self.facing_right else DASH_SPEED)
            return True
        return False

    def handle_attack(self, attack_type):
        if self.state == "DASH" and self.is_cancel_dash: self.vel_x = 0
        self.state = "ATK1" if attack_type == "LIGHT" else ("ATK2" if "ATK2" in self.animations else "ATK1")
        self.timer, self.is_attacking, self.has_hit, self.recovery_timer = 0, True, False, 0
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def add_to_buffer(self, action): self.input_buffer, self.buffer_timer = action, BUFFER_WINDOW
    def execute_buffer(self):
        if self.input_buffer:
            action = self.input_buffer; self.input_buffer, self.buffer_timer = None, 0
            if action == "LIGHT" and self.is_grounded: self.handle_attack("LIGHT")
            elif action == "HEAVY" and self.is_grounded: self.handle_attack("HEAVY")
            elif action == "JUMP" and self.is_grounded: self.vel_y = JUMP_FORCE

class Enemy(Entity):
    def __init__(self, x, y, char_id, hp):
        super().__init__(x, y, char_id, hp)
        self.ai_timer, self.ai_state = 0, "APPROACH"
    def update_ai(self, target):
        if self.state in ["DEATH", "HIT"]: self.is_guarding = False; return
        dist = target.rect.centerx - self.rect.centerx
        if abs(dist) > 20: self.facing_right = dist > 0
        if target.is_attacking and not self.is_guarding and self.state in ["IDLE", "RUN"] and random.random() < 0.7:
            self.is_guarding, self.vel_x, self.state = True, 0, "IDLE"
        else: self.is_guarding = False
        if self.is_attacking: self.vel_x = 0; return 
        planned_atk = "LIGHT" if self.char_id == "B1" else ("LIGHT" if random.random() < 0.7 else "HEAVY")
        cfg = HITBOX_CONFIG[planned_atk]
        attack_reach = (cfg["offset"] + cfg["w"]) * SCALE_FACTOR + (target.hurtbox_w // 2) - 20
        if self.ai_state == "APPROACH":
            if abs(dist) > attack_reach: self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED; self.state = "RUN"
            else: self.ai_state, self.ai_timer, self.planned_atk = "ATTACK", 0, planned_atk
        elif self.ai_state == "ATTACK":
            self.vel_x = 0; self.handle_attack(getattr(self, "planned_atk", "LIGHT"))
            self.ai_state, self.ai_timer = "WAIT", random.randint(30, 60) 
        elif self.ai_state == "WAIT":
            self.vel_x, self.state = 0, "IDLE"; self.ai_timer -= 1
            if self.ai_timer <= 0: self.ai_state = "APPROACH"
    def update(self): super().update()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand: Director's Cut")
    clock = pygame.time.Clock()
    font_small, font_large = pygame.font.SysFont("arial", 20, bold=True), pygame.font.SysFont("arial", 40, bold=True)
    player, enemy = Entity(200, GROUND_Y, "A1", PLAYER_MAX_HP), Enemy(1000, GROUND_Y, "B1", ENEMY_MAX_HP)
    combo_display = ComboDisplay()
    all_sprites = pygame.sprite.Group(player, enemy)
    hitstop_timer, screen_shake_timer, screen_shake_intensity = 0, 0, 0
    last_key_pressed, last_key_time = None, 0

    running = True
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1: player.god_mode = not player.god_mode
                if event.key == pygame.K_F2: enemy.god_mode = not enemy.god_mode
                curr_t = pygame.time.get_ticks()
                if event.key in [pygame.K_a, pygame.K_d]:
                    if event.key == last_key_pressed and (curr_t - last_key_time) < DOUBLE_TAP_TIME:
                        is_fwd = (event.key == pygame.K_d and player.facing_right) or (event.key == pygame.K_a and not player.facing_right)
                        player.trigger_dash(is_fwd)
                    last_key_pressed, last_key_time = event.key, curr_t
                if event.key == pygame.K_w and player.is_grounded: player.vel_y = JUMP_FORCE
                if event.key == pygame.K_i:
                    if player.is_grounded and (player.state in ["IDLE", "RUN"] or player.is_cancel_dash): player.handle_attack("LIGHT")
                    else: player.add_to_buffer("LIGHT")
                if event.key == pygame.K_o:
                    if player.is_grounded and (player.state in ["IDLE", "RUN"] or player.is_cancel_dash): player.handle_attack("HEAVY")
                    else: player.add_to_buffer("HEAVY")

        if hitstop_timer > 0: hitstop_timer -= 1
        else:
            if player.state != "DASH":
                if not player.is_attacking and player.state not in ["HIT", "RECOVERY"]: 
                    if keys[pygame.K_a]: player.vel_x = -BACK_WALK_SPEED if player.facing_right else -WALK_SPEED
                    elif keys[pygame.K_d]: player.vel_x = WALK_SPEED if player.facing_right else BACK_WALK_SPEED
                    else: player.vel_x = 0
                elif player.state == "RECOVERY": player.vel_x = 0
            if player.state in ["IDLE", "RUN"]: player.facing_right = (enemy.rect.centerx > player.rect.centerx)
            if enemy.state in ["IDLE", "RUN"]: enemy.facing_right = (player.rect.centerx > enemy.rect.centerx)
            enemy.update_ai(player)
            if player.state == "DASH" and player.is_cancel_dash:
                if enemy.state == "HIT": enemy.hit_stun_timer += DASH_CANCEL_STUN_BONUS
                player.is_cancel_dash = False 
            combo_display.update()
            player.apply_physics(enemy); enemy.apply_physics(player)
            all_sprites.update()

            if player.hitbox.colliderect(enemy.hurtbox) and not player.has_hit: 
                atk_type = "LIGHT" if player.state == "ATK1" else "HEAVY"
                # [Spec] 시간 기반 콤보 윈도우 체크
                now = pygame.time.get_ticks()
                if now - player.last_hit_time < COMBO_WINDOW_MS: player.combo_step += 1
                else: player.combo_step = 1
                player.last_hit_time = now
                combo_display.trigger(player.combo_step)
                screen_shake_timer, screen_shake_intensity = 10, (8 if atk_type == "HEAVY" else 4)
                if enemy.take_damage(10, player, atk_type): 
                    player.hit_gauge += 1
                    if player.hit_gauge >= 3: player.hit_gauge = 0; player.dash_charges = 1 
                hitstop_timer = HIT_STOP_LIGHT if atk_type == "LIGHT" else HIT_STOP_HEAVY
                player.has_hit = True

            if enemy.hitbox.colliderect(player.hurtbox) and not enemy.has_hit:
                e_atk = "LIGHT" if enemy.state == "ATK1" else "HEAVY"
                if player.take_damage(15, enemy, e_atk): 
                    hitstop_timer = HIT_STOP_LIGHT if e_atk == "LIGHT" else HIT_STOP_HEAVY
                    enemy.has_hit = True

        screen.fill((50, 50, 50))
        # [Spec] 다이나믹 카메라 좌표 연산
        cam_x = (player.rect.centerx + enemy.rect.centerx) // 2 - SCREEN_WIDTH // 2
        
        stage_text = font_large.render("STAGE 1 : THE LAST STAND", True, (200, 200, 200))
        screen.blit(stage_text, (SCREEN_WIDTH//2 - stage_text.get_width()//2, 20))
        pygame.draw.rect(screen, (80, 0, 0), (50, 70, 300, 25)) 
        hp_col = (0, 255, 0) if player.hp > 60 else (255, 255, 0) if player.hp > 30 else (255, 0, 0)
        pygame.draw.rect(screen, hp_col, (50, 70, 3 * player.hp, 25))
        pygame.draw.rect(screen, (255, 255, 255), (50, 70, 300, 25), 2)
        for i in range(3):
            col = (0, 200, 255) if i < player.hit_gauge else (60, 60, 60)
            pygame.draw.circle(screen, col, (80 + (i * 35), 680), 12)
        screen.blit(font_large.render(f"DASH: {player.dash_charges}", True, (255, 255, 255)), (210, 665))
        pygame.draw.rect(screen, (80, 0, 0), (930, 70, 300, 25)) 
        e_hp_col = (0, 255, 0) if enemy.hp > 30 else (255, 0, 0)
        pygame.draw.rect(screen, e_hp_col, (930, 70, 6 * enemy.hp, 25))
        pygame.draw.rect(screen, (255, 255, 255), (930, 70, 300, 25), 2)
        screen.blit(font_small.render("ENEMY B1", True, (255, 255, 255)), (930, 45))

        for entity in all_sprites: entity.draw_ghosts(screen, cam_x)
        ox, oy = 0, 0
        if screen_shake_timer > 0:
            ox, oy = random.randint(-screen_shake_intensity, screen_shake_intensity), random.randint(-screen_shake_intensity, screen_shake_intensity)
            screen_shake_timer -= 1

        for entity in all_sprites: screen.blit(entity.image, (entity.rect.x + ox - cam_x, entity.rect.y + oy))
        pygame.draw.line(screen, (100, 100, 100), (0 + ox - cam_x, GROUND_Y + oy), (SCREEN_WIDTH + ox - cam_x, GROUND_Y + oy), 2)
        if player.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), player.hitbox.move(ox - cam_x, oy), 2)
        if enemy.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), enemy.hitbox.move(ox - cam_x, oy), 2)
        pygame.draw.rect(screen, (0, 255, 0), player.hurtbox.move(ox - cam_x, oy), 1)
        pygame.draw.rect(screen, (0, 255, 0), enemy.hurtbox.move(ox - cam_x, oy), 1)

        for entity in all_sprites:
            if hasattr(entity, 'guard_effect_timer') and entity.guard_effect_timer > 0:
                y_v = 100 if entity.char_id == "A1" else (10 if entity.char_id == "B1" else 80)
                entity.guard_effect.draw(screen, entity.rect.centerx + ox - cam_x, entity.rect.centery + oy, 1 if entity.facing_right else -1, y_v)

        combo_display.draw(screen, player.rect, cam_x) 
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()
if __name__ == "__main__": main()