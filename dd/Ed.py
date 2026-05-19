import pygame
import sys
import os
import random
import math  # 🌟 이 줄을 반드시 추가해야 합니다!

# --- 설정 및 상수 ---
FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCALE_FACTOR = 4 
TOP_CROP = 20 

GRAVITY = 0.8
WALK_SPEED = 8
BACK_WALK_SPEED = 3    # 🌟 [추가] 후진 속도 (더 느리게)
JUMP_FORCE = -20
GROUND_Y = 550

DASH_SPEED = 20
BACK_DASH_SPEED = 10
DASH_DURATION = 12
DASH_COOLDOWN = 30
DOUBLE_TAP_TIME = 250
BUFFER_WINDOW = 30

WALL_MARGIN = 0
CAMERA_X = 0
VIRTUAL_WALL_DIST = SCREEN_WIDTH * 0.8  # 캐릭터 간 최대 거리 (화면 너비의 80%)


STAGE_SEQUENCE = [
    {"id": "B1", "hp": 100,  "name": "SCOUT B1"},
    {"id": "A2", "hp": 100, "name": "KNIGHT A2"},
    {"id": "C1", "hp": 100,  "name": "ASSASSIN C1"},
    {"id": "A2", "hp": 100, "name": "THE MASKED MASTER", "boss": True} # 보스는 A2로 시작하여 C1과 번갈아 변신
]

# 🌟 [추가] 전투 상수
HIT_STOP_LIGHT = 4  # 약공격: 빠르고 경쾌하게
HIT_STOP_HEAVY = 12 # 강공격: 묵직하고 강력하게
PLAYER_MAX_HP = 100
ENEMY_MAX_HP = 50
DASH_CANCEL_STUN_BONUS = 60  # 🌟 대쉬 캔슬 시 추가 경직 (약 1초)

KNOCKBACK_HIT = 12    # 일반 피격 넉백
KNOCKBACK_GUARD = 10  # 가드 피격 넉백

COMBO_SCALING = {
    1: 1.0, 2: 1.0, 
    3: 0.9, 4: 0.9, 
    5: 0.7, 6: 0.5, 7: 0.4 
}
MIN_SCALING = 0.4


HITBOX_CONFIG = {
    "LIGHT": { 
        "offset": 0, "w": 80, "h": 30, "y_off": 0, 
        "start": 7, # 🌟 3 -> 7 (선딜 대폭 증가: 이제 바로 안 나감)
        "end": 10   # 🌟 6 -> 10
    },
    "HEAVY": { 
        "offset": 35, "w": 50, "h": 120, "y_off": 0, 
        "start": 12, # 🌟 6 -> 12 (묵직한 선딜레이)
        "end": 17    # 🌟 12 -> 17
    },
    "REVERSE": { 
        "offset": 0, "w": 80, "h": 30, "y_off": 0, 
        "start": 7, 
        "end": 10 
    }
}

CHAR_DATA = {
     "A1": { # 플레이어
        "IDLE": ("Idle", 4, None), "RUN": ("Run", 8, None),
        "ATK1": ("Attack1", 4, 3), "ATK2": ("Attack2", 4, 3),
        "JUMP": ("Jump", 2, None), "FALL": ("Fall", 2, None),
        "HIT": ("Take Hit", 3, None), "DEATH": ("Death", 7, None),
    },
    "B1": { # 1스테이지: 정찰병
        "IDLE": ("Idle", 9, None), "RUN": ("Run", 9, None),
        "ATK1": ("Attack1", 16, 12), "HIT": ("Take Hit", 3, None), "DEATH": ("Death", 8, None),
    },
    "A2": { # 2스테이지: 중갑 전사 (6장 중 5번이 히트)
        "IDLE": ("Idle", 8, None), "RUN": ("Run", 8, None),
        "ATK1": ("Attack1", 6, 5), "ATK2": ("Attack2", 6, 5),
        "JUMP": ("Jump", 2, None), "FALL": ("Fall", 2, None),
        "HIT": ("Take Hit", 4, None), "DEATH": ("Death", 6, None),
    },
    "C1": { # 3스테이지: 암살자 (7장 중 5번/3번이 히트)
        "IDLE": ("Idle", 10, None), "RUN": ("Run", 8, None),
        "ATK1": ("Attack1", 7, 5),  # 약공격용
        "ATK2": ("Attack2", 7, 3),  # (사용 안 함 혹은 특수기로 활용 가능)
        "ATK3": ("Attack3", 8, 5),  # 🌟 강공격용 (Attack3 사용)
        "JUMP": ("Jump", 3, None), "FALL": ("Fall", 3, None),
        "HIT": ("Take Hit", 3, None), "DEATH": ("Death", 7, None),
    }
}

AI_BRAIN_CONFIG = {
    "B1": { 
        "guard_prob": 0.2, "back_catch_prob": 0.7, 
        "jump_in_prob": 0.05, # 1단계는 그냥 뚜벅뚜벅 걸어옴
        "dash_back_prob": 0.1, "aggressive_dash": 0.3
    },
    "A2": { 
        "guard_prob": 0.7, "back_catch_prob": 0.7,
        "jump_in_prob": 0.1,  # 중갑병은 무게감 있게 땅에서 걸어옴
        "dash_back_prob": 0.2, "aggressive_dash": 0.5
    },
    "C1": { 
        "guard_prob": 0.3, "back_catch_prob": 0.7,
        "jump_in_prob": 0.4,  # 암살자는 공중 접근을 자주 함
        "dash_back_prob": 0.6, "aggressive_dash": 0.8
    },
    "BOSS": { 
        "guard_prob": 0.8, "back_catch_prob": 0.7,
        "jump_in_prob": 0.2, 
        "dash_back_prob": 0.5, "aggressive_dash": 0.9
    }
}


class DeathExplosion:
    def __init__(self, x, y):
        self.shards = []
        # 1. 사각형 파편들 생성
        for _ in range(60):
            self.shards.append({
                "pos": [x, y],
                "vel": [random.uniform(-15, 15), random.uniform(-15, 15)], # 사방으로 비산
                "size": [random.randint(4, 12), random.randint(2, 4)], # 길쭉한 파편 형태
                "color": random.choice([(255, 255, 255), (100, 0, 255), (50, 0, 100)]), # 보라/흰색 (보스 감성)
                "life": random.randint(30, 60),
                "angle": random.uniform(0, 360)
            })
        self.flash_alpha = 255 # 처음에 화면이 번쩍하게 함

    def update(self):
        for s in self.shards:
            # 공기 저항으로 점점 느려지게 함
            s["pos"][0] += s["vel"][0]
            s["pos"][1] += s["vel"][1]
            s["vel"][0] *= 0.94
            s["vel"][1] *= 0.94
            s["life"] -= 1
            
        # 🌟 이 줄의 s.shards를 self.shards로 수정합니다!
        self.shards = [s for s in self.shards if s["life"] > 0]

        if self.flash_alpha > 0:
            self.flash_alpha -= 15 # 번쩍임은 빠르게 사라짐

    def draw(self, surface, camera_x):
        # 2. 화면 전체 번쩍임 (임팩트)
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(self.flash_alpha)
            surface.blit(flash_surf, (0, 0))

        # 3. 도트 파편 그리기
        for s in self.shards:
            shard_surf = pygame.Surface((s["size"][0], s["size"][1]))
            shard_surf.fill(s["color"])
            # 회전 연출 (선택사항, 성능을 위해 생략 가능)
            # rotated_shard = pygame.transform.rotate(shard_surf, s["angle"])
            surface.blit(shard_surf, (s["pos"][0] - camera_x, s["pos"][1]))

