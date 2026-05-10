import pygame
import sys
import os
import random

# --- 설정 및 상수 ---
FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCALE_FACTOR = 4 
TOP_CROP = 20 

GRAVITY = 0.8
WALK_SPEED = 6
BACK_WALK_SPEED = 3    # 🌟 [추가] 후진 속도 (더 느리게)
JUMP_FORCE = -16
GROUND_Y = 650

DASH_SPEED = 16
DASH_DURATION = 12
DASH_COOLDOWN = 30
DOUBLE_TAP_TIME = 250
BUFFER_WINDOW = 12 

WALL_MARGIN = -400

# 🌟 [추가] 전투 상수
HIT_STOP_DURATION = 5  # 히트스탑 지속 프레임 (타격감)
PLAYER_MAX_HP = 100
ENEMY_MAX_HP = 50

HITBOX_CONFIG = {
    "LIGHT": {
        "offset": 0, 
        "w": 80, 
        "h": 30, 
        "y_off": 0, # 🌟 [수정] 바닥에서 60픽셀 위로 (가슴 높이)
        "start": 3, 
        "end": 6
    },
    "HEAVY": {
        "offset": 35, 
        "w": 50, 
        "h": 120, 
        "y_off": 0, # 🌟 [수정] 바닥에서 40픽셀 위로 (박스가 크므로 낮게 설정)
        "start": 6, 
        "end": 12
    }
}

CHAR_DATA = {
    "A1": {
        "IDLE": ("Idle", 4), "RUN": ("Run", 8),
        "ATK1": ("Attack1", 4), "ATK2": ("Attack2", 4),
        "JUMP": ("Jump", 2), "FALL": ("Fall", 2),
        "HIT": ("Take Hit", 3), "DEATH": ("Death", 7),
    },
    "B1": { # 적 캐릭터 B1 데이터
        "IDLE": ("Idle", 9), "RUN": ("Run", 9),
        "ATK1": ("Attack1", 16), # B1은 약공격만 있음
        "HIT": ("Take Hit", 3), "DEATH": ("Death", 8),
    },
}

LIGHT_ATK_TOTAL_FRAMES = 14
HEAVY_ATK_TOTAL_FRAMES = 22

