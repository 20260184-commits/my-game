import pygame
import random
import sys
import math
import base64
import io

# --- 스프라이트 시트 설정 ---
# 달리기 앞 이미지
SHEET_B64 = "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" 
# 달리기 왼쪽 이미지

# 달리기 오른쪽 이미지

# 달리기 아래 이미지



# 1. 히트박스 크기 (충돌 판정용)
PLAYER_W, PLAYER_H = 80, 80 

# 2. 이미지 크기 (화면에 보여질 크기)
SPRITE_W, SPRITE_H = 200, 200 

# 애니메이션 구성
ANIMATION_CONFIG = {
    "idle": range(0, 4),
    "walk": range(4, 8),
    "parry": range(0, 4) 
}

def load_player_sprites():
    if not SHEET_B64: return None
    sheet_bytes = base64.b64decode(SHEET_B64)
    player_sheet = pygame.image.load(io.BytesIO(sheet_bytes)).convert_alpha()
    
    # 원본 시트의 한 칸 크기
    FRAME_W, FRAME_H = 96, 80
    COLS = 8
    
    # 시트 전체 프레임 추출 후 이미지 크기(SPRITE_W, SPRITE_H)로 스케일링
    all_frames = []
    for i in range(8):
        row, col = divmod(i, COLS)
        rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
        frame = player_sheet.subsurface(rect)
        scaled_frame = pygame.transform.scale(frame, (SPRITE_W, SPRITE_H))
        all_frames.append(scaled_frame)
        
    animations = {}
    for state, r in ANIMATION_CONFIG.items():
        animations[state] = [all_frames[i] for i in r]
    return animations

pygame.init()

# --- 설정 ---
PARRY_DURATION = 15
PARRY_COOLDOWN = 45
COMBO_DURATION = 600

def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE, BLACK, BLUE, GREEN, RED, GRAY = (255,255,255), (0,0,0), (50,120,220), (50,220,120), (220,50,50), (40,40,40)

STATE_NORMAL, STATE_TRANSITION, STATE_PHASE1, STATE_PHASE2, STATE_CLEAR = 0, 1, 2, 3, 4

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodger")
clock = pygame.time.Clock()
font = get_korean_font(36)
font_big = get_korean_font(72)

# 애니메이션 로드
PLAYER_ANIMATIONS = load_player_sprites()

LEVELS = [
    {"min_speed": 3, "max_speed": 5,  "spawn": 40, "label": "Lv.1"},
    {"min_speed": 5, "max_speed": 8,  "spawn": 25, "label": "Lv.2"},
    {"min_speed": 7, "max_speed": 12, "spawn": 15, "label": "Lv.3"},
]

ENEMY_W,  ENEMY_H  = 30, 30

def spawn_enemy(level_cfg):
    x = random.randint(0, WIDTH - ENEMY_W)
    speed = random.randint(level_cfg["min_speed"], level_cfg["max_speed"])
    return pygame.Rect(x, -ENEMY_H, ENEMY_W, ENEMY_H), speed

