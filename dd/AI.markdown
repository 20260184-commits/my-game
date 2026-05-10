main.py
```
import pygame
import sys
import random
import os
from settings import *
from player import Player
from entities import EnemyB, EnemyA2, EnemyC1, Boss

# --- 히트 스파크 입자 클래스 ---
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.lifetime = 20
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size -= 0.1

    def draw(self, screen, offset):
        if self.lifetime > 0:
            pygame.draw.rect(screen, self.color, 
                             (self.x + offset[0], self.y + offset[1], max(0, self.size), max(0, self.size)))

def main():
    game_state = {
        'hit_stop_timer': 0,
        'screen_shake_timer': 0,
        'screen_offset': [0, 0],
        'particles': [] # 입자 리스트 초기화 (에러 방지)
    }

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand")
    clock = pygame.time.Clock()
    
    if not os.path.exists("assets"): os.makedirs("assets")

    player = Player()
    current_stage = 1
    enemy = EnemyB(800, SCREEN_HEIGHT-135)
    debug_mode = False 
    
    running = True
    while running:
        p_rect = None
        e_rect = None

        if game_state['hit_stop_timer'] > 0: 
            game_state['hit_stop_timer'] -= 1
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        debug_mode = not debug_mode
                    # [중요] player.py에 이 함수가 있어야 함
                    player.handle_single_input(event)

            # [중요] player.py에 이 함수가 있어야 함
            player.handle_continuous_input()
            player.apply_physics()
            player.update()
            
            if enemy:
                enemy.update(player)
                enemy.apply_physics()
                
                if player.rect.colliderect(enemy.rect):
                    if not player.is_jumping: 
                        if player.rect.centerx < enemy.rect.centerx: 
                            player.rect.right = enemy.rect.left
                        else: 
                            player.rect.left = enemy.rect.right
                
                p_rect, p_dmg = player.get_attack_rect(player.attack_type, 10 if player.attack_type=="LIGHT" else 20)
                if p_rect and p_rect.colliderect(enemy.hurtbox) and not player.has_hit:
                    enemy.take_damage(p_dmg, player.direction, game_state)
                    player.has_hit = True
                    # 스파크 생성
                    for _ in range(15):
                        game_state['particles'].append(Particle(p_rect.centerx, p_rect.centery, SPARK_COLOR))
                
                e_rect, e_dmg = enemy.get_attack_rect()
                if e_rect and e_rect.colliderect(player.hurtbox) and not enemy.has_hit:
                    player.take_damage(e_dmg, enemy.direction, game_state)
                    enemy.has_hit = True
                    # 스파크 생성
                    for _ in range(15):
                        game_state['particles'].append(Particle(e_rect.centerx, e_rect.centery, SPARK_COLOR))
                
                if enemy.hp <= 0:
                    current_stage += 1
                    if current_stage == 2: enemy = EnemyA2(800, SCREEN_HEIGHT-160)
                    elif current_stage == 3: enemy = EnemyC1(800, SCREEN_HEIGHT-160)
                    elif current_stage == 4: enemy = Boss(800, SCREEN_HEIGHT-160)
                    else: enemy = None 

            if player.hp <= 0: running = False

        # 입자 업데이트
        for p in game_state['particles'][:]:
            p.update()
            if p.lifetime <= 0:
                game_state['particles'].remove(p)

        if game_state['screen_shake_timer'] > 0:
            game_state['screen_offset'] = [random.randint(-5, 5), random.randint(-5, 5)]
            game_state['screen_shake_timer'] -= 1
        else: 
            game_state['screen_offset'] = [0, 0]

        screen.fill(BG_COLOR) 
        
        # 입자 그리기
        for p in game_state['particles']:
            p.draw(screen, game_state['screen_offset'])

        if enemy: enemy.draw(screen, game_state['screen_offset'])
        player.draw(screen, game_state['screen_offset'])
        
        if debug_mode:
            if p_rect:
                pygame.draw.rect(screen, (255, 0, 0), p_rect.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 2)
            if e_rect:
                pygame.draw.rect(screen, (0, 255, 0), e_rect.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 2)
            pygame.draw.rect(screen, (255, 255, 255), player.rect.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 1, border_radius=10)
            if enemy:
                pygame.draw.rect(screen, (255, 255, 255), enemy.rect.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 1, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 0), player.hurtbox.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 1, border_radius=5)
            if enemy:
                pygame.draw.rect(screen, (255, 255, 0), enemy.hurtbox.move(game_state['screen_offset'][0], game_state['screen_offset'][1]), 1, border_radius=5)

        pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
        
        font = pygame.font.SysFont(None, 36)
        p_hp_text = font.render(f"Player HP: {int(player.hp)}  |  Stage: {current_stage}", True, BLACK)
        screen.blit(p_hp_text, (20, 20))
        if debug_mode:
            debug_text = font.render("DEBUG MODE: ON (Press D to Toggle)", True, (255, 0, 0))
            screen.blit(debug_text, (20, 60))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
```