def load_sprite_sheet(filename, frame_count):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
        sheet_width, sheet_height = sheet.get_size()
        frame_width = sheet_width // frame_count
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
            frame = sheet.subsurface(rect)
            if TOP_CROP > 0:
                crop_rect = pygame.Rect(0, TOP_CROP, frame_width, sheet_height - TOP_CROP)
                frame = frame.subsurface(crop_rect)
            new_size = (frame.get_width() * SCALE_FACTOR, frame.get_height() * SCALE_FACTOR)
            frame = pygame.transform.scale(frame, new_size)
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {filename} | 에러: {e}")
        dummy = pygame.Surface((100 * SCALE_FACTOR, 100 * SCALE_FACTOR))
        dummy.fill((255, 0, 0))
        return [dummy] * frame_count

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, char_id, hp):
        super().__init__()
        self.char_id = char_id
        self.state = "IDLE"
        self.timer = 0
        self.frame_index = 0
        self.facing_right = True
        self.vel_x = 0
        self.vel_y = 0
        self.is_grounded = True
        self.hit_gauge = 0       # 현재 충전된 히트 횟수 (0~3)
        self.dash_charges = 1    # 현재 사용 가능한 대쉬 횟수 (초기값 1)
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.input_buffer = None
        self.buffer_timer = 0
        self.guard_effect_timer = 0 # 가드 이펙트 지속 시간
        

        
        # 🌟 [추가] 체력 설정
        self.hp = hp
        self.max_hp = hp
        
        self.animations = {}
        data = CHAR_DATA.get(char_id, CHAR_DATA["A1"])
        for state, (suffix, count) in data.items():
            path = os.path.join("assets", f"{self.char_id}_{suffix}.png")
            self.animations[state] = load_sprite_sheet(path, count)

        self.image = self.animations["IDLE"][0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.is_attacking = False
        self.has_hit = False # 🌟 [추가] 이번 공격에 이미 히트했는지 여부

    def take_damage(self, amount, attacker):
        if self.state == "DEATH": 
            return False
        
        # 🌟 가드 판정: 뒤쪽 키를 누르고 있는가?
        is_guarding = False
        if self.char_id == "A1":
            keys = pygame.key.get_pressed()
            if (self.facing_right and keys[pygame.K_a]) or (not self.facing_right and keys[pygame.K_d]):
                is_guarding = True
        
        if is_guarding:
            final_damage = amount * 0.5
            knockback_power = 3 
            self.guard_effect_timer = 10 # 🌟 가드 이펙트 10프레임 동안 발생
            print("🛡️ 가드 성공!")
        else:
            final_damage = amount
            knockback_power = 10
            print("💥 정타!")

        self.hp -= final_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.state = "DEATH"
            self.is_attacking = False
            self.vel_x = 0
        else:
            self.state = "HIT"
            self.timer = 0
            self.is_attacking = False
            # 🌟 가드 여부에 관계없이 피격 상태(HIT)가 되면 
            # 아주 짧은 시간 동안은 update에서 vel_x가 0이 되거나 넉백이 적용됨
            self.vel_x = -knockback_power if self.facing_right else knockback_power
            
        return True

    def add_to_buffer(self, action):
        self.input_buffer = action
        self.buffer_timer = BUFFER_WINDOW

    def execute_buffer(self):
        if self.input_buffer:
            action = self.input_buffer
            self.input_buffer = None
            self.buffer_timer = 0
            if action == "LIGHT" and self.is_grounded: self.handle_attack("LIGHT")
            elif action == "HEAVY" and self.is_grounded: self.handle_attack("HEAVY")
            elif action == "JUMP" and self.is_grounded: self.vel_y = JUMP_FORCE

    def trigger_dash(self, is_forward):
        # 🌟 [수정] 대쉬 구분 로직
        if self.dash_cooldown_timer <= 0:
            # 1. 공격 중 대쉬 (캔슬 대쉬) -> 게이지 소모
            if self.is_attacking:
                if self.dash_charges > 0:
                    print("✨ 대쉬 캔슬!")
                    self.dash_charges -= 1
                else:
                    print("❌ 게이지 부족!")
                    return False
            
            self.state = "DASH"
            self.is_attacking = False
            self.timer = 0
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            
            # 🌟 [백대쉬 로직] 전진이면 바라보는 방향으로, 후진이면 반대 방향으로 속도 설정
            if is_forward:
                self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            else:
                self.vel_x = -DASH_SPEED if self.facing_right else DASH_SPEED
            
            return True
        return False

    def handle_attack(self, attack_type):
        if self.state in ["IDLE", "RUN"]:
            if attack_type == "LIGHT":
                self.state = "ATK1"
                self.timer = 0
                self.is_attacking = True
                self.has_hit = False # 🌟 [추가] 공격 시작 시 히트 플래그 초기화
            elif attack_type == "HEAVY":
                self.state = "ATK2"
                self.timer = 0
                self.is_attacking = True
                self.has_hit = False # 🌟 [추가] 강공격 시에도 히트 플래그 초기화 필수!

    def apply_physics(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

        self.rect.x += self.vel_x

        # 🌟 [수정] 이미지 여백을 고려한 벽 충돌 처리
        # 왼쪽 벽: 0이 아니라 WALL_MARGIN에서 멈춤
        if self.rect.left < WALL_MARGIN:
            self.rect.left = WALL_MARGIN
            self.vel_x = 0
        # 오른쪽 벽: SCREEN_WIDTH가 아니라 SCREEN_WIDTH - WALL_MARGIN에서 멈춤
        elif self.rect.right > SCREEN_WIDTH - WALL_MARGIN:
            self.rect.right = SCREEN_WIDTH - WALL_MARGIN
            self.vel_x = 0

    def update(self):
        self.apply_physics()
        if self.buffer_timer > 0: self.buffer_timer -= 1
        else: self.input_buffer = None
        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= 1

        if hasattr(self, 'guard_effect_timer') and self.guard_effect_timer > 0:
            self.guard_effect_timer -= 1


        if self.state == "DASH":
            self.dash_timer -= 1
            frames = self.animations["RUN"]
            self.frame_index = (pygame.time.get_ticks() // 50) % len(frames)
            self.image = frames[self.frame_index]
            if self.dash_timer <= 0:
                self.state = "IDLE"
                self.vel_x = 0
                self.execute_buffer()

        elif self.is_attacking:
            # 공격 유형 결정 (ATK1 -> LIGHT, ATK2 -> HEAVY)
            atk_type = "LIGHT" if self.state == "ATK1" else "HEAVY"
            total_frames = LIGHT_ATK_TOTAL_FRAMES if atk_type == "LIGHT" else HEAVY_ATK_TOTAL_FRAMES
            cfg = HITBOX_CONFIG[atk_type]
            
            self.timer += 1
            frames = self.animations[self.state]
            self.frame_index = int((self.timer / total_frames) * len(frames))
            if self.frame_index >= len(frames): self.frame_index = len(frames) - 1
            self.image = frames[self.frame_index]

            # 🌟 [통일된 히트박스 계산]
            if cfg["start"] <= self.timer <= cfg["end"]:
                offset = cfg["offset"] * SCALE_FACTOR 
                w = cfg["w"] * SCALE_FACTOR
                h = cfg["h"] * SCALE_FACTOR
    
    # 🌟 [핵심 수정] 상단 기준(rect.y) -> 하단 기준(rect.bottom)으로 변경
    # 바닥 좌표에서 (y_off * SCALE)만큼 뺀 뒤, 박스 높이(h)만큼 더 빼줘야 
    # 박스의 하단이 아닌 상단 좌표가 정확히 잡힙니다.
                hy = self.rect.bottom - (cfg["y_off"] * SCALE_FACTOR) - h
                
                # 2. X축 계산: 중심점(centerx) 기준 (이미지 너비가 달라도 동일한 사거리 생성)
                if self.facing_right:
                    hx = self.rect.centerx + offset
                else:
                    hx = self.rect.centerx - offset - w
                
                self.hitbox = pygame.Rect(hx, hy, w, h)
            else:
                self.hitbox = pygame.Rect(0, 0, 0, 0)

            if self.timer >= total_frames:
                self.state, self.timer, self.is_attacking = "IDLE", 0, False
                self.execute_buffer()
        
        else: 
            if not self.is_grounded:
                self.state = "JUMP" if self.vel_y < 0 else "FALL"
            elif abs(self.vel_x) > 0.1:
                self.state = "RUN"
            else:
                self.state = "IDLE"
            frames = self.animations.get(self.state, self.animations["IDLE"])
            if self.state == "RUN": self.frame_index = (pygame.time.get_ticks() // 100) % len(frames)
            elif self.state == "IDLE": self.frame_index = (pygame.time.get_ticks() // 200) % len(frames)
            else: self.frame_index = 0
            self.image = frames[self.frame_index]
            self.hitbox = pygame.Rect(0, 0, 0, 0)

        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

class Enemy(Entity):
    def __init__(self, x, y, char_id, hp):
        super().__init__(x, y, char_id, hp)
        self.ai_timer = 0
        self.ai_state = "APPROACH" # APPROACH, ATTACK, WAIT

    def update_ai(self, target):
        # 사망했거나 피격 중일 때는 AI 로직을 완전히 중단하여 애니메이션이 씹히지 않게 함
        if self.state == "DEATH" or self.state == "HIT": 
            return

        # 플레이어와의 거리 계산
        dist = target.rect.centerx - self.rect.centerx
        
        # 1. 방향 설정 (덜덜거림 방지)
        if abs(dist) > 20: 
            self.facing_right = dist > 0

        # 🌟 [핵심] 공격 중일 때는 AI가 상태(IDLE/RUN)를 강제로 바꾸지 못하게 함
        if self.is_attacking:
            self.vel_x = 0 # 공격 중에는 정지
            return 

        # 2. AI 상태 머신
        if self.ai_state == "APPROACH":
            # 사거리 밖이면 접근
            if abs(dist) > 200: 
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.state = "RUN" # 공격 중이 아닐 때만 RUN 설정
            else:
                # 사거리 진입 -> 공격 상태로 전환
                self.ai_state = "ATTACK"
                self.ai_timer = 0
        
        elif self.ai_state == "ATTACK":
            # 공격 실행 (Entity의 handle_attack 호출)
            self.vel_x = 0
            self.handle_attack("LIGHT")
            
            # 공격을 시작했으므로 즉시 WAIT 상태로 전환하여 
            # 다음 프레임에 다시 handle_attack이 호출되는 것을 방지
            self.ai_state = "WAIT"
            self.ai_timer = 45 # 공격 후 대기 시간 (약 0.75초)
        
        elif self.ai_state == "WAIT":
            self.vel_x = 0
            self.state = "IDLE" # 대기 중에는 IDLE 애니메이션
            self.ai_timer -= 1
            if self.ai_timer <= 0:
                self.ai_state = "APPROACH"

    def update(self):
        # Entity의 기본 update(물리, 애니메이션 처리)를 호출
        super().update()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand")
    clock = pygame.time.Clock()
    
    player = Entity(200, GROUND_Y, "A1", PLAYER_MAX_HP)
    enemy = Enemy(1000, GROUND_Y, "B1", ENEMY_MAX_HP)
    
    all_sprites = pygame.sprite.Group(player, enemy)
    hitstop_timer = 0

    last_key_pressed = None
    last_key_time = 0

    running = True
    while running:
        if hitstop_timer > 0:
            hitstop_timer -= 1
            # 히트스탑 중에는 업데이트를 건너뛰어 화면을 멈춤
        else:
            keys = pygame.key.get_pressed()
            if player.state != "DASH" and player.state != "HIT": 
                if not player.is_attacking:
                    if keys[pygame.K_a]:
                        player.vel_x = -BACK_WALK_SPEED if player.facing_right else -WALK_SPEED
                    elif keys[pygame.K_d]:
                        player.vel_x = WALK_SPEED if not player.facing_right else WALK_SPEED # (이 부분은 단순화해서 작성
                    else:
                        player.vel_x = 0
                else:
                    player.vel_x = 0
            else:
            # 대쉬 중일 때는 대쉬 속도가 적용되고, 
            # HIT 상태(가드 포함)일 때는 속도를 0으로 만들어 멈추게 함
                if player.state != "DASH":
                    player.vel_x = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    current_time = pygame.time.get_ticks()
                    if event.key in [pygame.K_a, pygame.K_d]:
                        if event.key == last_key_pressed and (current_time - last_key_time) < DOUBLE_TAP_TIME:
                            is_forward = False
                            if (event.key == pygame.K_d and player.facing_right) or \
                                (event.key == pygame.K_a and not player.facing_right):
                                is_forward = True
                        
                            player.trigger_dash(is_forward)
                        last_key_pressed, last_key_time = event.key, current_time
                    if event.key == pygame.K_w and player.is_grounded: player.vel_y = JUMP_FORCE
                    if event.key == pygame.K_i:
                        if player.is_grounded and player.state not in ["DASH"]: player.handle_attack("LIGHT")
                        else: player.add_to_buffer("LIGHT")
                    if event.key == pygame.K_o:
                        if player.is_grounded and player.state not in ["DASH"]: player.handle_attack("HEAVY")
                        else: player.add_to_buffer("HEAVY")
            
            player.facing_right = (enemy.rect.centerx > player.rect.centerx)
            # 적 또한 항상 플레이어를 바라봅니다.
            enemy.facing_right = (player.rect.centerx > enemy.rect.centerx)

            enemy.update_ai(player)
            all_sprites.update()

            # 🌟 [충돌 판정 로직]
            # 1. 플레이어 -> 적 공격
            if player.hitbox.colliderect(enemy.rect):
                if not player.has_hit: 
                    if enemy.take_damage(10, player):
            # 🌟 [추가] 공격 성공 시 히트 게이지 상승
                        player.hit_gauge += 1
                        if player.hit_gauge >= 3:
                            player.hit_gauge = 0
                            player.dash_charges += 1 # 3번 때리면 대쉬 1회 충전
            
                        hitstop_timer = HIT_STOP_DURATION
                        player.has_hit = True

            # 2. 적 -> 플레이어 공격
            if enemy.hitbox.colliderect(player.rect):
                if not enemy.has_hit:
                    if player.take_damage(15, enemy):
                        hitstop_timer = HIT_STOP_DURATION
                        enemy.has_hit = True # 🌟 히트 완료 표시!
                    enemy.hitbox = pygame.Rect(0, 0, 0, 0)

        # 그리기
        screen.fill((50, 50, 50))
        pygame.draw.line(screen, (100, 100, 100), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)
        
        # 🌟 [UI: HP 바]
        pygame.draw.rect(screen, (255, 0, 0), (50, 50, 300, 20))
        pygame.draw.rect(screen, (0, 255, 0), (50, 50, 3 * player.hp, 20))
        pygame.draw.rect(screen, (255, 0, 0), (930, 50, 300, 20))
        pygame.draw.rect(screen, (0, 255, 0), (930, 50, 6 * enemy.hp, 20))

        all_sprites.draw(screen)
        for entity in all_sprites:
            if hasattr(entity, 'guard_effect_timer') and entity.guard_effect_timer > 0:
                effect_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
                color = (150, 220, 255, 180) 
                cx, cy = 100, 100
                pygame.draw.circle(effect_surf, color, (cx, cy), 60, 5) 
                pygame.draw.circle(effect_surf, (150, 220, 255, 80), (cx, cy), 55) 
                
                if entity.facing_right:
                    pos = (entity.rect.centerx + 20, entity.rect.centery - 50)
                else:
                    effect_surf = pygame.transform.flip(effect_surf, True, False)
                    pos = (entity.rect.centerx - 120, entity.rect.centery - 50)
                
                screen.blit(effect_surf, pos)

        if player.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), player.hitbox, 2)
        if enemy.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), enemy.hitbox, 2)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()