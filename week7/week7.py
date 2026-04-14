import pygame
import random
import sys
import math
import base64
import io

# --- 설정 ---
MUSIC_FILE = r"assets\sounds\BBGGMM.wav" 
BOSS_TRIGGER_SCORE = 100  
BASE_ENEMY_SPEED_MIN = 4  
BASE_ENEMY_SPEED_MAX = 5  
BASE_SPAWN_RATE = 20      
COMBO_TIMEOUT = 600       

# --- 스프라이트 시트 설정 (Base64 문자열을 여기에 붙여넣으세요) ---
SHEETS = {
    "up": "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"
}

# --- 상수 ---
WIDTH, HEIGHT = 800, 600
PLAYER_W, PLAYER_H = 40, 60 
SPRITE_W, SPRITE_H = 150, 150 
ENEMY_W, ENEMY_H = 30, 30
FPS = 60
HUD_HEIGHT = 90

WHITE, BLACK, BLUE, GREEN, RED, GRAY, DARK_GRAY = (255,255,255), (0,0,0), (50,120,220), (50,220,120), (220,50,50), (40,40,40), (20,20,20)
PARRY_DURATION = 15
STATE_NORMAL, STATE_PHASE1, STATE_PHASE2 = 0, 1, 2
DEBUG_HITBOX = True

# --- 초기화 ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodger")
clock = pygame.time.Clock()

FONT_HUD = pygame.font.SysFont("arial", 24, bold=True)
FONT_BIG = pygame.font.SysFont("arial", 72, bold=True)
FONT_MSG = pygame.font.SysFont("arial", 32, bold=True)