player.py
```
import pygame
from settings import *
from entities import Entity, draw_guard_shield

class Player(Entity):
    def __init__(self):
        anim_data = {"Attack1": 4, "Attack2": 4, "Death": 7, "Fall": 2, "Idle": 4, "Jump": 2, "Run": 8, "Take Hit": 3}
        hit_data = {"Attack1": 3, "Attack2": 3}
        # super().__init__ 마지막 인자로 hurtbox_size (80, 85)를 추가
        super().__init__(100, SCREEN_HEIGHT-160, "A1", anim_data, hit_data, (200, 128), (80, 85))
        self.is_jumping = False
        self.is_guarding = False
        self.attack_type = None
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.ghosts = []

    # [중요] main.py에서 호출하는 단발성 입력 처리 함수
    def handle_single_input(self, event):
        if self.recovery_timer > 0: return

        if event.type == pygame.KEYDOWN:
            # 대시 (L_SHIFT)
            if event.key == pygame.K_LSHIFT and self.dash_cooldown <= 0 and not self.is_jumping:
                self.dash_timer = DASH_DURATION
                self.dash_cooldown = DASH_COOLDOWN
                self.vel_x = self.direction * DASH_SPEED
                self.current_anim_speed = LIGHT_ANIM_SPEED // 2 

            # 점프 (SPACE)
            if event.key == pygame.K_SPACE and not self.is_jumping:
                self.vel_y = JUMP_FORCE
                self.is_jumping = True

            # 공격 (Z, X)
            if self.attack_timer == 0:
                if event.key == pygame.K_z:
                    self.start_attack("LIGHT", "Attack1", 10)
                elif event.key == pygame.K_x:
                    self.start_attack("HEAVY", "Attack2", 20)

    # [중요] main.py에서 호출하는 지속성 입력 처리 함수 (에러 발생 지점!)
    def handle_continuous_input(self):
        if self.recovery_timer > 0: return
            
        keys = pygame.key.get_pressed()
        
        # 가드 처리
        self.is_guarding = keys[pygame.K_s] and self.attack_timer == 0 and not self.is_jumping
        
        if self.dash_timer > 0:
            # 대시 중 방향 전환
            if keys[pygame.K_LEFT]: self.direction = -1
            elif keys[pygame.K_RIGHT]: self.direction = 1
            self.vel_x = self.direction * DASH_SPEED
        else:
            # 일반 이동
            self.vel_x = 0
            if not self.is_guarding:
                if keys[pygame.K_LEFT]: 
                    self.vel_x = -WALK_SPEED
                    self.direction = -1
                elif keys[pygame.K_RIGHT]: 
                    self.vel_x = WALK_SPEED
                    self.direction = 1

    def start_attack(self, type_name, anim_name, damage):
        self.attack_type = type_name
        self.attack_timer = self.anim_handler.get_total_frames(anim_name) * 6
        if type_name == "LIGHT":
            self.recovery_timer = LIGHT_ATTACK_RECOVERY
            self.current_anim_speed = LIGHT_ANIM_SPEED
        else:
            self.recovery_timer = HEAVY_ATTACK_RECOVERY
            self.current_anim_speed = HEAVY_ANIM_SPEED
            
        self.vel_x = self.direction * 12
        self.has_hit = False
        self.anim_handler.reset()

    def apply_physics(self):
        super().apply_physics() 
        if self.rect.bottom >= SCREEN_HEIGHT - 50:
            self.is_jumping = False

    def update(self):
        # 대시 및 잔상 로직
        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.dash_timer == 0:
                self.current_anim_speed = LIGHT_ANIM_SPEED
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.dash_timer > 0:
            state = self.get_current_state()
            frame = self.anim_handler.get_frame(state, self.direction, self.current_anim_speed).copy()
            frame.set_alpha(100) 
            self.ghosts.append([frame, self.rect.copy(), 100])
        
        for ghost in self.ghosts[:]:
            ghost[2] -= 10
            ghost[1].x += self.vel_x * 0.5
            if ghost[2] <= 0:
                self.ghosts.remove(ghost)

        # 공격 및 상태 타이머 로직
        if self.attack_timer > 0: 
            self.attack_timer -= 1
        else:
            self.has_hit = False 
            
        if self.attack_timer == 0 and self.recovery_timer > 0: 
            self.recovery_timer -= 1
        if self.attack_timer == 0: 
            self.attack_type = None
            self.has_hit = False 
        if self.hit_timer > 0: 
            self.hit_timer -= 1

    def get_current_state(self):
        if self.hit_timer > 0: return "Take Hit"
        if self.attack_timer > 0: return "Attack1" if self.attack_type == "LIGHT" else "Attack2"
        if self.is_jumping: return "Jump" if self.vel_y < 0 else "Fall"
        if abs(self.vel_x) > 0.5: return "Run"
        return "Idle"

    def draw(self, screen, screen_offset):
        # 잔상 그리기
        for ghost in self.ghosts:
            img, rect, alpha = ghost
            img.set_alpha(alpha)
            f_rect = img.get_rect(midbottom=(rect.centerx + screen_offset[0], rect.bottom + screen_offset[1]))
            screen.blit(img, f_rect)

        # 본체 그리기
        state = self.get_current_state()
        frame = self.anim_handler.get_frame(state, self.direction, self.current_anim_speed)
        f_rect = frame.get_rect(midbottom=(self.rect.centerx + screen_offset[0], self.rect.bottom + screen_offset[1]))
        screen.blit(frame, f_rect)
        
        if self.is_guarding:
            offset_rect = self.rect.move(screen_offset[0], screen_offset[1])
            draw_guard_shield(screen, offset_rect, self.direction)
```

