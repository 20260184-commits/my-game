import pygame
import random
import sys

pygame.init()

# --- 패링 관련 설정 ---
PARRY_DURATION = 15
PARRY_COOLDOWN = 45

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

def draw_hud(score, lives, score_timer):
    if score_timer > 0:
        score_text = f"Score: {score}"
        score_surf = font.render(score_text, True, WHITE)
        screen.blit(score_surf, ((WIDTH - score_surf.get_width()) // 2, HEIGHT - 50))
    
    lives_text = f"Lives: {'♥ ' * lives}"
    lives_surface = font.render(lives_text, True, RED)
    screen.blit(lives_surface, (WIDTH - lives_surface.get_width() - 10, 10))

def game_over_screen(score):
    screen.fill(GRAY)
    screen.blit(font_big.render("GAME OVER", True, RED), (220, 220))
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
    parry_effects = [] # 패링 이펙트 리스트
    score = 0
    last_score = 0
    lives = 3
    spawn_timer = 0
    invincible = 0
    
    parry_timer = 0
    parry_successful = False
    cooldown_timer = 0
    score_timer = 0

    level_idx = 0
    level_cfg = LEVELS[level_idx]

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

        # 타이머 관리
        if parry_timer > 0:
            parry_timer -= 1
            if parry_timer == 0 and not parry_successful:
                cooldown_timer = PARRY_COOLDOWN
        
        if cooldown_timer > 0:
            cooldown_timer -= 1

        # 이펙트 업데이트
        for fx in parry_effects[:]:
            fx["radius"] += 10 # 1초(60프레임) 동안 600까지 커지도록 속도 설정
            if fx["radius"] >= fx["max_radius"]:
                parry_effects.remove(fx)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and player.left  > 0:     player.x -= 5
        if keys[pygame.K_RIGHT] and player.right < WIDTH:  player.x += 5
        if keys[pygame.K_UP]    and player.top   > 0:     player.y -= 5
        if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += 5

        spawn_timer += 1
        if spawn_timer >= level_cfg["spawn"]:
            spawn_timer = 0
            rect, speed = spawn_enemy(level_cfg)
            enemies.append([rect, speed])

        survived = []
        for pair in enemies:
            pair[0].y += pair[1]
            if pair[0].top < HEIGHT:
                survived.append(pair)
            else:
                score += 1
        enemies = survived

        if invincible > 0:
            invincible -= 1
        else:
            if parry_timer > 0:
                new_enemies = []
                hit_something = False
                for pair in enemies:
                    if player.colliderect(pair[0]):
                        score += 5
                        hit_something = True
                    else:
                        new_enemies.append(pair)
                enemies = new_enemies
                
                if hit_something:
                    parry_timer = 0 
                    parry_successful = True
                    # 이펙트 추가: 플레이어 중심, 반지름 25에서 시작, 최대 반지름 600
                    parry_effects.append({"center": player.center, "radius": 25, "max_radius": 600})
            else:
                for pair in enemies:
                    if player.colliderect(pair[0]):
                        lives -= 1
                        invincible = 90
                        enemies.clear()
                        if lives <= 0:
                            if game_over_screen(score):
                                main()
                            return
                        break

        level_idx = min(score // 20, len(LEVELS) - 1)
        level_cfg = LEVELS[level_idx]

        screen.fill(GRAY)

        # 이펙트 그리기 (흰색)
        for fx in parry_effects:
            pygame.draw.circle(screen, WHITE, fx["center"], int(fx["radius"]), 3)

        if cooldown_timer > 0:
            player_color = RED
        elif parry_timer > 0:
            player_color = GREEN
        else:
            player_color = BLUE

        blink = (invincible // 10) % 2 == 0
        if blink or invincible == 0:
            pygame.draw.rect(screen, player_color, player)

        for pair in enemies:
            pygame.draw.rect(screen, RED, pair[0])

        draw_hud(score, lives, score_timer)
        pygame.display.flip()

main()