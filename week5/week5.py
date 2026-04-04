import pygame
import random
import sys
import math

pygame.init()

# --- 패링 및 콤보 관련 설정 ---
PARRY_DURATION = 15
PARRY_COOLDOWN = 45
COMBO_DURATION = 600  # 10초 (60 FPS * 10)

def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0:
            return font
    return pygame.font.SysFont(None, size)

WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
BLUE   = (50,  120, 220)
GREEN  = (50,  220, 120) 
RED    = (220, 50,  50)
GRAY   = (40,  40,  40)

STATE_NORMAL = 0
STATE_TRANSITION = 1
STATE_PHASE1 = 2
STATE_PHASE2 = 3
STATE_CLEAR = 4

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodger")
clock = pygame.time.Clock()
font = get_korean_font(36)
font_big = get_korean_font(72)

LEVELS = [
    {"min_speed": 3, "max_speed": 5,  "spawn": 40, "label": "Lv.1"},
    {"min_speed": 5, "max_speed": 8,  "spawn": 25, "label": "Lv.2"},
    {"min_speed": 7, "max_speed": 12, "spawn": 15, "label": "Lv.3"},
]

PLAYER_W, PLAYER_H = 50, 30
ENEMY_W,  ENEMY_H  = 30, 30

def spawn_enemy(level_cfg):
    x = random.randint(0, WIDTH - ENEMY_W)
    speed = random.randint(level_cfg["min_speed"], level_cfg["max_speed"])
    return pygame.Rect(x, -ENEMY_H, ENEMY_W, ENEMY_H), speed