settings.py
```
# settings.py
import pygame

# 화면 설정
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (34, 139, 34)
PLAYER_COLOR = (50, 150, 255)
ENEMY_COLOR = (255, 80, 80)
GROUND_COLOR = (0, 191, 255, 128)
ATTACK_COLOR = (255, 0, 0)
GUARD_COLOR = (0, 191, 255)
RECOVERY_COLOR = (150, 150, 150)

# 디버그 설정
DEBUG_MODE = False  # 기본적으로는 끔


# 애니메이션 속도 (기본 100ms, 높을수록 느림)
LIGHT_ANIM_SPEED = 100
HEAVY_ANIM_SPEED = 160  # 강공격은 더 느리게

# 판정 크기
PHYSICS_WIDTH = 40  # 물리 캡슐 너비 (좁게 설정하여 '미끄러짐' 구현)
HURTBOX_WIDTH = 80  # 피격 판정 너비 (실제 몸통)
HURTBOX_HEIGHT = 110

# 공격 범위 설정 (Hitbox 크기)
ATTACK_RANGE_W = 160 # 가로 범위를 더 넓게
ATTACK_RANGE_H = 80  # 세로 범위를 더 넓게
ATTACK_OFFSET_X = 30 # 캐릭터 몸쪽으로 겹치는 정도

# 물리 상수
GRAVITY = 0.6          # 상승 시 적용될 기본 중력
FALL_GRAVITY = 1.2     # 하강 시 적용될 더 강한 중력 (빠르게 떨어짐)
JUMP_FORCE = -16       # 점프 힘을 다시 키워 시원하게 상승
WALK_SPEED = 5
ENEMY_SPEED_BASE = 3
KNOCKBACK_FORCE = 12

# 후딜레이 설정 (프레임 단위)
LIGHT_ATTACK_RECOVERY = 12  # 짧은 후딜
HEAVY_ATTACK_RECOVERY = 35  # 긴 후딜 (눈에 띄게)

DASH_SPEED = 15        # 대시 속도 (걷기보다 훨씬 빠르게)
DASH_DURATION = 12     # 대시 지속 시간 (프레임 단위)
DASH_COOLDOWN = 30     # 대시 재사용 대기시간

SPARK_COLOR = (255, 255, 200)
```