def draw_text(text, x, y, font, color, center=False, shadow=True):
    if shadow:
        s_surf = font.render(text, True, BLACK)
        pos = (x - s_surf.get_width()//2 + 2, y + 2) if center else (x + 2, y + 2)
        screen.blit(s_surf, pos)
    surf = font.render(text, True, color)
    pos = (x - surf.get_width()//2, y) if center else (x, y)
    screen.blit(surf, pos)

def load_player_sprites():
    animations = {}
    for direction, b64 in SHEETS.items():
        if not b64: continue
        try:
            sheet_bytes = base64.b64decode(b64)
            sheet = pygame.image.load(io.BytesIO(sheet_bytes)).convert_alpha()
            FRAME_W, FRAME_H = 96, 80
            COLS = 8
            frames = []
            for i in range(8):
                row, col = divmod(i, COLS)
                rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
                frame = sheet.subsurface(rect)
                scaled = pygame.transform.scale(frame, (SPRITE_W, SPRITE_H))
                frames.append(scaled)
            animations[f"walk_{direction}"] = frames
            animations[f"idle_{direction}"] = frames 
        except: continue
    return animations

PLAYER_ANIMATIONS = load_player_sprites()

def game_over_screen(score, title="GAME OVER", color=RED):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    draw_text(title, WIDTH//2, 220, FONT_BIG, color, center=True)
    draw_text(f"Score: {score}", WIDTH//2, 310, FONT_MSG, WHITE, center=True)
    draw_text("Press [R] to Restart | [Q] to Quit", WIDTH//2, 400, FONT_HUD, WHITE, center=True)
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

def spawn_enemy(boss_state, min_spd, max_spd, diff_mult, target_x=None):
    # 난이도 배수(diff_mult) 적용
    speed_mult = 1.6 if boss_state != STATE_NORMAL else 1.0
    speed = int(random.randint(min_spd, max_spd) * speed_mult * diff_mult)
    
    if boss_state == STATE_NORMAL or boss_state == STATE_PHASE1:
        # target_x가 지정되면 플레이어 위치에, 아니면 랜덤 위치에 생성
        x = target_x if target_x is not None else random.randint(0, WIDTH - ENEMY_W)
        return {"rect": pygame.Rect(x, HUD_HEIGHT, ENEMY_W, ENEMY_H), "vel": (0, speed)}
    else:
        is_left = random.random() < 0.5
        y = random.randint(HUD_HEIGHT + 50, HEIGHT - ENEMY_H)
        return {"rect": pygame.Rect(-ENEMY_W if is_left else WIDTH, y, ENEMY_W, ENEMY_H), "vel": (speed if is_left else -speed, 0)}

def main():
    try: pygame.mixer.music.load(MUSIC_FILE); pygame.mixer.music.play(-1)
    except: pass

    player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 100, PLAYER_W, PLAYER_H)
    enemies, parry_effects = [], []
    score, lives, invincible = 0, 3, 0
    parry_timer = 0
    combo_count, combo_timer = 0, 0
    shake_timer = 0
    boss_state = STATE_NORMAL
    boss_parry_count = 0
    spawn_timer = 0
    spawn_count = 0 # 적 생성 횟수 추적
    current_direction = "up"
    anim_frame, anim_timer = 0, 0

    while True:
        clock.tick(FPS)
        
        # --- 난이도 계산 (점수 기반) ---
        diff_mult = 1.0
        if score >= 80: diff_mult = 1.4
        elif score >= 40: diff_mult = 1.3
        elif score >= 20: diff_mult = 1.1
        
        # 생성 속도 계산 (보스 상태 및 점수 배수 적용)
        base_rate = BASE_SPAWN_RATE / 1.6 if boss_state != STATE_NORMAL else BASE_SPAWN_RATE
        spawn_rate = int(base_rate / diff_mult)
        
        keys = pygame.key.get_pressed()
        moving = False
        if keys[pygame.K_LEFT]:  moving = True; player.x -= 5
        if keys[pygame.K_RIGHT]: moving = True; player.x += 5
        if keys[pygame.K_UP]:    current_direction = "up"; moving = True; player.y -= 5
        if keys[pygame.K_DOWN]:  moving = True; player.y += 5 
        
        player.clamp_ip(pygame.Rect(0, HUD_HEIGHT, WIDTH, HEIGHT - HUD_HEIGHT))
        state = f"walk_{current_direction}" if moving else f"idle_{current_direction}"
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE: parry_timer = PARRY_DURATION

        if invincible > 0: invincible -= 1
        if combo_timer > 0: combo_timer -= 1
        else: combo_count = 0
        if shake_timer > 0: shake_timer -= 1
        
        anim_timer += 1
        if anim_timer >= 5:
            if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS: anim_frame = (anim_frame + 1) % len(PLAYER_ANIMATIONS[state])
            anim_timer = 0
        if parry_timer > 0: parry_timer -= 1

        if boss_state == STATE_NORMAL and score >= BOSS_TRIGGER_SCORE:
            boss_state = STATE_PHASE1
            enemies.clear(); boss_parry_count = 0
        
        spawn_timer += 1
        if spawn_timer >= spawn_rate:
            spawn_timer = 0
            spawn_count += 1
            
            # 2번째, 4번째... 짝수 번째 적은 플레이어의 X 위치에 생성
            target_x = None
            if spawn_count % 4 == 0:
                target_x = player.x + (PLAYER_W - ENEMY_W)//2
                
            enemies.append(spawn_enemy(boss_state, BASE_ENEMY_SPEED_MIN, BASE_ENEMY_SPEED_MAX, diff_mult, target_x))
        
        boss_rect = pygame.Rect(WIDTH//2 - 40, HUD_HEIGHT + 20, 80, 80)
        if boss_state != STATE_NORMAL and player.colliderect(boss_rect) and invincible == 0:
            lives -= 1; invincible = 60; combo_count = 0
            if lives <= 0:
                if game_over_screen(score): main(); return

        for enemy in enemies[:]:
            enemy["rect"].x += enemy["vel"][0]
            enemy["rect"].y += enemy["vel"][1]
            
            if player.colliderect(enemy["rect"]):
                if parry_timer > 0:
                    enemies.remove(enemy)
                    score += int(1 * (1.2 ** combo_count))
                    combo_count += 1; combo_timer = COMBO_TIMEOUT
                    invincible = 10  # 패링 성공 직후 10프레임 동안 무적 (애매한 피격 방지)
                    parry_timer = 0
                    shake_timer = 10
                    if boss_state != STATE_NORMAL: boss_parry_count += 1
                    parry_effects.append({"pos": player.center, "radius": 10, "max_radius": 120})
                    if boss_parry_count >= 10:
                        if boss_state == STATE_PHASE1: boss_state = STATE_PHASE2; boss_parry_count = 0; enemies.clear()
                        elif boss_state == STATE_PHASE2: 
                            if game_over_screen(score, "VICTORY!", GREEN): main(); return
                elif invincible == 0:
                    lives -= 1; invincible = 60; combo_count = 0
                    if lives <= 0:
                        if game_over_screen(score): main(); return
            elif enemy["rect"].right < 0 or enemy["rect"].left > WIDTH or enemy["rect"].top > HEIGHT or enemy["rect"].bottom < HUD_HEIGHT:
                enemies.remove(enemy); score += 1
        
        offset = (random.randint(-6, 6), random.randint(-6, 6)) if shake_timer > 0 else (0, 0)
        screen.fill(GRAY)
        for enemy in enemies: pygame.draw.rect(screen, RED, enemy["rect"].move(offset))
        if boss_state != STATE_NORMAL:
            pygame.draw.rect(screen, BLACK, boss_rect.move(offset))
        for fx in parry_effects[:]:
            pygame.draw.circle(screen, WHITE, (fx["pos"][0] + offset[0], fx["pos"][1] + offset[1]), int(fx["radius"]), 3)
            fx["radius"] += 6
            if fx["radius"] >= fx["max_radius"]: parry_effects.remove(fx)

        if invincible == 0 or (invincible // 5) % 2 == 0:
            if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS:
                img = PLAYER_ANIMATIONS[state][anim_frame % len(PLAYER_ANIMATIONS[state])]
                screen.blit(img, (player.x + offset[0] - (SPRITE_W - PLAYER_W)//2, player.y + offset[1] - (SPRITE_H - PLAYER_H)//2))
            else:
                pygame.draw.rect(screen, BLUE, player.move(offset))
            if DEBUG_HITBOX:
                pygame.draw.rect(screen, GREEN, player.move(offset), 2)
        
        pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, HUD_HEIGHT))
        draw_text(f"Lives: {'♥ ' * lives}", 15, 12, FONT_HUD, RED)
        draw_text(f"Score: {score}", WIDTH//2, 12, FONT_HUD, WHITE, center=True)
        draw_text(f"Combo: {combo_count}", WIDTH - 150, 12, FONT_HUD, GREEN)
        if boss_state != STATE_NORMAL:
            draw_text(f"Boss Parry: {boss_parry_count}/10", WIDTH//2, 55, FONT_HUD, WHITE, center=True)

        pygame.display.flip()

if __name__ == "__main__":
    main()