def draw_hud(score, lives, score_timer, combo_count, combo_multiplier, combo_timer):
    if score_timer > 0:
        score_surf = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_surf, ((WIDTH - score_surf.get_width()) // 2, HEIGHT - 50))
    if combo_count > 0:
        combo_surf = font.render(f"Combo: {combo_count} (x{combo_multiplier:.1f})", True, GREEN)
        screen.blit(combo_surf, (10, 80))
    lives_surf = font.render(f"Lives: {'♥ ' * lives}", True, RED)
    screen.blit(lives_surf, (WIDTH - lives_surf.get_width() - 10, 10))

def game_over_screen(score, title="GAME OVER", color=RED):
    screen.fill(GRAY)
    screen.blit(font_big.render(title, True, color), (220, 220))
    screen.blit(font.render(f"Score: {score}", True, WHITE), (350, 310))
    screen.blit(font.render("R: Restart   Q: Quit", True, WHITE), (270, 360))
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

def main():
    player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 60, PLAYER_W, PLAYER_H)
    
    current_state = "idle"
    last_state = "idle"
    anim_frame = 0
    anim_timer = 0
    
    enemies, parry_effects = [], []
    score, last_score, lives, spawn_timer, invincible = 0, 0, 3, 0, 0
    parry_timer, parry_successful, cooldown_timer, score_timer = 0, False, 0, 0
    combo_count, combo_multiplier, combo_timer = 0, 1.0, 0
    level_idx, level_cfg = 0, LEVELS[0]
    
    boss_state = STATE_NORMAL
    boss_hp = 100
    boss_rect = pygame.Rect(WIDTH // 2 - 40, HEIGHT // 2 - 40, 80, 80)
    boss_transition_timer = 0
    green_squares, yellow_bullets, bullet_spawn_timer = [], [], 0
    earthquake_waves, wave_spawn_timer, boss_parry_count = [], 0, 0

    while True:
        clock.tick(FPS)

        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
        
        if parry_timer > 0: current_state = "parry"
        elif moving: current_state = "walk"
        else: current_state = "idle"

        if current_state != last_state:
            anim_frame = 0
            last_state = current_state
        anim_timer += 1
        if anim_timer >= 5:
            anim_frame = (anim_frame + 1) % len(PLAYER_ANIMATIONS[current_state])
            anim_timer = 0

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                if cooldown_timer == 0:
                    parry_timer = PARRY_DURATION
                    parry_successful = False

        if score != last_score: score_timer = 60; last_score = score
        if score_timer > 0: score_timer -= 1
        if parry_timer > 0:
            parry_timer -= 1
            if parry_timer == 0 and not parry_successful: cooldown_timer = PARRY_COOLDOWN
        if cooldown_timer > 0: cooldown_timer -= 1
        if combo_timer > 0: combo_timer -= 1
        else: combo_count = 0; combo_multiplier = 1.0

        for fx in parry_effects[:]:
            fx["radius"] += 10
            if fx["radius"] >= fx["max_radius"]: parry_effects.remove(fx)

        if keys[pygame.K_LEFT]  and player.left  > 0: player.x -= 5
        if keys[pygame.K_RIGHT] and player.right < WIDTH: player.x += 5
        if keys[pygame.K_UP]    and player.top   > 0: player.y -= 5
        if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += 5

        # 보스 로직 (생략)
        if boss_state == STATE_NORMAL:
            spawn_timer += 1
            if spawn_timer >= level_cfg["spawn"]:
                spawn_timer = 0
                rect, speed = spawn_enemy(level_cfg)
                enemies.append([rect, speed])
            survived = []
            for pair in enemies:
                pair[0].y += pair[1]
                if pair[0].top < HEIGHT: survived.append(pair)
                else: score += 1
            enemies = survived
            if score >= 10:
                enemies.clear()
                boss_state = STATE_TRANSITION
                boss_transition_timer = 90
        elif boss_state == STATE_TRANSITION:
            boss_transition_timer -= 1
            if boss_transition_timer <= 0:
                boss_state = STATE_PHASE1
                offset = 95
                green_squares = [pygame.Rect(boss_rect.centerx - offset, boss_rect.centery - offset, 30, 30),
                                 pygame.Rect(boss_rect.centerx + offset - 30, boss_rect.centery - offset, 30, 30),
                                 pygame.Rect(boss_rect.centerx - offset, boss_rect.centery + offset - 30, 30, 30),
                                 pygame.Rect(boss_rect.centerx + offset - 30, boss_rect.centery + offset - 30, 30, 30)]
        elif boss_state == STATE_PHASE1:
            bullet_spawn_timer += 1
            if bullet_spawn_timer >= 30:
                bullet_spawn_timer = 0
                angle = math.atan2(player.centery - boss_rect.centery, player.centerx - boss_rect.centerx)
                yellow_bullets.append({"pos": list(boss_rect.center), "vel": [math.cos(angle) * 7, math.sin(angle) * 7], "radius": 8})
            for b in yellow_bullets[:]:
                b["pos"][0] += b["vel"][0]; b["pos"][1] += b["vel"][1]
                b_rect = pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)
                hit_sq = False
                for sq in green_squares[:]:
                    if b_rect.colliderect(sq): green_squares.remove(sq); hit_sq = True; break
                if hit_sq: yellow_bullets.remove(b); continue
                if not screen.get_rect().collidepoint(b["pos"]): yellow_bullets.remove(b)
            if len(green_squares) == 0: boss_hp = 50; boss_state = STATE_PHASE2
        elif boss_state == STATE_PHASE2:
            wave_spawn_timer += 1
            if wave_spawn_timer >= 100:
                wave_spawn_timer = 0
                earthquake_waves.append({"x": boss_rect.centerx, "y": boss_rect.centery, "radius": 0, "speed": 5, "color": RED})
            for w in earthquake_waves[:]:
                w["radius"] += w["speed"]
                if w["radius"] > WIDTH * 1.5: earthquake_waves.remove(w)

        # 충돌 판정
        if invincible > 0: invincible -= 1
        else:
            hit_detected = False
            if parry_timer > 0:
                for pair in enemies[:]:
                    if player.colliderect(pair[0]): enemies.remove(pair); hit_detected = True
                if boss_state == STATE_PHASE1:
                    for b in yellow_bullets[:]:
                        if player.colliderect(pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)): yellow_bullets.remove(b); hit_detected = True
                    for sq in green_squares[:]:
                        if player.colliderect(sq): green_squares.remove(sq); hit_detected = True
                    if player.colliderect(boss_rect): hit_detected = True
                if boss_state == STATE_PHASE2:
                    for w in earthquake_waves[:]:
                        dist = math.hypot(player.centerx - w['x'], player.centery - w['y'])
                        if abs(dist - w['radius']) < 40:
                            earthquake_waves.remove(w); boss_parry_count += 1; hit_detected = True
                            if boss_parry_count >= 6:
                                if game_over_screen(score, "VICTORY!", GREEN): main()
                                return
                if hit_detected:
                    combo_count += 1; combo_multiplier = round(combo_multiplier * 1.2, 2); combo_timer = COMBO_DURATION
                    score += int(1 * combo_multiplier); parry_timer = 0; parry_successful = True
                    parry_effects.append({"center": player.center, "radius": 25, "max_radius": 600})
            else:
                for pair in enemies:
                    if player.colliderect(pair[0]): hit_detected = True
                if boss_state != STATE_NORMAL and player.colliderect(boss_rect): hit_detected = True
                if boss_state == STATE_PHASE1:
                    for b in yellow_bullets:
                        if player.colliderect(pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)): hit_detected = True
                    for sq in green_squares:
                        if player.colliderect(sq): hit_detected = True
                if boss_state == STATE_PHASE2:
                    for w in earthquake_waves:
                        dist = math.hypot(player.centerx - w['x'], player.centery - w['y'])
                        if abs(dist - w['radius']) < 20: hit_detected = True
                if hit_detected:
                    lives -= 1; invincible = 90; enemies.clear(); combo_count = 0; combo_multiplier = 1.0; combo_timer = 0
                    if lives <= 0:
                        if game_over_screen(score, "GAME OVER", RED): main()
                        return

        # 그리기
        screen.fill(GRAY)
        if boss_state == STATE_TRANSITION: pygame.draw.rect(screen, WHITE, boss_rect, 2)
        if boss_state != STATE_NORMAL:
            pygame.draw.rect(screen, BLACK, boss_rect)
            bar_width = 300
            pygame.draw.rect(screen, RED, (WIDTH//2 - bar_width//2, 20, bar_width, 20))
            pygame.draw.rect(screen, GREEN, (WIDTH//2 - bar_width//2, 20, bar_width * (boss_hp / 100), 20))
        if boss_state == STATE_PHASE1:
            for sq in green_squares: pygame.draw.rect(screen, GREEN, sq)
            for b in yellow_bullets: pygame.draw.circle(screen, (255,255,0), (int(b["pos"][0]), int(b["pos"][1])), b["radius"])
        if boss_state == STATE_PHASE2:
            for w in earthquake_waves: pygame.draw.circle(screen, w['color'], (int(w['x']), int(w['y'])), int(w['radius']), 3)
            count_txt = font.render(f"Boss Parry: {boss_parry_count}/6", True, WHITE)
            screen.blit(count_txt, (WIDTH//2 - count_txt.get_width()//2, 50))
        for fx in parry_effects: pygame.draw.circle(screen, WHITE, fx["center"], int(fx["radius"]), 3)

        # 플레이어 그리기 (히트박스 중심과 이미지 중심 정렬)
        blink = (invincible // 10) % 2 == 0
        if blink or invincible == 0:
            if PLAYER_ANIMATIONS:
                # 이미지와 히트박스 크기 차이만큼 오프셋 계산
                offset_x = (SPRITE_W - PLAYER_W) // 2
                offset_y = (SPRITE_H - PLAYER_H) // 2
                screen.blit(PLAYER_ANIMATIONS[current_state][anim_frame], (player.x - offset_x, player.y - offset_y))
            else:
                pygame.draw.rect(screen, BLUE, player)

        for pair in enemies: pygame.draw.rect(screen, RED, pair[0])
        draw_hud(score, lives, score_timer, combo_count, combo_multiplier, combo_timer)
        pygame.display.flip()

main()