entites.py
```
# entities.py
import pygame
import random
from settings import *
from animation import AnimationHandler
import math

def draw_guard_shield(screen, rect, direction):
    """
    상상력을 더한 다이내믹 에너지 보호막
    """
    time_val = pygame.time.get_ticks() * 0.005 
    pulse = math.sin(time_val) * 8

    shield_width, shield_height = rect.width + 200, rect.height + 200
    shield_surf = pygame.Surface((shield_width, shield_height), pygame.SRCALPHA)
    
    center_x, center_y = shield_width // 2, shield_height // 2
    
    if direction == 1:
        start_angle = -math.pi / 2
        end_angle = math.pi / 2
    else:
        start_angle = math.pi / 2
        end_angle = 3 * math.pi / 2

    # 외곽 오라
    outer_radius = 110 + pulse 
    pygame.draw.arc(shield_surf, (100, 200, 255, 60), 
                    (center_x - outer_radius, center_y - outer_radius, outer_radius * 2, outer_radius * 2), 
                    start_angle, end_angle, 20)

    # 내부 핵심막
    inner_radius = 90 + (pulse * 0.5)
    pygame.draw.arc(shield_surf, (0, 120, 255, 150), 
                    (center_x - inner_radius, center_y - inner_radius, inner_radius * 2, inner_radius * 2), 
                    start_angle, end_angle, 12)
    
    # 포인트 빛
    point_radius = 75 + pulse
    pygame.draw.arc(shield_surf, (200, 255, 255, 180), 
                    (center_x - point_radius, center_y - point_radius, point_radius * 2, point_radius * 2), 
                    start_angle, end_angle, 5)

    screen.blit(shield_surf, (rect.x - 100, rect.y - 100))


class Entity:
    def __init__(self, x, y, prefix, anim_data, hit_data, frame_size, hurtbox_size):
        # 물리용 Rect (캡슐: 좁고 길게)
        self.rect = pygame.Rect(x, y, PHYSICS_WIDTH, hurtbox_size[1]) 
        # 피격용 Hurtbox (몸통: 넓게)
        self.hurtbox = pygame.Rect(x - (HURTBOX_WIDTH - PHYSICS_WIDTH)//2, y, HURTBOX_WIDTH, hurtbox_size[1])
        
        self.direction = 1
        self.hp = 100
        self.vel_x = 0
        self.vel_y = 0
        self.attack_timer = 0
        self.recovery_timer = 0
        self.hit_timer = 0
        self.has_hit = False
        self.is_guarding = False
        self.current_anim_speed = LIGHT_ANIM_SPEED 
        self.anim_handler = AnimationHandler(prefix, anim_data, hit_data, frame_size)

    def apply_physics(self):
        # 가변 중력 적용
        self.vel_y += GRAVITY if self.vel_y < 0 else FALL_GRAVITY
        self.rect.y += self.vel_y
        
        if self.rect.bottom >= SCREEN_HEIGHT - 50:
            self.rect.bottom = SCREEN_HEIGHT - 50
            self.vel_y = 0

        friction = 0.85 if self.recovery_timer <= 0 else 0.5
        self.vel_x *= friction
        self.rect.x += self.vel_x
        
        # 물리 rect와 피격 hurtbox 동기화
        self.hurtbox.y = self.rect.y
        self.hurtbox.centerx = self.rect.centerx

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

    def take_damage(self, damage, attacker_dir, game_state):
        final_damage = damage * 0.5 if self.is_guarding else damage
        self.hp -= final_damage
        self.hit_timer = 15
        self.vel_x = attacker_dir * KNOCKBACK_FORCE
        game_state['hit_stop_timer'] = 6 if not self.is_guarding else 3
        game_state['screen_shake_timer'] = 10 if final_damage > 15 else 5
        self.anim_handler.reset()

    def get_attack_rect(self, attack_type, damage):
        if self.attack_timer <= 0: return None, 0
        state = self.get_current_state()
        curr_frame, _ = self.anim_handler.get_current_frame_info(state)
        hit_start = self.anim_handler.get_hit_frame(state)
        if curr_frame < hit_start: return None, 0
        
        # [강공격 대공 판정] attack_type이 "HEAVY"일 때만 높게 설정
        if attack_type == "HEAVY":
            attack_w, attack_h = 130, 150 
            attack_y = self.rect.bottom - 140 
        else:
            attack_w, attack_h = 110, 60
            attack_y = self.rect.bottom - int(self.rect.height * 0.6)
        
        attack_offset_x = 20
        if self.direction == 1: 
            rect = pygame.Rect(self.rect.right - attack_offset_x, attack_y, attack_w, attack_h)
        else: 
            rect = pygame.Rect(self.rect.left - attack_w + attack_offset_x, attack_y, attack_w, attack_h)
            
        return rect, damage

class Enemy(Entity):
    def __init__(self, x, y, prefix, anim_data, hit_data, frame_size, hurtbox_size, speed):
        super().__init__(x, y, prefix, anim_data, hit_data, frame_size, hurtbox_size)
        self.speed = speed
        self.state = "IDLE"
        self.state_timer = 0
        self.attack_startup = 0
        self.current_attack_anim = "Attack1"
        self.attack_type = "LIGHT" # 현재 공격의 타입 저장
        self.heavy_attacks = []    # 강공격으로 설정할 애니메이션 리스트
        self.is_moving = False

    def update(self, player):
        # 1. 공격 판정 타이머 관리
        if self.attack_timer > 0:
            self.attack_timer -= 1
        
        # 2. 상태 결정 타이머 관리
        if self.state_timer > 0:
            self.state_timer -= 1
        else:
            self.decide_action(player)

        dist = player.rect.centerx - self.rect.centerx
        abs_dist = abs(dist)

        # 가드 상태 처리
        if self.state == "GUARD":
            self.is_guarding = True
            self.is_moving = False
            self.vel_x = 0
        else:
            self.is_guarding = False

        # 행동 로직
        if self.state == "CHASE":
            self.direction = 1 if dist > 0 else -1
            self.rect.x += self.direction * self.speed
            self.is_moving = True
            if abs_dist < 80:
                self.state = "ATTACK"
                self.state_timer = 0

        elif self.state == "RETREAT":
            self.direction = -1 if dist > 0 else 1
            self.rect.x += self.direction * (self.speed * 0.7)
            self.is_moving = True
            if abs_dist > 200:
                self.state = "CHASE"

        elif self.state == "JUMP_ATTACK":
            if self.vel_y == 0: self.vel_y = JUMP_FORCE
            self.direction = 1 if dist > 0 else -1
            self.rect.x += self.direction * (self.speed * 1.2)
            self.is_moving = True
            if self.rect.bottom >= SCREEN_HEIGHT - 50: 
                self.state = "ATTACK"
                self.state_timer = 0

        elif self.state == "ATTACK":
            self.is_moving = False
            if self.attack_startup > 0:
                self.attack_startup -= 1
            elif self.attack_timer == 0:
                # [수정] 애니메이션 속도 및 강공격 여부 결정
                anim_name = self.current_attack_anim
                if anim_name in self.heavy_attacks:
                    self.attack_type = "HEAVY"
                    self.current_anim_speed = HEAVY_ANIM_SPEED
                else:
                    self.attack_type = "LIGHT"
                    self.current_anim_speed = LIGHT_ANIM_SPEED
                
                self.attack_timer = self.anim_handler.get_total_frames(anim_name) * 6
                self.attack_startup = -1 
                self.has_hit = False 
        
        # 공격 종료 후 상태 전환
        if self.state == "ATTACK" and self.attack_timer == 0 and self.attack_startup < 0:
            self.state = "IDLE"
            self.has_hit = False

        elif self.state == "IDLE":
            self.is_moving = False

    def decide_action(self, player):
        dist = player.rect.centerx - self.rect.centerx
        abs_dist = abs(dist)
        rand = random.random()
        ideal_dist = ATTACK_RANGE_W * 0.8 

        if abs_dist > 350:
            self.state = "CHASE"; self.state_timer = 60
        elif abs_dist < ideal_dist - 40:
            if rand < 0.6:
                self.state = "RETREAT"; self.state_timer = 30
            else:
                self.state = "ATTACK"
                self.current_attack_anim = random.choice(list(self.anim_handler.hit_frame_data.keys()))
                self.attack_startup = 10
                self.state_timer = self.anim_handler.get_total_frames(self.current_attack_anim) * 6
        elif abs_dist < ideal_dist + 40:
            if rand < 0.7:
                self.state = "ATTACK"
                self.current_attack_anim = random.choice(list(self.anim_handler.hit_frame_data.keys()))
                self.attack_startup = 10
                self.state_timer = self.anim_handler.get_total_frames(self.current_attack_anim) * 6
            else:
                self.state = "IDLE"; self.state_timer = 20
        else:
            if rand < 0.5: self.state = "CHASE"; self.state_timer = 40
            elif rand < 0.8: self.state = "JUMP_ATTACK"; self.state_timer = 60
            else: self.state = "IDLE"; self.state_timer = 30

    def get_current_state(self):
        if self.hit_timer > 0: return "Take Hit"
        if self.state == "ATTACK": return self.current_attack_anim
        if self.state == "JUMP_ATTACK": return "Jump"
        if self.is_moving: return "Run"
        return "Idle"

    def get_attack_rect(self):
        if self.state != "ATTACK" or self.attack_startup > 0: 
            return None, 0
        # 결정된 attack_type("LIGHT" or "HEAVY")을 부모 클래스에 전달
        return super().get_attack_rect(self.attack_type, 10)

    def draw(self, screen, screen_offset):
        state = self.get_current_state()
        frame = self.anim_handler.get_frame(state, self.direction, self.current_anim_speed)
        f_rect = frame.get_rect(midbottom=(self.rect.centerx + screen_offset[0], self.rect.bottom + screen_offset[1]))
        screen.blit(frame, f_rect)

        if self.is_guarding:
            offset_rect = self.rect.move(screen_offset[0], screen_offset[1])
            draw_guard_shield(screen, offset_rect, self.direction)

        pygame.draw.rect(screen, BLACK, (self.rect.centerx-25+screen_offset[0], self.rect.top-20+screen_offset[1], 50, 10))
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.centerx-25+screen_offset[0], self.rect.top-20+screen_offset[1], 50*(self.hp/100), 10))
        if self.hit_timer > 0: self.hit_timer -= 1

# --- [적 세부 클래스: 강공격 리스트 지정] ---

class EnemyB(Enemy):
    def __init__(self, x, y):
        anim_data = {"Attack1": 16, "Death": 8, "Idle": 9, "Run": 9, "Take Hit": 3}
        hit_data = {"Attack1": 12}
        super().__init__(x, y, "B1", anim_data, hit_data, (90, 58), (80, 85), ENEMY_SPEED_BASE)
        self.heavy_attacks = [] # B는 모든 공격이 약공격

class EnemyA2(Enemy):
    def __init__(self, x, y):
        anim_data = {"Attack1": 6, "Attack2": 6, "Death": 6, "Fall": 2, "Idle": 8, "Jump": 2, "Run": 8, "Take Hit": 4}
        hit_data = {"Attack1": 5, "Attack2": 5}
        super().__init__(x, y, "A2", anim_data, hit_data, (200, 122), (100, 110), ENEMY_SPEED_BASE + 2)
        # [요청] A2의 Attack1을 강공격으로 설정
        self.heavy_attacks = ["Attack1"]

class EnemyC1(Enemy):
    def __init__(self, x, y):
        anim_data = {"Attack1": 7, "Attack2": 7, "Attack3": 8, "Death": 7, "Fall": 3, "Idle": 10, "Jump": 3, "Run": 8, "Take Hit": 3}
        hit_data = {"Attack1": 5, "Attack2": 3, "Attack3": 5}
        super().__init__(x, y, "C1", anim_data, hit_data, (162, 101), (90, 100), ENEMY_SPEED_BASE - 1)
        # [요청] C1의 Attack3을 강공격으로 설정
        self.heavy_attacks = ["Attack3"]

class Boss(Enemy):
    def __init__(self, x, y):
        self.modes = {
            "A2": {"prefix": "A2", "anim": {"Attack1": 6, "Attack2": 6, "Death": 6, "Fall": 2, "Idle": 8, "Jump": 2, "Run": 8, "Take Hit": 4}, "hit": {"Attack1": 5, "Attack2": 5}, "size": (200, 122), "hurtbox": (100, 110), "speed": 6, "heavy": ["Attack1"]},
            "C1": {"prefix": "C1", "anim": {"Attack1": 7, "Attack2": 7, "Attack3": 8, "Death": 7, "Fall": 3, "Idle": 10, "Jump": 3, "Run": 8, "Take Hit": 3}, "hit": {"Attack1": 5, "Attack2": 3, "Attack3": 5}, "size": (162, 101), "hurtbox": (90, 100), "speed": 2, "heavy": ["Attack3"]}
        }
        self.current_mode = "A2"
        m = self.modes[self.current_mode]
        super().__init__(x, y, m["prefix"], m["anim"], m["hit"], m["size"], m["hurtbox"], m["speed"])
        self.heavy_attacks = m["heavy"]
        self.mode_timer = 180 

    def update(self, player):
        self.mode_timer -= 1
        if self.mode_timer <= 0:
            self.current_mode = "C1" if self.current_mode == "A2" else "A2"
            m = self.modes[self.current_mode]
            self.anim_handler = AnimationHandler(m["prefix"], m["anim"], m["hit"], m["size"])
            self.speed = m["speed"]
            self.heavy_attacks = m["heavy"] # 모드 전환 시 강공격 리스트 업데이트
            self.mode_timer = 180
        super().update(player)
```