class PixelGuard:
    def __init__(self):
        self.pixel_scale = SCALE_FACTOR # 전역 SCALE_FACTOR 사용
        self.width = 32
        self.height = 64
        self.particles = []

    def draw(self, surface, cx, cy, facing,  y_offset=100):
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
                if random.random() < 0.5:
                    small_surf.set_at((x, y), (255, 255, 255, 255))

        if random.random() < 0.4:
            self.particles.append([random.randint(10, 25), self.height, random.uniform(1, 3)])
        for p in self.particles[:]:
            p[1] -= p[2]
            if p[1] < 0: self.particles.remove(p)
            else: small_surf.set_at((int(p[0]), int(p[1])), (0, 200, 255, 255))

        scaled_w = self.width * self.pixel_scale
        scaled_h = self.height * self.pixel_scale
        scaled_surf = pygame.transform.scale(small_surf, (scaled_w, scaled_h))

        if facing == -1:
            scaled_surf = pygame.transform.flip(scaled_surf, True, False)
            offset_x = -70 - (scaled_w // 2)
        else:
            offset_x = 70 - (scaled_w // 2)
            
        surface.blit(scaled_surf, (cx + offset_x, cy - (scaled_h // 2) + y_offset))

class ComboDisplay:
    def __init__(self):
        self.font = pygame.font.SysFont("impact", 60, bold=True) # 임팩트 있는 폰트
        self.timer = 0
        self.active = False
        self.combo_count = 0

    def trigger(self, count):
        self.combo_count = count
        self.timer = 20  # 애니메이션 지속 프레임
        self.active = True

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        else:
            self.active = False

    def draw(self, surface, player_rect):
        if not self.active or self.combo_count <= 1: # 2타부터 콤보 표시
            return

        # 🌟 팝 애니메이션 계산: 타이머가 줄어들면서 크기가 커졌다가 작아짐
        # 0~20프레임 동안 scale이 1.0 -> 1.5 -> 1.0으로 변함
        scale = 1.0 + (math.sin((self.timer / 20) * 3.14) * 0.5)
        
        text_surf = self.font.render(f"{self.combo_count} HIT!", True, (255, 200, 0)) # 금색
        
        # 그림자 효과 추가
        shadow_surf = self.font.render(f"{self.combo_count} HIT!", True, (0, 0, 0))
        
        # 크기 조절
        w, h = text_surf.get_size()
        scaled_w, scaled_h = int(w * scale), int(h * scale)
        
        text_surf = pygame.transform.scale(text_surf, (scaled_w, scaled_h))
        shadow_surf = pygame.transform.scale(shadow_surf, (scaled_w, scaled_h))

        # 플레이어 머리 위쪽 약간 오른쪽에 배치
        pos_x = player_rect.centerx + 60
        pos_y = player_rect.bottom - 300 - (scaled_h // 2)

        surface.blit(shadow_surf, (pos_x + 4, pos_y + 4)) # 그림자 먼저
        surface.blit(text_surf, (pos_x, pos_y))

LIGHT_ATK_TOTAL_FRAMES = 18
HEAVY_ATK_TOTAL_FRAMES = 26

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
    def __init__(self, x, y, char_id, hp, is_boss=False):
        super().__init__()
        self.char_id = char_id
        self.is_boss = is_boss # 🌟 무조건 맨 위에 추가해야 에러가 안 납니다!
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
        self.guard_effect = PixelGuard() # 🌟 [추가] 이 줄을 추가하세요
        self.recovery_timer = 0  # 🌟 [추가] 후딜레이 타이머
        self.ghosts = []
        self.is_cancel_dash = False
        self.god_mode = False  # 🌟 [추가] 무적 모드 기본값은 꺼짐
        self.is_guarding = False # 🌟 [추가] 가드 상태 변수

        # 🌟 [추가] 체력 설정
        self.hp = hp
        self.max_hp = hp
        
        self.animations = {}
        data = CHAR_DATA.get(char_id, CHAR_DATA["A1"])
        for state, (suffix, count, hit_idx) in data.items(): 
            path = os.path.join("dd\\assets", f"{self.char_id}_{suffix}.png")
            frames = load_sprite_sheet(path, count)
            
            # 🌟 [이미지 스왑 핵심] 보스일 경우 이미지를 붉은색으로 물들임!
            if self.is_boss:
                tinted_frames = []
                for frame in frames:
                    new_frame = frame.copy()
                    # 원본 이미지에 (빨강 100%, 초록 30%, 파랑 30%) 필터를 덮어씌움 -> 검붉은 핏빛 기사 완성
                    new_frame.fill((255, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    tinted_frames.append(new_frame)
                self.animations[state] = tinted_frames
            else:
                self.animations[state] = frames

        self.image = self.animations["IDLE"][0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.is_attacking = False
        self.has_hit = False # 🌟 [추가] 이번 공격에 이미 히트했는지 여부
        self.combo_step = 0
        self.combo_timer = 0 # 🌟 프레임 단위 콤보 유지시간 타이머 (60 = 1초)
        self.cancel_ui_timer = 0 # 🌟 [추가] 캔슬 대쉬 UI 표시 타이머
        self.is_blocking = False # 🌟 [추가] 방금 맞은 공격을 가드했는가?
        self.used_cancel_in_combo = False # 🌟 [추가] 이번 콤보에서 캔슬 대쉬를 썼는가? (무한 대쉬 방지)

        if char_id == "A1":
            self.hurtbox_w, self.hurtbox_h = 60, 100 # 플레이어는 세로로 긴 형태
        elif char_id == "B1":
            self.hurtbox_w, self.hurtbox_h = 70, 40  # 적(B1)은 낮고 뭉툭한 형태
        else:
            self.hurtbox_w, self.hurtbox_h = 60, 80
            
        self.hurtbox = pygame.Rect(0, 0, 0, 0) # 실제 좌표가 담길 박스

    def take_damage(self, amount, attacker, attack_type): # attack_type 인자 추가
        if self.state == "DEATH": return False

        self.combo_step = 0
        self.combo_timer = 0
        self.used_cancel_in_combo = False

        amount *= 0.5

        is_guarding = self.is_guarding 

        if self.is_boss:
            # 강공격이 아니면 상태가 HIT으로 변하지 않고 체력만 깎임 (슈퍼 아머)
            if attack_type == "LIGHT":
                self.hp -= amount * 0.3 # 데미지도 훨씬 적게 받음
                return True # 경직 없이 리턴
            else:
                amount *= 0.7 # 강공격도 어느 정도 경감

        if attack_type == "LIGHT":
            base_stun = 7 if is_guarding else 12
            base_recovery = 12 if is_guarding else 10
        else: 
            base_stun = 10 if is_guarding else 20
            base_recovery = 20 if is_guarding else 5

        combo_count = attacker.combo_step if hasattr(attacker, 'combo_step') else 1
        scale = COMBO_SCALING.get(combo_count, MIN_SCALING) 
        current_scale = scale if not is_guarding else 1.0
        
        final_damage = amount * current_scale
        final_stun = base_stun * current_scale 

        if is_guarding:
            final_damage *= 0.5 
            base_knockback = KNOCKBACK_GUARD 
            self.guard_effect_timer = 10
            self.is_blocking = True # 🌟 [가드 성공 기록]
        else:
            base_knockback = KNOCKBACK_HIT
            self.is_blocking = False # 🌟 [클린 히트 기록]

        final_knockback = base_knockback

        if not self.god_mode:
            self.hp -= final_damage
        else:
            print(f"✨ {self.char_id} is INVINCIBLE!") 
    
        self.hit_stun_timer = final_stun 
        self.state = "HIT"
        self.timer = 0 # 🌟 [추가] 피격 애니메이션이 첫 프레임부터 시작하도록 초기화
        self.is_attacking = False
        attacker.recovery_frames = base_recovery

        self.hit_stun_timer = final_stun 
        self.state = "HIT"
        attacker.recovery_frames = base_recovery 
    
        if self.hp <= 0:
            self.hp = 0
            # 🌟 [버그 수정] 사망 진입 시 타이머 초기화
            if self.state != "DEATH":
                self.state = "DEATH"
                self.timer = 0
        else:
            self.vel_x = -final_knockback if self.facing_right else final_knockback
        
        return True

    def add_to_buffer(self, action):
        self.input_buffer = action
        self.buffer_timer = BUFFER_WINDOW

    def execute_buffer(self):
        if self.input_buffer:
            action = self.input_buffer
            self.input_buffer = None
            self.buffer_timer = 0
            # 🌟 [수정] 대쉬(DASH) 중에도 선입력된 공격이 나갈 수 있도록 "DASH" 추가
            if self.state in ["IDLE", "RUN", "DASH"]:
                if action == "LIGHT" and self.is_grounded: self.handle_attack("LIGHT")
                elif action == "HEAVY" and self.is_grounded: self.handle_attack("HEAVY")
                # 🌟 [추가] 선입력 버퍼에 REVERSE 추가
                elif action == "REVERSE" and self.is_grounded: self.handle_attack("REVERSE")
                elif action == "JUMP" and self.is_grounded: self.vel_y = JUMP_FORCE

    def trigger_dash(self, is_forward):
        # 🌟 [수정] 대쉬 구분 로직
        if self.dash_cooldown_timer <= 0:
            if self.is_attacking:
                if self.dash_charges > 0:
                    print("✨ 콤보 캔슬 대쉬! 콤보 유지시간 확장!")
                    self.dash_charges -= 1
                    self.is_cancel_dash = True 
                    self.combo_timer = 120
                    self.cancel_ui_timer = 30 
                    self.used_cancel_in_combo = True # 🌟 [추가] 이번 콤보에선 게이지 획득 불가!
                else:
                    return False

            else:
                self.is_cancel_dash = False # 🌟 그냥 대쉬로 설정
            
            self.hitbox = pygame.Rect(0, 0, 0, 0) 

            self.state = "DASH"
            self.is_attacking = False
            self.hit_gauge = 0 
            self.timer = 0
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            
            # 🌟 [백대쉬 로직] 전진이면 바라보는 방향으로, 후진이면 반대 방향으로 속도 설정
            current_dash_speed = DASH_SPEED if is_forward else BACK_DASH_SPEED
            if is_forward:
                self.vel_x = current_dash_speed if self.facing_right else -current_dash_speed
            else:
                self.vel_x = -current_dash_speed if self.facing_right else current_dash_speed
            
            return True
        return False

    def handle_attack(self, attack_type):
        if not self.is_grounded: return False

        if self.is_attacking: return False 


        # 🌟 [추가] 캐릭터별 공격 애니메이션 매핑 분기
        target_state = "ATK1" # 기본값
        
        if self.char_id == "A2":
            target_state = "ATK2" if attack_type == "LIGHT" else "ATK1"
        elif self.char_id == "C1":
            # 🌟 [수정] REVERSE 공격이 들어오면 ATK2(양방향 타격) 발동
            if attack_type == "REVERSE":
                target_state = "ATK2"
            else:
                target_state = "ATK1" if attack_type == "LIGHT" else "ATK3"
        else: # A1, B1 등 기본형
            target_state = "ATK1" if attack_type == "LIGHT" else "ATK2"

        # 해당 애니메이션이 실제로 존재하는지 체크 (예외 방지)
        if target_state in self.animations:
            self.state = target_state
        else:
            self.state = "ATK1" # 없으면 기본 공격형으로 후퇴

        # 🌟 [중요] 현재 공격이 '약'인지 '강'인지 별도로 저장 (애니메이션 이름과 무관하게 프레임 데이터 적용)
        self.current_atk_type = attack_type 
        
        self.timer = 0
        self.is_attacking = True
        self.has_hit = False
        self.recovery_timer = 0
        self.hitbox = pygame.Rect(0, 0, 0, 0)

        if self.state == "DASH":
            self.dash_timer = 0

        return True

    def register_hit(self):
        """타격 성공 시 콤보 스텝을 올리고 시간을 갱신"""
        if self.combo_timer > 0 or self.combo_step == 0: 
            self.combo_step += 1 
        else:
            self.combo_step = 1 
            self.used_cancel_in_combo = False 
        
        # 🌟 타격 성공 시 콤보 유지시간을 35프레임(약 0.6초)으로 설정!
        self.combo_timer = 60
        return self.combo_step

    def apply_physics(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
    
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

    # 🌟 [수정] 상태에 따른 마찰력 차등 적용
        if self.state == "DASH":
            friction = 1.0 # 대쉬 중엔 속도 유지
        elif self.state == "HIT":
            friction = 0.98 # 🌟 피격 중엔 마찰력을 줄여 더 멀리 밀려나게 함
        else:
            friction = 0.92 # 일반 이동 시엔 빠르게 멈춤

        self.vel_x *= friction
        if abs(self.vel_x) < 0.1: self.vel_x = 0

        self.rect.x += self.vel_x

        # 벽 충돌 처리
        

        

    def update(self):
        self.apply_physics()
        
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_step = 0 # 시간이 다 지나면 콤보 초기화
                self.used_cancel_in_combo = False

        # 🌟 [선입력(버퍼) 자동 캔슬 시스템]
        if self.buffer_timer > 0:
            self.buffer_timer -= 1
        else:
            self.input_buffer = None
            
        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= 1


        if hasattr(self, 'guard_effect_timer') and self.guard_effect_timer > 0:
                self.guard_effect_timer -= 1

    # 🌟 [추가] 피격 경직 타이머 처리
        if hasattr(self, 'hit_stun_timer') and self.hit_stun_timer > 0:
            self.hit_stun_timer -= 1
            if self.hit_stun_timer <= 0 and self.state == "HIT":
                self.state = "IDLE" # 경직이 끝나면 IDLE로 복귀


        if self.state == "DASH":
            self.dash_timer -= 1
            frames = self.animations["RUN"]
            self.frame_index = (pygame.time.get_ticks() // 50) % len(frames)
            self.image = frames[self.frame_index]
            if self.dash_timer <= 0:
                self.state = "IDLE" # 확실하게 상태를 돌려줌
                self.vel_x = 0
                self.is_cancel_dash = False # 캔슬 플래그 초기화
                self.execute_buffer()

        elif self.is_attacking:
            # 🌟 [수정] 애니메이션 이름이 아니라, 실제 발동한 공격 타입(약/강)을 기준으로 프레임 결정
            atk_type = getattr(self, 'current_atk_type', "LIGHT")
            
            total_frames = LIGHT_ATK_TOTAL_FRAMES if atk_type == "LIGHT" else HEAVY_ATK_TOTAL_FRAMES
            cfg = HITBOX_CONFIG[atk_type]
            
            self.timer += 1
            frames = self.animations[self.state]
            self.frame_index = int((self.timer / total_frames) * len(frames))
            if self.frame_index >= len(frames): self.frame_index = len(frames) - 1
            self.image = frames[self.frame_index]

            # 🌟 [자동 계산 판정 시스템] 🌟
            state_info = CHAR_DATA[self.char_id].get(self.state)
            if state_info:
                # state_info = ("Attack1", 4, 3) -> (이름, 장수, 히트이미지번호)
                sprite_count = state_info[1]
                hit_sprite_idx = state_info[2]

                if hit_sprite_idx is not None:
                    # 1. 이미지 한 장당 할당된 프레임 길이 계산
                    frame_duration = total_frames / sprite_count
                    # 2. 해당 이미지 번호의 시작 프레임과 종료 프레임 자동 계산
                    start_f = hit_sprite_idx * frame_duration
                    end_f = (hit_sprite_idx + 1) * frame_duration

                    # 3. 현재 타이머가 그 계산된 구간 안에 있는지 확인
                    if start_f <= self.timer <= end_f:
                        offset = cfg["offset"] * SCALE_FACTOR 
                        w = cfg["w"] * SCALE_FACTOR
                        h = cfg["h"] * SCALE_FACTOR
                        hy = self.rect.bottom - (cfg["y_off"] * SCALE_FACTOR) - h
                        
                        # 🌟 [추가] REVERSE 타입일 경우 양방향으로 뻗어나가는 커다란 판정 생성
                        if atk_type == "REVERSE":
                            # 내 몸 중심을 기준으로 좌우로 w만큼 펼침
                            hx = self.rect.centerx - w
                            hitbox_w = w * 2
                            self.hitbox = pygame.Rect(hx, hy, hitbox_w, h)
                        else:
                            if self.facing_right: hx = self.rect.centerx + offset
                            else: hx = self.rect.centerx - offset - w
                            self.hitbox = pygame.Rect(hx, hy, w, h)
                    else:
                        self.hitbox = pygame.Rect(0, 0, 0, 0)
                else:
                    self.hitbox = pygame.Rect(0, 0, 0, 0)

            if self.timer >= total_frames:
                # 기본 후딜레이 설정
                base_rec = 15 if atk_type == "LIGHT" else 20 # 🌟 기본 후딜 상향
                
                # 콤보 누적 패널티 (체감 가능하게 유지)
                if self.combo_step <= 2:
                    fatigue_penalty = 0 
                else:
                    fatigue_penalty = (self.combo_step - 2) * (5 if atk_type == "LIGHT" else 8)
                
                if not self.has_hit:
                    # 🌟 [핵심] 헛쳤을 때의 패널티를 극대화하여 '연타 스팸' 방지
                    self.combo_step = 0 
                    self.combo_timer = 0 # 🌟 헛치면 콤보 시간도 즉시 증발 (얄짤없음)
                    whiff_penalty = 35 if atk_type == "LIGHT" else 50
                    self.recovery_timer = base_rec + whiff_penalty 
                    
                    # 시각적 피드백: 헛쳤을 때 캐릭터를 살짝 검게 만들어 무방비 상태임을 표시 (선택 사항)
                    print(f"⚠️ {self.char_id} WHIFF!!! TOTAL RECOVERY: {self.recovery_timer}f")
                else:
                    # 히트 성공 시: 기본 후딜 + 콤보 패널티
                    base_val = getattr(self, 'recovery_frames', base_rec)
                    self.recovery_timer = base_val + fatigue_penalty
                    if hasattr(self, 'recovery_frames'): del self.recovery_frames

                if self.recovery_timer > 0:
                    self.state = "RECOVERY"
                else:
                    self.state = "IDLE"
                
                self.timer = 0
                self.is_attacking = False
                self.execute_buffer()

        elif self.state == "HIT":
        # 🌟 피격 애니메이션 처리
            frames = self.animations.get("HIT", self.animations["IDLE"])
            self.timer += 1
            
            # 🌟 [핵심 변경] % 대신 min()을 사용하여 마지막 프레임에 도달하면 고정시킵니다.
            # 애니메이션 속도를 조절하고 싶다면 5를 다른 숫자로 바꾸세요.
            self.frame_index = min(len(frames) - 1, self.timer // 5)
            
            self.image = frames[self.frame_index]
            self.hitbox = pygame.Rect(0, 0, 0, 0)


        elif self.state == "RECOVERY":
            self.recovery_timer -= 1
            # 후딜레이 중에는 IDLE의 첫 프레임(굳은 모습) 출력
            frames = self.animations["IDLE"]
            self.image = frames[0]
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            if self.recovery_timer <= 0:
                self.state = "IDLE"
                self.execute_buffer()
        elif self.state == "DEATH":
            frames = self.animations.get("DEATH", self.animations["IDLE"])
            # 🌟 [버그 수정] 전역 시간이 아닌 고유 타이머로 프레임 계산 및 마지막 프레임 고정
            self.timer += 1
            self.frame_index = self.timer // 10 # 애니메이션 재생 속도
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1 # 마지막 프레임에서 멈춤
            self.image = frames[self.frame_index]
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            self.vel_x = 0 # 사망 시 정지
            
            
        
        else: 
            if not self.is_grounded:
                # 🌟 [수정] 점프/낙하 애니메이션이 있는 캐릭터만 해당 상태 사용
                if self.vel_y < 0 and "JUMP" in self.animations:
                    self.state = "JUMP"
                elif self.vel_y >= 0 and "FALL" in self.animations:
                    self.state = "FALL"
                else:
                    # B1처럼 점프 애니메이션이 없으면 IDLE의 0번 프레임으로 대체
                    self.state = "IDLE" 
            elif abs(self.vel_x) > 0.1:
                self.state = "RUN"
            else:
                self.state = "IDLE"

            frames = self.animations.get(self.state, self.animations["IDLE"])
            # 공중 상태인데 애니메이션이 없는 경우(B1 등) 강제로 IDLE 첫 프레임 고정
            if not self.is_grounded and self.state == "IDLE":
                self.frame_index = 0
            elif self.state == "RUN": 
                self.frame_index = (pygame.time.get_ticks() // 100) % len(frames)
            elif self.state == "IDLE": 
                self.frame_index = (pygame.time.get_ticks() // 200) % len(frames)
            # 점프/낙하 애니메이션 재생 (마지막 프레임 고정)
            elif self.state in ["JUMP", "FALL"]:
                self.frame_index = min(len(frames) - 1, int(abs(self.vel_y) // 5))
            else:
                self.frame_index = 0
                
            self.image = frames[self.frame_index]


        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        
        self.hurtbox = pygame.Rect(
            self.rect.centerx - self.hurtbox_w // 2, 
            self.rect.bottom - self.hurtbox_h, 
            self.hurtbox_w, 
            self.hurtbox_h
        )

        is_active = (self.state == "DASH" or self.state == "HIT" or self.is_attacking)
        if is_active or (self.is_boss and self.state != "DEATH"):
            tick = 3 if self.is_boss else 6 # 보스는 더 자주 잔상 생성
            if pygame.time.get_ticks() % tick == 0:
                ghost_img = self.image.copy()
                if self.is_boss:
                # 보스는 검붉은색 오라
                    ghost_img.fill((200, 30, 30, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    self.ghosts.append([ghost_img, self.rect.copy(), 150]) # 더 오래 남음
                else:
                # 일반 캐릭터는 푸른색 잔상
                    ghost_img.fill((150, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT) 
                    self.ghosts.append([ghost_img, self.rect.copy(), 100])


        for g in self.ghosts[:]:
            g[2] -= 25
            if g[2] <= 0:
                self.ghosts.remove(g)

class Enemy(Entity):
    def __init__(self, x, y, char_id, hp, is_boss=False): # 🌟 인자 추가
        super().__init__(x, y, char_id, hp, is_boss)
        self.ai_timer = 0
        self.ai_state = "IDLE"
        self.decision_timer = 0
        self.is_boss = is_boss # 🌟 보스 여부 저장

        self.transform_timer = 0
        self.is_transforming = False
        self.pre_transform_timer = 0
    
    def change_form(self, new_id):
        # 1. 변신하기 전의 현재 발밑 좌표(midbottom)를 기억해둡니다.
        old_bottom_pos = self.rect.midbottom 

        self.char_id = new_id
        self.animations = {}
        data = CHAR_DATA.get(new_id, CHAR_DATA["A1"])
        
        # 새로운 애니메이션 로드 및 보스(붉은색) 필터 적용
        for state, (suffix, count, hit_idx) in data.items(): 
            path = os.path.join("dd\\assets", f"{self.char_id}_{suffix}.png")
            frames = load_sprite_sheet(path, count)
            tinted_frames = []
            for frame in frames:
                new_frame = frame.copy()
                new_frame.fill((255, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
                tinted_frames.append(new_frame)
            self.animations[state] = tinted_frames

        self.state = "IDLE"
        self.image = self.animations["IDLE"][0]
        
        # 🌟 2. 새로운 이미지의 크기에 맞춰 rect를 새로 생성하고, 아까 기억해둔 발밑 좌표에 붙입니다!
        self.rect = self.image.get_rect(midbottom=old_bottom_pos)
        
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        
        # 허트박스 크기 업데이트
        if new_id == "C1":
            self.hurtbox_w, self.hurtbox_h = 60, 80
        elif new_id == "A2":
            self.hurtbox_w, self.hurtbox_h = 60, 80


    def update_ai(self, target):
    # 후딜레이(RECOVERY) 상태일 때도 AI가 아무 행동(점프, 이동, 가드)을 못 하게 막음
        if self.state == "DEATH": return 
        
        if self.is_boss:
            if not self.is_transforming:
                self.transform_timer += 1
                if self.transform_timer >= 480: # 60fps * 8초 = 480프레임
                    self.is_transforming = True
                    self.pre_transform_timer = 60 # 1초간 사전 이펙트 대기
                    self.state = "IDLE"
                    self.vel_x = 0 # 이동 정지
                    return # 변신 준비 중엔 AI 정지

            if self.is_transforming:
                self.pre_transform_timer -= 1
                self.vel_x = 0
                
                if self.state == "HIT":
                    self.state = "IDLE" 

                # 1초 대기가 끝나면 쾅! 하고 변신
                if self.pre_transform_timer <= 0:
                    new_form = "C1" if self.char_id == "A2" else "A2"
                    self.change_form(new_form)
                    self.is_transforming = False
                    self.transform_timer = 0
                    
                    # 변신 시 튕겨내기 (충격파 효과)
                    dist = target.rect.centerx - self.rect.centerx
                    target.vel_x = 15 if dist > 0 else -15
                    target.hit_stun_timer = 10
                    target.state = "HIT"
                    
                return # 변신 중에는 아래의 공격/이동 AI를 실행하지 않음
        if self.state in ["HIT", "RECOVERY"]:
            return # <--- 이제 타이머는 위에서 이미 계산됐으므로 안심하고 리턴 가능
    
        is_boss = getattr(self, 'is_boss', False)
        cfg_id = "BOSS" if is_boss else self.char_id
        cfg = AI_BRAIN_CONFIG.get(cfg_id, AI_BRAIN_CONFIG["B1"]) 

        if not self.is_grounded:
            return

        dist = target.rect.centerx - self.rect.centerx
        abs_dist = abs(dist)
        self.facing_right = dist > 0

        # 🌟 철벽 가드 시스템 (관성 유지)
        if self.is_guarding:
            if not target.is_attacking:
                self.is_guarding = False 
            else:
                return # 🌟 강제로 멈추지 않고(vel_x=0 삭제) 마찰력에 맡김

        # AI 상태 및 사거리 계산
        is_target_vulnerable = (target.state == "RECOVERY")
        is_target_whiffing = (target.is_attacking and not target.has_hit)
        
        can_heavy = "ATK2" in self.animations
        if self.char_id == "C1":
            rand = random.random()
            if rand < 0.4: planned_atk = "LIGHT"
            elif rand < 0.7: planned_atk = "REVERSE"
            else: planned_atk = "HEAVY"
        else:
            planned_atk = "LIGHT" if (not can_heavy or random.random() < 0.7) else "HEAVY"
            
        atk_cfg = HITBOX_CONFIG[planned_atk] 
        attack_reach = (atk_cfg["offset"] + atk_cfg["w"]) * SCALE_FACTOR + (target.hurtbox_w // 2)
        self.debug_reach = attack_reach 

        if self.is_attacking:
            # 콤보 캔슬 압박
            if self.has_hit and self.dash_charges > 0 and random.random() < 0.7: 
                state_info = CHAR_DATA[self.char_id].get(self.state)
                if state_info and state_info[2] is not None:
                    hit_end_f = (state_info[2] + 1) * (18/state_info[1]) 
                    if self.timer > hit_end_f:
                        self.trigger_dash(is_forward=True)
                        self.decision_timer = 0 
            return # 🌟 공격 중에도 vel_x=0으로 멈추지 않고 타격 관성 유지

        if self.state == "DASH":
            return

        # ====================================================================
        # 🛡️ [우선순위 1] 방어 및 회피 (상대가 공격 중일 때)
        # ====================================================================
        if target.is_attacking and abs_dist < attack_reach * 1.5:
            if self.decision_timer <= 0:
                # 🌟 뒤잡기 점프: 게이지 검사(dash_charges > 0) 삭제! 
                if target.state == "ATK1" and random.random() < cfg["back_catch_prob"]: 
                    self.vel_y = JUMP_FORCE 
                    self.state = "DASH" 
                    self.dash_timer = 20 
                    self.vel_x = (DASH_SPEED * 1.3) if self.facing_right else (-DASH_SPEED * 1.3)
                    self.decision_timer = 30 
                    print("🤖 AI: 완벽한 뒤잡기 점프!")
                    return
                
                if random.random() < cfg["guard_prob"]: 
                    self.is_guarding = True 
                    self.decision_timer = 10
                    return
                
                # 🌟 백대쉬 회피: 게이지 검사 삭제!
                if random.random() < cfg["dash_back_prob"]: 
                    self.trigger_dash(is_forward=False)
                    self.decision_timer = 15
                    return
                
                self.decision_timer = 10 
            return 

        # ====================================================================
        # ⚔️ [우선순위 2] 딜캐 (상대가 헛치거나 후딜레이 중일 때)
        # ====================================================================
        if is_target_vulnerable or is_target_whiffing:
            if abs_dist <= attack_reach:
                self.handle_attack(planned_atk)
                self.decision_timer = 5
                return
            elif abs_dist <= attack_reach * 2.5:
                self.trigger_dash(is_forward=True)
                self.decision_timer = 0
                return

        # ====================================================================
        # 🚶 [우선순위 3] 뉴트럴 상태에서의 거리 조절
        # ====================================================================
        if self.decision_timer > 0:
            self.decision_timer -= 1
            if self.state not in ["IDLE", "DASH", "HIT", "RECOVERY"] and self.is_grounded:
                 self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
            return

        if abs_dist > attack_reach * 2.5: 
            if random.random() < cfg["aggressive_dash"]: 
                self.trigger_dash(is_forward=True)
                self.decision_timer = 15
            else:
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.decision_timer = 10

        elif abs_dist > attack_reach: 
            if random.random() < cfg["jump_in_prob"] and self.is_grounded: 
                self.vel_y = JUMP_FORCE
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.decision_timer = 20
            else:
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.decision_timer = 5 

        else: 
            self.handle_attack(planned_atk)
            self.decision_timer = 20

    def update(self):
        super().update()

def main():
    global CAMERA_X 

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand")
    clock = pygame.time.Clock()
    
    font_small = pygame.font.SysFont("arial", 20, bold=True)
    font_large = pygame.font.SysFont("arial", 40, bold=True)
    font_huge = pygame.font.SysFont("impact", 120, italic=True) # 🌟 [추가] 카운트다운용 거대 폰트

    current_stage_idx = 0
    stage_info = STAGE_SEQUENCE[current_stage_idx]
    countdown_timer = 240

    active_explosions = []
    death_delay_timer = 0 # 보스 사망 후 화면 멈춤 및 폭발 연출용

    player = Entity(200, GROUND_Y, "A1", PLAYER_MAX_HP)
    # 🌟 is_boss 정보를 생성할 때 넘겨줌
    enemy = Enemy(1000, GROUND_Y, stage_info["id"], stage_info["hp"], stage_info.get("boss", False))
    
    # 🌟 [대칭 적용 1] P1과 P2(AI) 각각의 콤보 디스플레이 생성
    p1_combo_display = ComboDisplay() 
    p2_combo_display = ComboDisplay()
    
    combo_display = ComboDisplay() # 🌟 [추가] 콤보 디스플레이 생성
    
    all_sprites = pygame.sprite.Group(player, enemy)
    hitstop_timer = 0

    screen_shake_timer = 0
    screen_shake_intensity = 0

    last_key_pressed = None
    last_key_time = 0

    running = True
    while running:
        keys = pygame.key.get_pressed()
        
        if countdown_timer > 0:
            countdown_timer -= 1 # 🌟 [추가] 카운트다운 줄이기

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                # F1, F2는 시스템 단축키라 언제든 작동
                if event.key == pygame.K_F1: player.god_mode = not player.god_mode
                if event.key == pygame.K_F2: enemy.god_mode = not enemy.god_mode
                if event.key == pygame.K_F4:
                    if enemy.state != "DEATH":
                        enemy.hp = 0
                        enemy.state = "DEATH"
                        enemy.timer = 0
                        print("💀 DEBUG: ENEMY KILLED!")

                if event.key == pygame.K_F3:
                    if current_stage_idx < len(STAGE_SEQUENCE) - 1:
                        current_stage_idx += 1
                        next_stage = STAGE_SEQUENCE[current_stage_idx]
            
                        enemy.kill() 
                        # 새로운 적 소환
                        enemy = Enemy(1100, GROUND_Y, next_stage["id"], next_stage["hp"], next_stage.get("boss", False))
                        all_sprites.add(enemy)
            
                        # 플레이어 초기화
                        player.rect.left = 200
                        player.hp = player.max_hp
                        countdown_timer = 240 
                        
                        # 카메라 및 콤보 텍스트 등 초기화
                        CAMERA_X = 0 
                        player.combo_step = 0
                        p1_combo_display.active = False
                        p2_combo_display.active = False
                        
                        print(f"⏩ STAGE SKIPPED! NEXT STAGE: {next_stage['name']}")
                    else:
                        print("⏩ ALREADY AT THE LAST STAGE (OR CLEARED)!")

                # 🌟 [추가] 카운트다운이 끝난 상태에서만 플레이어 조작 가능
                if countdown_timer <= 0:
                    current_time = pygame.time.get_ticks()
                    if event.key in [pygame.K_a, pygame.K_d]:
                        if event.key == last_key_pressed and (current_time - last_key_time) < DOUBLE_TAP_TIME:
                            is_forward = False
                            if (event.key == pygame.K_d and player.facing_right) or (event.key == pygame.K_a and not player.facing_right):
                                is_forward = True
                            player.trigger_dash(is_forward)
                        last_key_pressed, last_key_time = event.key, current_time
                    
                    if event.key == pygame.K_w and player.is_grounded: 
                        if not player.is_attacking and player.state not in ["HIT", "RECOVERY", "DASH"]:
                            player.vel_y = JUMP_FORCE
                    
                    if event.key == pygame.K_i:
                        # 🌟 [추가] 캐릭터가 바라보는 반대(등 뒤) 방향키를 누르고 있는지 체크
                        is_back_pressed = (keys[pygame.K_a] and player.facing_right) or (keys[pygame.K_d] and not player.facing_right)
                        
                        # C1이고, 등 뒤 방향키를 누른 채 i를 누르면 양방향 타격기(REVERSE) 발동
                        if player.is_grounded and player.state in ["IDLE", "RUN", "DASH"]:
                            if player.char_id == "C1" and is_back_pressed:
                                player.handle_attack("REVERSE")
                            else:
                                player.handle_attack("LIGHT")
                        else:
                            # 그 외의 상태(공격 중 등)일 때는 선입력(buffer)에 저장
                            if player.char_id == "C1" and is_back_pressed:
                                player.add_to_buffer("REVERSE")
                            else:
                                player.add_to_buffer("LIGHT")

                    if event.key == pygame.K_o:
                        if player.is_grounded and player.state in ["IDLE", "RUN", "DASH"]:
                            player.handle_attack("HEAVY")
                        else:
                            player.add_to_buffer("HEAVY")

        if hitstop_timer > 0:
            hitstop_timer -= 1
        else:
            player.is_guarding = False
            
            # 🌟 [추가] 카운트다운이 끝났을 때만 이동 및 AI 작동
            if countdown_timer <= 0:
                if player.is_grounded and not player.is_attacking and player.state not in ["HIT", "RECOVERY", "DASH"]:
                    if (player.facing_right and keys[pygame.K_a]) or (not player.facing_right and keys[pygame.K_d]):
                        player.is_guarding = True

                if player.state != "DASH":
                    if not player.is_attacking and player.state not in ["HIT", "RECOVERY"]: 
                        if keys[pygame.K_a]: player.vel_x = -BACK_WALK_SPEED if player.facing_right else -WALK_SPEED
                        elif keys[pygame.K_d]: player.vel_x = WALK_SPEED if player.facing_right else BACK_WALK_SPEED
                        else: pass 
                    elif player.state == "HIT": pass 
                    elif player.state == "RECOVERY": pass
                    else: pass
                
                enemy.update_ai(player) # 🌟 AI도 여기서 작동 (카운트다운 땐 멍때림)

            # 바라보는 방향 업데이트 (카운트다운 중에도 상대를 쳐다보긴 함)
            if player.state in ["IDLE", "RUN"]:
                player.facing_right = (enemy.rect.centerx > player.rect.centerx)
            if enemy.state in ["IDLE", "RUN"]:
                enemy.facing_right = (player.rect.centerx > enemy.rect.centerx)
            
            if player.state == "DASH" and player.is_cancel_dash:
                if enemy.state == "HIT" and not enemy.is_blocking:
                    enemy.hit_stun_timer += DASH_CANCEL_STUN_BONUS
                player.is_cancel_dash = False 

            if enemy.state == "DASH" and enemy.is_cancel_dash:
                if player.state == "HIT" and not player.is_blocking:
                    player.hit_stun_timer += DASH_CANCEL_STUN_BONUS
                    print(f"⚠️ DANGER! AI가 캔슬 대쉬로 플레이어를 굳혔습니다!")
                enemy.is_cancel_dash = False 

            p1_combo_display.update()
            p2_combo_display.update()
            combo_display.update()
            all_sprites.update()

            if enemy.state == "DEATH" and enemy.frame_index == len(enemy.animations["DEATH"]) - 1:
    # 2초(120프레임) 정도 대기 후 다음 스테이지로 전환하는 타이머를 써도 좋지만, 
    # 일단 즉시 전환 로직입니다.
                if enemy.is_boss and death_delay_timer == 0:
                    # 🌟 보스가 터지는 순간!
                    active_explosions.append(DeathExplosion(enemy.hurtbox.centerx, enemy.hurtbox.centery - 100))
                    death_delay_timer = 100 
                    
                    # 🌟 시간을 잠시 멈춘 듯한 효과 (히트스탑)
                    hitstop_timer = 20 
                    
                    # 🌟 화면 진동은 아주 강하게
                    screen_shake_timer = 50
                    screen_shake_intensity = 25

                if not enemy.is_boss or (enemy.is_boss and death_delay_timer == 1):
                    if current_stage_idx < len(STAGE_SEQUENCE) - 1:
                        current_stage_idx += 1
                        next_stage = STAGE_SEQUENCE[current_stage_idx]
                        enemy.kill() 
                        enemy = Enemy(1100, GROUND_Y, next_stage["id"], next_stage["hp"], next_stage.get("boss", False))
                        all_sprites.add(enemy)
                        player.rect.left = 200
                        player.hp = player.max_hp
                        countdown_timer = 240 
                        death_delay_timer = 0 # 타이머 초기화
                        print(f"NEXT STAGE: {next_stage['name']}")
                    else:
                        print("ALL STAGES CLEARED!")
            if death_delay_timer > 0:
                death_delay_timer -= 1

            target_cam_x = (player.rect.centerx + enemy.rect.centerx) / 2 - SCREEN_WIDTH // 2
            
            CAMERA_X += (target_cam_x - CAMERA_X) * 0.1

            dist = player.rect.centerx - enemy.rect.centerx
            if abs(dist) > VIRTUAL_WALL_DIST:
    # 거리가 벌어지려고 할 때, 멀어지는 방향의 속도를 차단
                if dist > 0: # 플레이어가 오른쪽
                    if player.vel_x > 0: player.vel_x = 0 # 플레이어 전진 차단
                    if enemy.vel_x < 0: enemy.vel_x = 0   # 적 후진 차단
                    player.rect.centerx = enemy.rect.centerx + VIRTUAL_WALL_DIST # 위치 고정
                else: # 플레이어가 왼쪽
                    if player.vel_x < 0: player.vel_x = 0 # 플레이어 후진 차단
                    if enemy.vel_x > 0: enemy.vel_x = 0   # 적 전진 차단
                    player.rect.centerx = enemy.rect.centerx - VIRTUAL_WALL_DIST # 위치 고정

            # 1. 플레이어 -> 적 공격
            if player.hitbox.colliderect(enemy.hurtbox):
                if not player.has_hit: 
                    atk_type = "LIGHT" if player.state == "ATK1" else "HEAVY"
                    combo_count = player.register_hit() 
                    p1_combo_display.trigger(combo_count) 

                    screen_shake_timer = 10 
                    screen_shake_intensity = 8 if atk_type == "HEAVY" else 4 

                    if enemy.take_damage(10, player, atk_type): 
                        # 🌟 [무한 콤보 픽스] 이번 콤보에서 캔슬 대쉬를 안 썼을 때만 게이지 상승!
                        if not player.used_cancel_in_combo:
                            player.hit_gauge += 1
                            if player.hit_gauge >= 3:
                                player.hit_gauge = 0
                                player.dash_charges = 1 
            
                    hitstop_timer = HIT_STOP_LIGHT if atk_type == "LIGHT" else HIT_STOP_HEAVY
                    player.has_hit = True

            # 2. 적 -> 플레이어 공격
            if enemy.hitbox.colliderect(player.hurtbox):
                if not enemy.has_hit:
                    enemy_atk_type = "LIGHT" if enemy.state == "ATK1" else "HEAVY"
                    
                    if enemy.is_boss:
                        screen_shake_timer, screen_shake_intensity = 20, 15
                    else:
                        screen_shake_timer, screen_shake_intensity = 10, 5

                    combo_count = enemy.register_hit()
                    p2_combo_display.trigger(combo_count) 

                    if player.take_damage(10, enemy, enemy_atk_type): 
                        hitstop_timer = HIT_STOP_LIGHT if enemy_atk_type == "LIGHT" else HIT_STOP_HEAVY
                        enemy.has_hit = True
                        
                        # 🌟 [무한 콤보 픽스] AI도 무한 대쉬 콤보 불가!
                        if not enemy.used_cancel_in_combo:
                            enemy.hit_gauge += 1
                            if enemy.hit_gauge >= 3:
                                enemy.hit_gauge = 0
                                enemy.dash_charges = 1
                    

        # 그리기
        screen.fill((50, 50, 50))
        
        # 1. 월드 요소 그리기 (오프셋 및 카메라 적용)
        offset_x, offset_y = 0, 0
        if screen_shake_timer > 0:
            offset_x = random.randint(-screen_shake_intensity, screen_shake_intensity)
            offset_y = random.randint(-screen_shake_intensity, screen_shake_intensity)
            screen_shake_timer -= 1

        for entity in all_sprites:
            # 잔상
            for img, rect, alpha in entity.ghosts:
                img.set_alpha(alpha) 
                screen.blit(img, (rect.x + offset_x - CAMERA_X, rect.y + offset_y))
            # 본체
            screen.blit(entity.image, (entity.rect.x + offset_x - CAMERA_X, entity.rect.y + offset_y))

        # 바닥선
        pygame.draw.line(screen, (100, 100, 100), (0 + offset_x - CAMERA_X, GROUND_Y + offset_y), (SCREEN_WIDTH + offset_x - CAMERA_X, GROUND_Y + offset_y), 2)

        # 히트박스/허트박스 디버그 라인 (오프셋 적용)
        if player.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), player.hitbox.move(offset_x - CAMERA_X, offset_y), 2)
        if enemy.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), enemy.hitbox.move(offset_x - CAMERA_X, offset_y), 2)
        pygame.draw.rect(screen, (0, 255, 0), player.hurtbox.move(offset_x - CAMERA_X, offset_y), 1)
        pygame.draw.rect(screen, (0, 255, 0), enemy.hurtbox.move(offset_x - CAMERA_X, offset_y), 1)

        # 🌟 [추가] AI의 공격 사거리(Attack Reach) 시각화 (노란색 선)
        if hasattr(enemy, 'debug_reach'):
            # 적이 바라보는 방향으로 사거리 끝 좌표 계산
            reach_x = enemy.rect.centerx + (enemy.debug_reach if enemy.facing_right else -enemy.debug_reach)
            
            # 적 발밑에서부터 사거리 끝까지 노란색 선 그리기
            start_pos = (enemy.rect.centerx + offset_x - CAMERA_X, enemy.rect.bottom + offset_y)
            end_pos = (reach_x + offset_x - CAMERA_X, enemy.rect.bottom + offset_y)
            pygame.draw.line(screen, (255, 255, 0), start_pos, end_pos, 4) # 두께 4의 노란선

        if getattr(enemy, 'is_transforming', False):
            center_pos = (enemy.rect.centerx + offset_x - CAMERA_X, enemy.rect.centery + offset_y)

            pillar = pygame.Surface((120, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = random.randint(50, 150)
            pygame.draw.rect(pillar, (255, 0, 0, alpha), (0, 0, 120, SCREEN_HEIGHT))
            screen.blit(pillar, (enemy.rect.centerx - 60 - CAMERA_X, 0))

            radius1 = enemy.pre_transform_timer * 5
            pygame.draw.circle(screen, (255, 0, 0), center_pos, radius1, 5)
        
            screen_shake_timer, screen_shake_intensity = 2, 8

            # 시간이 지날수록 원이 작아지며 캐릭터에게 흡수되는 연출
            radius1 = enemy.pre_transform_timer * 3
            radius2 = enemy.pre_transform_timer * 1.5
            center_pos = (enemy.rect.centerx + offset_x - CAMERA_X, enemy.rect.centery + offset_y)
            pygame.draw.circle(screen, (200, 0, 255), center_pos, radius1, 3)
            pygame.draw.circle(screen, (255, 100, 255), center_pos, radius2, 5)
            
            # 기 모으는 동안 화면 미세 진동
            screen_shake_timer = 2
            screen_shake_intensity = 3

        # 가드 이펙트
        for entity in all_sprites:
            if hasattr(entity, 'guard_effect_timer') and entity.guard_effect_timer > 0:
                facing_val = 1 if entity.facing_right else -1
                y_val = 100 if entity.char_id == "A1" else 10
                entity.guard_effect.draw(screen, entity.rect.centerx + offset_x - CAMERA_X, entity.rect.centery + offset_y, facing_val, y_val)

        # 캔슬 대쉬 UI (캐릭터 머리 위)
        for entity in all_sprites:
            if hasattr(entity, 'cancel_ui_timer') and entity.cancel_ui_timer > 0:
                entity.cancel_ui_timer -= 1
                y_offset = 30 - entity.cancel_ui_timer
                cancel_text = font_small.render("CANCEL!", True, (0, 255, 255))
                screen.blit(cancel_text, (entity.rect.centerx - CAMERA_X - cancel_text.get_width()//2, entity.rect.top - 20 - y_offset))

        # 콤보 디스플레이
        p1_combo_rect = player.rect.copy()
        p1_combo_rect.x -= CAMERA_X
        p1_combo_display.draw(screen, p1_combo_rect)

        p2_combo_rect = enemy.rect.copy()
        p2_combo_rect.x -= CAMERA_X
        p2_combo_display.draw(screen, p2_combo_rect)

        # ========================================================
        # 🌟 격투 게임 대칭형 HUD (Heads Up Display)
        # ========================================================
        
        # [중앙 VS 마크]
        vs_text = font_large.render("VS", True, (255, 200, 0))
        screen.blit(vs_text, (SCREEN_WIDTH//2 - vs_text.get_width()//2, 30))

        # [Player 1 (왼쪽) UI]
        p1_hp_ratio = player.hp / player.max_hp
        p1_color = (0, 255, 0) if p1_hp_ratio > 0.5 else (255, 255, 0) if p1_hp_ratio > 0.2 else (255, 0, 0)
        pygame.draw.rect(screen, (80, 0, 0), (50, 40, 450, 30)) # 배경
        pygame.draw.rect(screen, p1_color, (50, 40, 450 * p1_hp_ratio, 30)) # HP
        pygame.draw.rect(screen, (255, 255, 255), (50, 40, 450, 30), 3) # 테두리
        
        p1_name = font_small.render("PLAYER 1", True, (255, 255, 255))
        screen.blit(p1_name, (50, 15))

        # Player 1 게이지 (좌측 하단)
        for i in range(3):
            color = (0, 200, 255) if i < player.hit_gauge else (60, 60, 60)
            pygame.draw.circle(screen, color, (60 + (i * 30), 680), 10)
        p1_dash_text = font_small.render(f"DASH: {player.dash_charges}", True, (255, 255, 255))
        screen.blit(p1_dash_text, (160, 670))

        if countdown_timer > 0:
            if countdown_timer > 180: text_str, color = "3", (255, 255, 255)
            elif countdown_timer > 120: text_str, color = "2", (255, 255, 255)
            elif countdown_timer > 60: text_str, color = "1", (255, 255, 255)
            else: text_str, color = "FIGHT!", (255, 50, 50)
            
            # 심장 박동처럼 텍스트 크기가 울렁거리는(Pop) 효과
            scale_anim = math.sin(((countdown_timer % 60) / 60) * 3.14) if countdown_timer > 60 else math.sin((countdown_timer / 60) * 3.14)
            scale = 1.0 + (scale_anim * 0.3)
            
            cd_text = font_huge.render(text_str, True, color)
            cd_shadow = font_huge.render(text_str, True, (0, 0, 0))
            
            w, h = cd_text.get_size()
            scaled_w, scaled_h = int(w * scale), int(h * scale)
            cd_text = pygame.transform.scale(cd_text, (scaled_w, scaled_h))
            cd_shadow = pygame.transform.scale(cd_shadow, (scaled_w, scaled_h))
            
            # 정중앙 배치
            screen.blit(cd_shadow, (SCREEN_WIDTH//2 - scaled_w//2 + 5, SCREEN_HEIGHT//2 - scaled_h//2 + 5))
            screen.blit(cd_text, (SCREEN_WIDTH//2 - scaled_w//2, SCREEN_HEIGHT//2 - scaled_h//2))


        # [Player 2 (오른쪽) UI] - 데미지를 입으면 가운데 쪽으로 줄어듦
        p2_hp_ratio = enemy.hp / enemy.max_hp
        p2_color = (0, 255, 0) if p2_hp_ratio > 0.5 else (255, 255, 0) if p2_hp_ratio > 0.2 else (255, 0, 0)
        p2_bar_x = SCREEN_WIDTH - 50 - 450
        pygame.draw.rect(screen, (80, 0, 0), (p2_bar_x, 40, 450, 30)) # 배경
        # 🌟 격투게임식 역방향 HP바 (오른쪽 끝 고정, 가운데로 줄어듦)
        pygame.draw.rect(screen, p2_color, (p2_bar_x + 450 * (1 - p2_hp_ratio), 40, 450 * p2_hp_ratio, 30)) 
        pygame.draw.rect(screen, (255, 255, 255), (p2_bar_x, 40, 450, 30), 3) # 테두리
        
        p2_name = font_small.render("PLAYER 2 (AI)", True, (255, 255, 255))
        screen.blit(p2_name, (SCREEN_WIDTH - 50 - p2_name.get_width(), 15))

        # Player 2 게이지 (우측 하단, 대칭 배치)
        for i in range(3):
            color = (255, 50, 50) if i < enemy.hit_gauge else (60, 60, 60) # 적은 붉은색 게이지
            pygame.draw.circle(screen, color, (SCREEN_WIDTH - 60 - (i * 30), 680), 10)
        p2_dash_text = font_small.render(f"DASH: {enemy.dash_charges}", True, (255, 255, 255))
        screen.blit(p2_dash_text, (SCREEN_WIDTH - 240, 670))

        for exp in active_explosions:
            exp.update()
            exp.draw(screen, CAMERA_X)
        active_explosions = [e for e in active_explosions if e.shards]

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()