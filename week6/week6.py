import pygame
import random
import sys
import math
import base64
import io

# --- 설정 ---
MUSIC_FILE = "assets\sounds\BBGGMM.wav"  # 여기에 사용할 음악 파일명을 입력하세요

# --- 스프라이트 시트 설정 (Base64 문자열을 여기에 붙여넣으세요) ---
SHEETS = {
    "left": "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",
    "right": "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",
    "down": "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",
    "up": "iVBORw0KGgoAAAANSUhEUgAAAwAAAABQCAYAAACu5xLkAAAAAXNSR0IArs4c6QAADLhJREFUeJzt3W9sHMUdxvFngx1wEGByjkViYysi8qWFpMgSlkiqqn9eFNkO0EgVvImg0BdFrYAmUvyColaq8iKRTKEU1UUoQCJV5UVVFc4RQlCkiEjIEZCGpLoDQxvnD8b1gktwLomdbF84s75bn8/nu93b3fP3gyJsn42Gmd88OzO750gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgHixwm4AgMXbdtt6J/fzoSnHymQyYTUHAFAl5D/8wAYAZSGAqq+lpUVtdcsdSVp33dUFv2f/sTRzugqofyxl1H/1kf/RUSv1H9tiqZUBiBMCKDyl9L3BGASD+o8O8r/6qP/wkP/hq8X6XxZ2AxajpaVFd7avde5sX+t4X+uqtxzvRQH+KTWAGAN/tbS0SFJe3w+fvRBqm5Yi6j985H94qP9wkf/hqtX6j/wGwCyAanUAoo4FaPhyFzzevh8+e8H9YzAH/FNO/dP//iH/w0X9h4/8D0+t13/kNwBGrQ5AHBBA4Tl9+rROnp3SybNTkuT+W5o7FgjGYusf/iP/w0P9h4v8D1ct13/kNwBW1nJqeQCizspaDgEUnkQi4X6c2/e5XzNfZzz8R/2Hi/wPF/UfHeR/9dV6/Ud+A5C1slY5A8ApkD+y1sw/0uICiP73h23bOvXFqbw3Fp08O6Xhsxfcfu/YtFUNG7bo5NkpvX3ma21ovV7f/Nbd9L8PqP9wkf/hov7DN1/+N2zYoo5NW92v/egbq/TeVR2htLFW1Xr9R34DYNu2yhmAuL0bO6ps21aD05BXzLkL0I5NW9Wxaas7Dhtar9d7V3XQ/z5JJBJ5dwGMJ557VgP7BjSwb8D92vU3d+rRrjW6I9mkB1ePVrOZNWuh+pcKb8C4EPuD/A8X+R+++fLf8OY+fe+fYvU/3wZs/7G0FZcxiPwGIJFIlBVA8EcikVDWylreUwizADVYfAbHexdgYN+Aenp63D9vvfaM7v1xjyTppc9u0uHMuHa+PhSLAIq6heqfORAs8j9c5H/4bNvW/m0btX/bRkmz+U/uB69Y/Rtxrv1YFEsikZBt22pd2epeCEz4PDXwhiRp9OR/9ODqUd2RbGIi+Mj0vdG6stUxAWQ8u+8NDTz1nCTpwdWj9L3P3ll3uyNJhy7OnHS+f3k67/XHXzugw0eHJckdh3/981XGwAel1L/EHAiKOf0k/8NB/kfD2491O0N/OyFpNv8L5f4DX34iSdq8vF7fHj7COFRoofqPe+1HvrEEUHTsbrvVkfIXoPOFUN/IccbAB7vbbnU2L693PzebAOM7f3/V7X+DTUAwCtW/VHgOPPfdaX3vmQP0f4XI/2gotACVOHyohlQq5TQ+/itJs/lfLPefnxxxv5frcOXefqzbkSRT/9mRSUnSDz94K/a1H5vGmouvxAI0DN5TaInFZzUkk0nnoWydCm0Cdp44pnePfJo3Btknt+vlG2+RxBj4qVD9S8yBaiH/w0X+h8d7CLT54w/m5P6hJx7Vh4mkpJkNwKGLU9rbMK1MJsM4VMhsfs0YvDk8kbf4N3I3YHG5+xL59wBIM+GzeXm9OwCdy+rUuawuL/wl6Wfbfy5JevnGW9zAQmV2t93q5PalGYOdJ47N+V4zAczPVaF5NS2VSjnpdFp7G2YXPG8OTyg7Mun2v/ciIM0sgC6dz1S3sTXKW/+5Cs2Bzt/2uR/v2rWLOeAD8j9cuVleLP+zT253P35n3e0O1wB/7G2Ydjdemz/+QFLh3N9gZ9xHgPY2TCudTiuVSjEGFdi1a5dTP3gm7wDu186/53yfGQMjLvUf+Q2AtxNLXYAW+lksXqp95ZxTz/kWnxvsmUXnA19+krdoRXl6eno0ODgoafbkraHtWjeAnt33hu7YuG7m9SsB5H08BZXJvfjmKjQHsk9u16GLU3p+ckTPT46o7k9/rlo7axX5Hz7vHCh2+GBq35xAo3KZTMba2zDtLv4L5b7x/uXZsRocHJzzXiUsjjfDi23AHvjyk7zHr1LtK6vUyvJFfgPgDZ83hyeKLkDNIBBA/ujr63M3AYcuTi0YQmbx39/fH0p7a8W5oRed7OGXJM1eAA5dnHJr/90jn857EeDWr3/6+/vdDMp99EqaOwdyN1/kjz+8+Z87B8j/6sidA8Xy3yw+Td9zDfBPOp2WVDz3jb6R45bJ/+zhl3Ru6EU2wmUqdPdlvrVPbv2n2leqr69v7n8wYiK/SHAcx1m/fr0eytZJmnvxPXx0OG8QOpfNfJ8JoN7e3sj/P0ZVKpVyzCn07t27dfDgQUkzIWQ8vaU772eOXCsWnz44N/SiM3F0SGt++ke3Lx3HcaTi/f/KKfreT47jOIODg9qxY4ceytblbcAM7xh0LqtjE+aTVCrlmL6XFpf/6XRalmUxBj4pJX+kmWtAf3+/eweTa3BlSu13aW7+n3nhEadxY5dWdP2EMShTMpl0cjdgxnxjcGZts/r6+tTT0xP5/Il048688Ijz/k0zt7B27NihUgfhlVMZyzz7RviUx5wa/GNslXp7e61SQ4gFqD/OvPCII2nOBoD+r55y5gD97y+T44vJf7MAlaTO0cG8OYTylJP/qVTK+X7zfyWJBWgFSsl9o9AGQBJzoALlbMDiUvt1YTdgISbAFxtALPwrM3F0SJLUmxMcpYYQKucN7Ptak3m3cQ/ec7d72inx7H9QJo4OMQdCZHK8jPx3Fz/wx2Jrv7e312IM/PX0lu683DdM/t/XmnRyNwEs/P1Rbu03buwKslkVi01xlLoL5gQuGLn9XyyE6P9gmA1AoX43zEWAMfDHXd19ev3Abkkz/f+Xk2n3QnDwnrvzvpe+Dxb5H67c/vfWvuGdA7nzB5Uh/8OzmNqX4tX/kb8DUIj39FPiBDRo99+8XtLsr+ArpHNZneQ5gYB/ioW/eZ15EJzcOeBl+t57Agf/Fcp/SfR/gIrVvkH+BIv8D4dlWdZ9rUmnFms/8r8FyLj/5vV6ekv3vDswMzjeRyXgn4UCCMEpdVGTe/qGyhQ6vSx1Dvz+l7/wuzlL2kL5L5FPQXrlVMYqpX/ZfAVjsfkPf5VS+3HMn9hsAKR4dnCtIIDCt2dytOjrub/2kFvv/lreaJV0Amc8+rs/BN2kJYVcCd9i8kcig/y20K+1XWh8ELy45VSsGrvQX+zCM+jBSibn3l0ZHx/P+9y2bfo/IIlEIq//m5qa1Nzc7H4+Njamzz//3JqYmKh625aCRCLh7Lz2pqLf0zdynPoPiKn/YmNA/wenUP578atvg5NMJh1v3nP9rZ6F1p97Jkdj1/+xOlL3/s1qvSe+cD9m9xsdjY2NYhGKWmRyptAiNNW+UhqpdouWHjMG3g2wJPo/Atra2jQywkCgtqTaV+atOY04rz1jtQEwxsbGJEl7G/JPoOO2+4qbTCZj5Z4CjY+Pa+rCBav+6qvdr123YkU4jVsCbNu2tt223pGkA5/N/I5hMxckTt+CdiVfnEQioT2TowXvwCA4tm1b3rtgps/nbAQQKHPdbWpqmvPaNddcU+3mLAmZTMZqbm52pPys6V69StLsNQHBGBsbU6q98B0Y27almD1RI8XsPQBjY2NzLrK2bVvdq1e5kwDBe3jtDXp47Q1a03yjdXl69rlE27atS1MXOf0PQFtbW97nhTa7K+rrtKI+lnv6OLFs27auBL6LxX91mKz31n+hawP8lclkrPHxcY2Pj+vKHLDMtcC8LkkfffRRqO2sZd46z50HHIAGr8D60/R7LPs+VqsF7wm0CZz9x9Kx7Pw46ejoUL01peOZjKW1XTNjcHlaly9Nu5uvv371vzCbWNMuXbokKb/Wx86ctprXtDgSp/8hsCQ5LDqrK7f+57seIDgm6/d7NsCm79e1rtLwKU6ig5Jb86x/wuHJ/Fj3fSwb750AQK1rbGzU9Pnz+vr8efdrK+rr9JsfdM68MfL1IeZClXnfFEkeVR/XAiw1e+7qIvNDUmuZH6tHgIzc247AUpG7+Jekc1Px+4tHakncw78WcC0AEIZayP9YPQIELFXzva+CU6BoqIWLAYDoI/PD433sEACwRO25q8sxt+QBALWtljI/lo8AAQAAACgPjwABQJk+PPVV2E0AAFQJmQ8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgPR/RyKFRlW8UrYAAAAASUVORK5CYII="


}