animation.py
```
# animation.py
import pygame
from settings import *

class AnimationHandler:
    def __init__(self, prefix, animation_data, hit_frame_data, frame_size):
        self.animations = {}
        self.hit_frame_data = hit_frame_data 
        self.frame_size = frame_size
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_duration = 100 

        for anim_name, frame_count in animation_data.items():
            file_name = f"{prefix}_{anim_name}.png"
            try:
                sheet = pygame.image.load(f"assets/{file_name}").convert_alpha()
                frames = []
                for i in range(frame_count):
                    rect = pygame.Rect(i * frame_size[0], 0, frame_size[0], frame_size[1])
                    frame = sheet.subsurface(rect)
                    scale_factor = 2.0 
                    frame = pygame.transform.scale(frame, (int(frame_size[0] * scale_factor), int(frame_size[1] * scale_factor)))
                    frames.append(frame)
                self.animations[anim_name] = frames
            except Exception as e:
                print(f"Error loading {file_name}: {e}")
                self.animations[anim_name] = [pygame.Surface((frame_size[0]*2, frame_size[1]*2))]

    def get_current_frame_info(self, anim_name):
        if anim_name not in self.animations: return 0, 1
        return self.current_frame, len(self.animations[anim_name])
    
    def get_hit_frame(self, anim_name):
        return self.hit_frame_data.get(anim_name, 999) - 1

    def get_frame(self, anim_name, direction, speed_override=None):
        if anim_name not in self.animations: anim_name = "Idle"
        frames = self.animations[anim_name]
        
        if self.current_frame >= len(frames): self.current_frame = 0
        
        # [수정] speed_override가 있으면 해당 속도를 사용, 없으면 기본값 사용
        current_duration = speed_override if speed_override else self.frame_duration
        
        self.animation_timer += 16 
        if self.animation_timer >= current_duration:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(frames)
            
        frame = frames[self.current_frame]
        if direction == -1: frame = pygame.transform.flip(frame, True, False)
        return frame

    def get_total_frames(self, anim_name):
        return len(self.animations[anim_name]) if anim_name in self.animations else 1

    def reset(self):
        self.current_frame = 0
        self.animation_timer = 0
```