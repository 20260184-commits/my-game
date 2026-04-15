import pygame
import random
import sys
import base64
import io

# --- 설정 ---
MUSIC_FILE = r"assets\sounds\BBGGMM.wav" 
BOSS_TRIGGER_SCORE = 100  
BASE_ENEMY_SPEED_MIN = 4  
BASE_ENEMY_SPEED_MAX = 5  
BASE_SPAWN_RATE = 20      
COMBO_TIMEOUT = 600       
BOSS_WAVE_POSITIONS = [0.25, 0.1, 0.5, 0.9, 0.75]
WAVE_INTERVAL = 150 
FPS = 60

# --- 상수 ---
WIDTH, HEIGHT = 800, 600
PLAYER_W, PLAYER_H = 40, 60 
SPRITE_W, SPRITE_H = 150, 150 
ENEMY_W, ENEMY_H = 30, 30
HUD_HEIGHT = 90

WHITE, BLACK, BLUE, GREEN, RED, GRAY, DARK_GRAY = (255,255,255), (0,0,0), (50,120,220), (50,220,120), (220,50,50), (40,40,40), (20,20,20)
PARRY_DURATION = 15 
STATE_NORMAL, STATE_PHASE1, STATE_PHASE2 = 0, 1, 2
DEBUG_HITBOX = True

# --- 스프라이트 데이터 (사용자 입력 부분) ---
SHEETS = {
    "up": "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", 
    "parry": "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"

}

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodger Optimized")
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
        if not b64 or b64 == "...": continue
        try:
            sheet_bytes = base64.b64decode(b64)
            sheet = pygame.image.load(io.BytesIO(sheet_bytes)).convert_alpha()
            FRAME_W, FRAME_H = 96, 80
            frames = []
            for i in range(8):
                row, col = divmod(i, 8)
                rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
                frames.append(pygame.transform.scale(sheet.subsurface(rect), (SPRITE_W, SPRITE_H)))
            
            if direction == "parry": animations["parry"] = frames
            else:
                animations[f"walk_{direction}"] = frames
                animations[f"idle_{direction}"] = frames 
        except Exception as e: print(f"Error: {e}")
    return animations

PLAYER_ANIMATIONS = load_player_sprites()

def spawn_enemy(boss_state, min_spd, max_spd, diff_mult, target_x=None, y_offset=0):
    if boss_state == STATE_PHASE1:
        speed = 6
    else:
        speed_mult = 1.6 if boss_state != STATE_NORMAL else 1.0
        speed = int(random.randint(min_spd, max_spd) * speed_mult * diff_mult)
    
    if boss_state == STATE_NORMAL or boss_state == STATE_PHASE1:
        x = target_x if target_x is not None else random.randint(0, WIDTH - ENEMY_W)
        # [수정] HUD_HEIGHT 대신 HUD_HEIGHT - 100 으로 설정하여 화면 밖에서 생성
        # y_offset은 3줄 배치를 위해 그대로 유지
        return {"rect": pygame.Rect(x, HUD_HEIGHT - 100 + y_offset, ENEMY_W, ENEMY_H), "vel": (0, speed)}
    else:
        # [수정] 2페이지 적들도 좌우가 아닌 위에서 아래로 나오게 변경
        x = random.randint(0, WIDTH - ENEMY_W)
        return {"rect": pygame.Rect(x, HUD_HEIGHT - 50, ENEMY_W, ENEMY_H), "vel": (0, speed)}
    
def game_over_screen(score, title="GAME OVER", color=RED):
    overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(150); overlay.fill(BLACK)
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