# --- 상수 및 설정 ---
WIDTH, HEIGHT = 800, 600
PLAYER_W, PLAYER_H = 60, 60 
SPRITE_W, SPRITE_H = 150, 150 
ENEMY_W, ENEMY_H = 30, 30
FPS = 60

# 색상
WHITE, BLACK, BLUE, GREEN, RED, GRAY, DARK_GRAY = (255,255,255), (0,0,0), (50,120,220), (50,220,120), (220,50,50), (40,40,40), (20,20,20)
PARRY_DURATION, PARRY_COOLDOWN, COMBO_DURATION = 15, 45, 600
STATE_NORMAL, STATE_TRANSITION, STATE_PHASE1, STATE_PHASE2, STATE_CLEAR = 0, 1, 2, 3, 4

# --- 초기화 ---
pygame.init()
pygame.mixer.init() # 음악 재생을 위한 믹서 초기화

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodger")
clock = pygame.time.Clock()

# 폰트
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
            animations[f"idle_{direction}"] = [frames[0]]
        except: continue
    return animations

PLAYER_ANIMATIONS = load_player_sprites()

LEVELS = [
    {"min_speed": 3, "max_speed": 5,  "spawn": 40, "label": "Lv.1"},
    {"min_speed": 5, "max_speed": 8,  "spawn": 25, "label": "Lv.2"},
    {"min_speed": 7, "max_speed": 12, "spawn": 15, "label": "Lv.3"},
]