def draw_hud(score, lives, score_timer, combo_count, combo_multiplier, combo_timer):
    # 점수 UI
    if score_timer > 0:
        score_text = f"Score: {score}"
        score_surf = font.render(score_text, True, WHITE)
        screen.blit(score_surf, ((WIDTH - score_surf.get_width()) // 2, HEIGHT - 50))
    
    # 콤보 UI
    if combo_count > 0:
        combo_text = f"Combo: {combo_count} (x{combo_multiplier:.1f})"
        combo_surf = font.render(combo_text, True, GREEN)
        screen.blit(combo_surf, (10, 80))
    
    # 라이브 UI
    lives_text = f"Lives: {'♥ ' * lives}"
    lives_surface = font.render(lives_text, True, RED)
    screen.blit(lives_surface, (WIDTH - lives_surface.get_width() - 10, 10))

def game_over_screen(score, title="GAME OVER", color=RED):
    screen.fill(GRAY)
    screen.blit(font_big.render(title, True, color), (220, 220))
    screen.blit(font.render(f"Score: {score}", True, WHITE), (350, 310))
    screen.blit(font.render("R: Restart   Q: Quit", True, WHITE), (270, 360))
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

def main():
    player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 60, PLAYER_W, PLAYER_H)
    enemies = []
    parry_effects = []
    score = 0
    last_score = 0
    lives = 3
    spawn_timer = 0
    invincible = 0
    
    parry_timer = 0
    parry_successful = False
    cooldown_timer = 0
    score_timer = 0
    
    combo_count = 0
    combo_multiplier = 1.0
    combo_timer = 0

    level_idx = 0
    level_cfg = LEVELS[level_idx]

    # --- 보스 관련 변수 ---
    boss_state = STATE_NORMAL
    boss_hp = 100
    boss_rect = pygame.Rect(WIDTH // 2 - 40, HEIGHT // 2 - 40, 80, 80)
    boss_transition_timer = 0
    
    # Phase 1 관련
    green_squares = []
    yellow_bullets = []
    bullet_spawn_timer = 0
    
    # Phase 2 관련
    earthquake_waves = []
    wave_spawn_timer = 0
    boss_parry_count = 0

    while True:
        clock.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                if cooldown_timer == 0:
                    parry_timer = PARRY_DURATION
                    parry_successful = False

        if score != last_score:
            score_timer = 60
            last_score = score
        if score_timer > 0: score_timer -= 1

        if parry_timer > 0:
            parry_timer -= 1
            if parry_timer == 0 and not parry_successful:
                cooldown_timer = PARRY_COOLDOWN
        
        if cooldown_timer > 0: cooldown_timer -= 1
        if combo_timer > 0: combo_timer -= 1
        else:
            combo_count = 0
            combo_multiplier = 1.0

        for fx in parry_effects[:]:
            fx["radius"] += 10
            if fx["radius"] >= fx["max_radius"]:
                parry_effects.remove(fx)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and player.left  > 0:     player.x -= 5
        if keys[pygame.K_RIGHT] and player.right < WIDTH:  player.x += 5
        if keys[pygame.K_UP]    and player.top   > 0:     player.y -= 5
        if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += 5

        # --- 게임 로직 분기 ---
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
                # [수정] 사각형 위치: 보스(80x80) 외곽에서 40px 떨어지도록 offset 계산
                # 보스 중심에서 사각형 중심까지 거리 = 40(보스반폭) + 40(간격) + 15(사각형반폭) = 95
                offset = 95 
                green_squares = [
                    pygame.Rect(boss_rect.centerx - offset, boss_rect.centery - offset, 30, 30),
                    pygame.Rect(boss_rect.centerx + offset - 30, boss_rect.centery - offset, 30, 30),
                    pygame.Rect(boss_rect.centerx - offset, boss_rect.centery + offset - 30, 30, 30),
                    pygame.Rect(boss_rect.centerx + offset - 30, boss_rect.centery + offset - 30, 30, 30)
                ]

        elif boss_state == STATE_PHASE1:
            # [수정] 탄막 소환 속도 향상 (50 -> 30)
            bullet_spawn_timer += 1
            if bullet_spawn_timer >= 30:
                bullet_spawn_timer = 0
                angle = math.atan2(player.centery - boss_rect.centery, player.centerx - boss_rect.centerx)
                yellow_bullets.append({
                    "pos": list(boss_rect.center),
                    "vel": [math.cos(angle) * 7, math.sin(angle) * 7], # [수정] 탄막 속도 향상 (4 -> 7)
                    "radius": 8
                })

            for b in yellow_bullets[:]:
                b["pos"][0] += b["vel"][0]
                b["pos"][1] += b["vel"][1]
                b_rect = pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)
                
                hit_sq = False
                for sq in green_squares[:]:
                    if b_rect.colliderect(sq):
                        green_squares.remove(sq)
                        hit_sq = True
                        break
                if hit_sq:
                    yellow_bullets.remove(b)
                    continue
                
                if not screen.get_rect().collidepoint(b["pos"]):
                    yellow_bullets.remove(b)

            if len(green_squares) == 0:
                boss_hp = 50
                boss_state = STATE_PHASE2

        elif boss_state == STATE_PHASE2:
            wave_spawn_timer += 1
            if wave_spawn_timer >= 100:
                wave_spawn_timer = 0
                earthquake_waves.append({
                    "x": boss_rect.centerx, "y": boss_rect.centery, 
                    "radius": 0, "speed": 5, "color": RED
                })
            
            for w in earthquake_waves[:]:
                w["radius"] += w["speed"]
                if w["radius"] > WIDTH * 1.5:
                    earthquake_waves.remove(w)

        # --- [통합] 충돌 및 데미지 판정 ---
        if invincible > 0:
            invincible -= 1
        else:
            hit_detected = False
            
            # 1. 패링 중일 때 (쳐내기)
            if parry_timer > 0:
                # 일반 적 패링
                for pair in enemies[:]:
                    if player.colliderect(pair[0]):
                        enemies.remove(pair)
                        hit_detected = True
                
                # 보스 1페이즈 패링 (탄막, 사각형, 보스)
                if boss_state == STATE_PHASE1:
                    for b in yellow_bullets[:]:
                        if player.colliderect(pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)):
                            yellow_bullets.remove(b)
                            hit_detected = True
                    for sq in green_squares[:]:
                        if player.colliderect(sq):
                            green_squares.remove(sq)
                            hit_detected = True
                    if player.colliderect(boss_rect):
                        hit_detected = True
                
                # [수정] 보스 2페이즈 패링 (지진파를 쳐내기)
                if boss_state == STATE_PHASE2:
                    for w in earthquake_waves[:]:
                        dist = math.hypot(player.centerx - w['x'], player.centery - w['y'])
                        # 지진파 경계선 근처에 플레이어가 있다면 패링 성공!
                        if abs(dist - w['radius']) < 40: 
                            earthquake_waves.remove(w)
                            boss_parry_count += 1
                            hit_detected = True
                            
                            # [수정] 카운트가 6이 되었을 때만 승리 화면을 띄우고 함수를 종료(return)함
                            if boss_parry_count >= 6:
                                if game_over_screen(score, "VICTORY!", GREEN):
                                    main()
                                return # 보스를 이겼을 때만 루프를 완전히 빠져나감
                # 패링 성공 시 공통 효과 (이 부분은 기존과 동일)
                if hit_detected:
                    combo_count += 1
                    combo_multiplier = round(combo_multiplier * 1.2, 2)
                    combo_timer = COMBO_DURATION
                    score += int(1 * combo_multiplier)
                    parry_timer = 0 
                    parry_successful = True
                    parry_effects.append({"center": player.center, "radius": 25, "max_radius": 600})

            # 2. 패링 중이 아닐 때 (데미지 입음)
            else:
                for pair in enemies:
                    if player.colliderect(pair[0]): hit_detected = True
                if boss_state != STATE_NORMAL and player.colliderect(boss_rect): hit_detected = True
                
                if boss_state == STATE_PHASE1:
                    for b in yellow_bullets:
                        if player.colliderect(pygame.Rect(b["pos"][0]-8, b["pos"][1]-8, 16, 16)):
                            hit_detected = True
                    for sq in green_squares:
                        if player.colliderect(sq): hit_detected = True
                
                if boss_state == STATE_PHASE2:
                    for w in earthquake_waves:
                        dist = math.hypot(player.centerx - w['x'], player.centery - w['y'])
                        if abs(dist - w['radius']) < 20:
                            hit_detected = True

                if hit_detected:
                    lives -= 1
                    invincible = 90
                    enemies.clear()
                    combo_count = 0
                    combo_multiplier = 1.0
                    combo_timer = 0
                    if lives <= 0:
                        if game_over_screen(score, "GAME OVER", RED):
                            main()
                        return

        # --- 그리기 로직 ---
        screen.fill(GRAY)
        if boss_state == STATE_TRANSITION:
            pygame.draw.rect(screen, WHITE, boss_rect, 2)

        if boss_state != STATE_NORMAL:
            pygame.draw.rect(screen, BLACK, boss_rect)
            bar_width = 300
            pygame.draw.rect(screen, RED, (WIDTH//2 - bar_width//2, 20, bar_width, 20))
            current_hp_w = bar_width * (boss_hp / 100)
            pygame.draw.rect(screen, GREEN, (WIDTH//2 - bar_width//2, 20, current_hp_w, 20))

        if boss_state == STATE_PHASE1:
            for sq in green_squares: pygame.draw.rect(screen, GREEN, sq)
            for b in yellow_bullets: pygame.draw.circle(screen, (255, 255, 0), (int(b["pos"][0]), int(b["pos"][1])), b["radius"])

        if boss_state == STATE_PHASE2:
            for w in earthquake_waves:
                pygame.draw.circle(screen, w['color'], (int(w['x']), int(w['y'])), int(w['radius']), 3)
            count_txt = font.render(f"Boss Parry: {boss_parry_count}/6", True, WHITE)
            screen.blit(count_txt, (WIDTH//2 - count_txt.get_width()//2, 50))

        if boss_state == STATE_CLEAR:
            screen.fill(GRAY)
            screen.blit(font_big.render("VICTORY!", True, GREEN), (WIDTH//2 - 150, HEIGHT//2 - 50))
            pygame.display.flip()
            # (승리 후 대기 로직 생략)

        for fx in parry_effects:
            pygame.draw.circle(screen, WHITE, fx["center"], int(fx["radius"]), 3)

        if cooldown_timer > 0: player_color = RED
        elif parry_timer > 0: player_color = GREEN
        else: player_color = BLUE

        blink = (invincible // 10) % 2 == 0
        if blink or invincible == 0:
            pygame.draw.rect(screen, player_color, player)

        for pair in enemies:
            pygame.draw.rect(screen, RED, pair[0])

        draw_hud(score, lives, score_timer, combo_count, combo_multiplier, combo_timer)
        pygame.display.flip()

main()