def main():
    try: pygame.mixer.music.load(MUSIC_FILE); pygame.mixer.music.play(-1)
    except: pass

    player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 100, PLAYER_W, PLAYER_H)
    enemies, parry_effects = [], []
    score, lives, invincible = 0, 3, 0
    parry_timer, parry_cooldown, miss_timer, success_timer = 0, 0, 0, 0
    combo_count, combo_timer = 0, 0
    shake_timer, boss_parry_count = 0, 0
    boss_state = STATE_NORMAL
    boss_wave_count, boss_wave_timer = 0, 0
    spawn_timer, spawn_count = 0, 0 
    current_direction, parry_success = "up", False
    anim_frame, anim_timer, prev_state = 0, 0, ""
    
    MAX_PARRY_COOLDOWN = 3 * FPS
    MISS_DURATION = int(1.5 * FPS)

    while True:
        clock.tick(FPS)
        
        # --- 난이도 계산 ---
        diff_mult = 1.0
        if score >= 80: diff_mult = 1.4
        elif score >= 40: diff_mult = 1.3
        elif score >= 20: diff_mult = 1.1
        spawn_rate = int((BASE_SPAWN_RATE / 1.6 if boss_state != STATE_NORMAL else BASE_SPAWN_RATE) / diff_mult)
        
        # --- 입력 처리 ---
        keys = pygame.key.get_pressed()
        moving = False
        if parry_timer == 0: 
            if keys[pygame.K_LEFT]:  moving = True; player.x -= 5
            if keys[pygame.K_RIGHT]: moving = True; player.x += 5
            if keys[pygame.K_UP]:    current_direction = "up"; moving = True; player.y -= 5
            if keys[pygame.K_DOWN]:  moving = True; player.y += 5 
        player.clamp_ip(pygame.Rect(0, HUD_HEIGHT, WIDTH, HEIGHT - HUD_HEIGHT))

        # --- 애니메이션 상태 결정 ---
        state = "parry" if parry_timer > 0 else (f"walk_{current_direction}" if moving else f"idle_{current_direction}")
        if state != prev_state: anim_frame = 0; prev_state = state

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and parry_cooldown == 0:
                parry_timer, parry_success = PARRY_DURATION, False

        # --- 타이머 업데이트 ---
        if invincible > 0: invincible -= 1
        if combo_timer > 0: combo_timer -= 1
        else: combo_count = 0
        if shake_timer > 0: shake_timer -= 1
        if parry_cooldown > 0: parry_cooldown -= 1
        if miss_timer > 0: miss_timer -= 1
        if success_timer > 0: success_timer -= 1 # [추가] 성공 타이머 감소

        if state == "parry":
            # [핵심] 패링 유지 시간과 애니메이션 프레임을 직접 동기화
            # (전체 유지시간 - 남은 시간) / 전체 유지시간 = 진행률(0.0 ~ 1.0)
            if PLAYER_ANIMATIONS and "parry" in PLAYER_ANIMATIONS:
                frames = PLAYER_ANIMATIONS["parry"]
                progress = (PARRY_DURATION - parry_timer) / PARRY_DURATION
                anim_frame = int(progress * len(frames))
                # 마지막 프레임에서 멈추지 않고 범위 내에 있게 제한
                anim_frame = min(anim_frame, len(frames) - 1)
        else:
            # 일반 걷기/대기 애니메이션은 기존 timer 방식 유지
            anim_timer += 1
            if anim_timer >= 6: # 일반 속도 6
                if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS:
                    anim_frame = (anim_frame + 1) % len(PLAYER_ANIMATIONS[state])
                anim_timer = 0

        if parry_timer > 0: 
            parry_timer -= 1
            if parry_timer == 0 and not parry_success:
                miss_timer, parry_cooldown = MISS_DURATION, MAX_PARRY_COOLDOWN

        # --- 보스 상태 관리 ---
        if boss_state == STATE_NORMAL and score >= BOSS_TRIGGER_SCORE:
            boss_state, enemies, boss_parry_count, boss_wave_count, boss_wave_timer = STATE_PHASE1, [], 0, 0, 0

        # --- 스폰 로직 (최적화) ---
        if boss_state == STATE_PHASE1:
            boss_wave_timer += 1
            if boss_wave_timer >= WAVE_INTERVAL and boss_wave_count < 5:
                boss_wave_timer = 0
                safe_x = BOSS_WAVE_POSITIONS[boss_wave_count] * WIDTH
                for row_offset in [0, 40, 80]: 
                    for x in range(0, WIDTH, 40):
                        if abs(x - safe_x) > 40: 
                            enemies.append(spawn_enemy(boss_state, BASE_ENEMY_SPEED_MIN, BASE_ENEMY_SPEED_MAX, diff_mult, x, row_offset))
                boss_wave_count += 1
            if boss_wave_count >= 5 and not enemies:
                boss_state, boss_parry_count = STATE_PHASE2, 0
        elif boss_state == STATE_NORMAL:
            spawn_timer += 1
            if spawn_timer >= spawn_rate:
                spawn_timer = 0; spawn_count += 1
                tx = player.x + (PLAYER_W - ENEMY_W)//2 if spawn_count % 4 == 0 else None
                enemies.append(spawn_enemy(boss_state, BASE_ENEMY_SPEED_MIN, BASE_ENEMY_SPEED_MAX, diff_mult, tx))
        elif boss_state == STATE_PHASE2:
            spawn_timer += 1
            if spawn_timer >= int(spawn_rate * 0.7):
                spawn_timer = 0
                enemies.append(spawn_enemy(boss_state, BASE_ENEMY_SPEED_MIN, BASE_ENEMY_SPEED_MAX, diff_mult))

        # --- 충돌 처리 ---
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
                    parry_success = True
                    success_timer = int(1.5 * FPS) # [추가] Success 메시지 출력
                    miss_timer = 0
                          # 1. 성공 플래그를 True로 설정
                    enemies.remove(enemy)     # 2. 적을 리스트에서 제거 # redundant but safe
                    # [최적화] 보스전 점수 중지
                    if boss_state == STATE_NORMAL: score += int(1 * (1.2 ** combo_count))
                    combo_count += 1; combo_timer = COMBO_TIMEOUT; parry_timer = 0
                    if boss_state != STATE_NORMAL: boss_parry_count += 1
                    parry_effects.append({"pos": player.center, "radius": 10, "max_radius": 120})
                    if boss_parry_count >= 10:
                        if boss_state == STATE_PHASE1: boss_state, boss_parry_count, enemies = STATE_PHASE2, 0, []
                        elif boss_state == STATE_PHASE2: 
                            if game_over_screen(score, "VICTORY!", GREEN): main(); return
                elif invincible == 0:
                    lives -= 1; invincible = 60; combo_count = 0
                    shake_timer, parry_cooldown = 15, 0
                    if lives <= 0: 
                        if game_over_screen(score): main(); return
            elif enemy["rect"].top > HEIGHT or enemy["rect"].right < 0 or enemy["rect"].left > WIDTH:
                enemies.remove(enemy)
                if boss_state == STATE_NORMAL: score += 1

        # --- 렌더링 ---
        offset = (random.randint(-6, 6), random.randint(-6, 6)) if shake_timer > 0 else (0, 0)
        screen.fill(GRAY)
        for e in enemies: pygame.draw.rect(screen, RED, e["rect"].move(offset))
        if boss_state != STATE_NORMAL: pygame.draw.rect(screen, BLACK, boss_rect.move(offset))
        for fx in parry_effects[:]:
            pygame.draw.circle(screen, WHITE, (fx["pos"][0] + offset[0], fx["pos"][1] + offset[1]), int(fx["radius"]), 3)
            fx["radius"] += 6
            if fx["radius"] >= fx["max_radius"]: parry_effects.remove(fx)

        if invincible == 0 or (invincible // 5) % 2 == 0:
            if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS:
                img = PLAYER_ANIMATIONS[state][anim_frame % len(PLAYER_ANIMATIONS[state])]
                screen.blit(img, (player.x + offset[0] - (SPRITE_W - PLAYER_W)//2, player.y + offset[1] - (SPRITE_H - PLAYER_H)//2))
            else: pygame.draw.rect(screen, BLUE, player.move(offset))
            if DEBUG_HITBOX: pygame.draw.rect(screen, GREEN, player.move(offset), 2)

        if success_timer > 0:
            # 성공 시 초록색 Success!
            draw_text("Success!", player.centerx, player.top - 30, FONT_HUD, GREEN, center=True)
        elif miss_timer > 0:
            # 실패 시 빨간색 Miss!
            draw_text("Miss!", player.centerx, player.top - 30, FONT_HUD, RED, center=True)

        # 패링 바 렌더링
        bar_x, bar_y, bar_w, bar_h = player.x, player.bottom + 5, PLAYER_W, 6
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h))
        fill_w = bar_w if parry_cooldown == 0 else int(bar_w * ((MAX_PARRY_COOLDOWN - parry_cooldown) / MAX_PARRY_COOLDOWN))
        pygame.draw.rect(screen, BLUE, (bar_x, bar_y, fill_w, bar_h))

        pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, HUD_HEIGHT))
        draw_text(f"Lives: {'♥ ' * lives}", 15, 12, FONT_HUD, RED)
        draw_text(f"Score: {score}", WIDTH//2, 12, FONT_HUD, WHITE, center=True)
        draw_text(f"Combo: {combo_count}", WIDTH - 150, 12, FONT_HUD, GREEN)
        fps_text = f"FPS: {int(clock.get_fps())}"
        draw_text(fps_text, 15, 40, FONT_HUD, WHITE) # 좌표 (15, 40)은 적절히 조절하세요.
        
        if boss_state == STATE_PHASE2: draw_text(f"Boss Parry: {boss_parry_count}/10", WIDTH//2, 55, FONT_HUD, WHITE, center=True)

        pygame.display.flip()

if __name__ == "__main__":
    main()