def spawn_enemy(level_cfg):
    x = random.randint(0, WIDTH - ENEMY_W)
    speed = random.randint(level_cfg["min_speed"], level_cfg["max_speed"])
    return pygame.Rect(x, -ENEMY_H, ENEMY_W, ENEMY_H), speed

def draw_hud(score, lives, score_timer, combo_count, combo_multiplier):
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, 50))
    pygame.draw.line(screen, GRAY, (0, 50), (WIDTH, 50), 2)
    draw_text(f"Lives: {'♥ ' * lives}", 15, 12, FONT_HUD, RED)
    if score_timer > 0:
        draw_text(f"Score: {score}", WIDTH//2, 12, FONT_HUD, WHITE, center=True)
    if combo_count > 0:
        draw_text(f"Combo: {combo_count} (x{combo_multiplier:.1f})", WIDTH - 20, 12, FONT_HUD, GREEN, center=False)

def game_over_screen(score, title="GAME OVER", color=RED):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    draw_text(title, WIDTH//2, 220, FONT_BIG, color, center=True)
    draw_text(f"Score: {score}", WIDTH//2, 310, FONT_MSG, WHITE, center=True)
    draw_text("R: Restart   Q: Quit", WIDTH//2, 360, FONT_MSG, WHITE, center=True)
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

def main():
    # --- 배경 음악 재생 ---
    try:
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.set_volume(0.5) # 볼륨 0.0 ~ 1.0
        pygame.mixer.music.play(-1)        # -1은 무한 반복
    except:
        print(f"음악 파일을 찾을 수 없습니다: {MUSIC_FILE}")

    player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 60, PLAYER_W, PLAYER_H)
    current_direction = "down"
    anim_frame, anim_timer = 0, 0
    
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
        moving = False
        if keys[pygame.K_LEFT]:  current_direction = "left"; moving = True
        elif keys[pygame.K_RIGHT]: current_direction = "right"; moving = True
        elif keys[pygame.K_UP]:    current_direction = "up"; moving = True
        elif keys[pygame.K_DOWN]:  current_direction = "down"; moving = True
        
        state = f"walk_{current_direction}" if moving else f"idle_{current_direction}"
        anim_timer += 1
        if anim_timer >= 5:
            if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS:
                anim_frame = (anim_frame + 1) % len(PLAYER_ANIMATIONS[state])
            anim_timer = 0

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                if cooldown_timer == 0:
                    parry_timer = PARRY_DURATION
                    parry_successful = False

        # 로직 처리
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
        if keys[pygame.K_UP]    and player.top   > 50: player.y -= 5
        if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += 5

        # 보스 패턴 로직
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
            pygame.draw.rect(screen, RED, (WIDTH//2 - bar_width//2, 60, bar_width, 20))
            pygame.draw.rect(screen, GREEN, (WIDTH//2 - bar_width//2, 60, bar_width * (boss_hp / 100), 20))
        if boss_state == STATE_PHASE1:
            for sq in green_squares: pygame.draw.rect(screen, GREEN, sq)
            for b in yellow_bullets: pygame.draw.circle(screen, (255,255,0), (int(b["pos"][0]), int(b["pos"][1])), b["radius"])
        if boss_state == STATE_PHASE2:
            for w in earthquake_waves: pygame.draw.circle(screen, w['color'], (int(w['x']), int(w['y'])), int(w['radius']), 3)
            draw_text(f"Boss Parry: {boss_parry_count}/6", WIDTH//2, 90, FONT_HUD, WHITE, center=True)
            
        for fx in parry_effects: pygame.draw.circle(screen, WHITE, fx["center"], int(fx["radius"]), 3)

        blink = (invincible // 10) % 2 == 0
        if blink or invincible == 0:
            if PLAYER_ANIMATIONS and state in PLAYER_ANIMATIONS:
                img = PLAYER_ANIMATIONS[state][anim_frame % len(PLAYER_ANIMATIONS[state])]
                screen.blit(img, (player.x - (SPRITE_W - PLAYER_W)//2, player.y - (SPRITE_H - PLAYER_H)//2))
            else:
                pygame.draw.rect(screen, BLUE, player)

        for pair in enemies: pygame.draw.rect(screen, RED, pair[0])
        
        draw_hud(score, lives, score_timer, combo_count, combo_multiplier)
        pygame.display.flip()

if __name__ == "__main__":
    main()