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

# 🌟 [신규 추가] 게임 상태 관리 및 설정 제어 변수들
GAME_STATE = "MENU"   # "MENU" (메인), "SETTINGS" (설정), "REBINDING" (키 변경 대기), "GAMEPLAY" (인게임)
SHOW_HITBOXES = False  # True: 히트박스 디버그 가시화 / False: 디버그 사각형 숨김
GLOBAL_VOLUME = 0.5   # 0.0 ~ 1.0 사운드 기본 볼륨 크기 (50% 시작)

# 🌟 [신규 추가] 사용자 정의 키 바인딩 초기 기본값
KEY_BINDINGS = {
    "LEFT": pygame.K_a,
    "RIGHT": pygame.K_d,
    "DOWN": pygame.K_s,  # 🌟 [추가] 아래 방향키 기본값 S 추가
    "JUMP": pygame.K_w,
    "LIGHT": pygame.K_i,
    "HEAVY": pygame.K_o
}
REBIND_TARGET = None  # 현재 변경 대기 중인 대상 키 정보 기록용

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


SOUNDS = {}

def apply_volume():
    for sound in SOUNDS.values():
        if sound:
            sound.set_volume(GLOBAL_VOLUME)


def play_sound(name):
    if name in SOUNDS and SOUNDS[name]:
        SOUNDS[name].play()

def play_sound_slow(name, factor=0.5):
    if name in SOUNDS and SOUNDS[name]:
        try:
            sound = SOUNDS[name]
            # 오디오 소스의 순수 PCM 바이트 데이터를 가져옵니다.
            raw_bytes = sound.get_raw()
            
            # 16비트 스테레오 오디오 기준 1프레임은 4바이트(좌우 채널 각각 2바이트)입니다.
            frame_size = 4
            repeat_factor = int(1.0 / factor)
            
            new_bytes = bytearray()
            # 4바이트 단위로 오디오 프레임을 쪼개어 단순 바이트 곱셈 연산으로 샘플을 늘립니다.
            for i in range(0, len(raw_bytes), frame_size):
                frame = raw_bytes[i : i + frame_size]
                if len(frame) == frame_size:
                    new_bytes.extend(frame * repeat_factor)
                    
            # 수정된 순수 바이트 버퍼를 통해 pygame Sound 객체를 새로 생성해 재생합니다.
            slowed_sound = pygame.mixer.Sound(buffer=bytes(new_bytes))
            slowed_sound.play()
        except Exception as e:
            # 예상치 못한 형식 오류 발생 시 시스템 중단 없이 원본 일반 속도로 안전하게 대체 재생합니다.
            print(f"⚠️ 사운드 감속 재생 실패 (일반 사운드로 대체): {e}")
            SOUNDS[name].play()

class DeathExplosion:
    def __init__(self, x, y):
        self.shards = []
        for _ in range(60):
            self.shards.append({
                "pos": [x, y],
                "vel": [random.uniform(-15, 15), random.uniform(-15, 15)], 
                "size": [random.randint(4, 12), random.randint(2, 4)], 
                "color": random.choice([(255, 255, 255), (100, 0, 255), (50, 0, 100)]), 
                "life": random.randint(30, 60),
                "angle": random.uniform(0, 360)
            })
        self.flash_alpha = 255 

    def update(self):
        for s in self.shards:
            s["pos"][0] += s["vel"][0]
            s["pos"][1] += s["vel"][1]
            s["vel"][0] *= 0.94
            s["vel"][1] *= 0.94
            s["life"] -= 1
            
        self.shards = [s for s in self.shards if s["life"] > 0]

        if self.flash_alpha > 0:
            self.flash_alpha -= 15 

    def draw(self, surface, camera_x):
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(self.flash_alpha)
            surface.blit(flash_surf, (0, 0))

        for s in self.shards:
            shard_surf = pygame.Surface((s["size"][0], s["size"][1]))
            shard_surf.fill(s["color"])
            surface.blit(shard_surf, (s["pos"][0] - camera_x, s["pos"][1]))


# 🌟 [신규 추가] 타격감 극대화를 위한 피격 스파크 파티클 클래스
class HitSpark:
    def __init__(self, x, y, is_heavy=False):
        self.shards = []  # 기존 메인 루프의 업데이트 필터(shards) 연동을 위해 변수명을 일치시킵니다.
        count = 24 if is_heavy else 10
        speed = 10 if is_heavy else 5
        colors = [(255, 255, 255), (255, 220, 0), (255, 80, 0)] if is_heavy else [(255, 255, 255), (200, 200, 200)]
        
        for _ in range(count):
            self.shards.append({
                "pos": [x + random.randint(-10, 10), y + random.randint(-20, 20)],
                "vel": [random.uniform(-speed, speed), random.uniform(-speed, speed) - 2],
                "size": [random.randint(4, 8), random.randint(4, 8)] if is_heavy else [random.randint(2, 5), random.randint(2, 5)],
                "color": random.choice(colors),
                "life": random.randint(10, 20)
            })

    def update(self):
        for s in self.shards:
            s["pos"][0] += s["vel"][0]
            s["pos"][1] += s["vel"][1]
            s["vel"][1] += 0.3  # 약간의 중력 가속도 효과 추가
            s["life"] -= 1
        self.shards = [s for s in self.shards if s["life"] > 0]

    def draw(self, surface, camera_x):
        for s in self.shards:
            spark_surf = pygame.Surface((s["size"][0], s["size"][1]))
            spark_surf.fill(s["color"])
            surface.blit(spark_surf, (s["pos"][0] - camera_x, s["pos"][1]))


class RomanCancelEffect:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = 230
        self.color = color
        self.life = 15
        self.alpha = 200
        self.shards = [1]  # 기존 메인 루프의 이펙트 자동 해제 필터(shards)와의 연동을 위함

    def update(self):
        # 둥글게 원형이 퍼져나가는 연출
        self.radius += 15
        self.alpha = max(0, self.alpha - 13)
        self.life -= 1
        if self.life <= 0:
            self.shards = []  # 수명이 다하면 리스트에서 자동 제거되도록 비웁니다.

    def draw(self, surface, camera_x):
        if self.life > 0:
            circle_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (self.color[0], self.color[1], self.color[2], self.alpha), (int(self.radius), int(self.radius)), int(self.radius), 8)
            surface.blit(circle_surf, (self.x - self.radius - camera_x, self.y - self.radius))


class ParallaxBackground:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.layers = []
        
        # 1️⃣ 변수값 크기 지정 (기존 1280에서 1920으로, 920에서 1380으로 50% 확대)
        self.bg_width = int(screen_width * 1.7)  
        self.bg_height = int(920 * 1.7)         
        self.bg_y_offset = -520 * 1.7
        
        layer_files = [
            "Layer_0011_0.png",
            "Layer_0010_1.png",
            "Layer_0009_2.png",
            "Layer_0008_3.png",
            "Layer_0007_Lights.png",
            "Layer_0006_4.png",
            "Layer_0005_5.png",
            "Layer_0004_Lights.png",
            "Layer_0003_6.png",
            "Layer_0002_7.png",
            "Layer_0001_8.png",
            "Layer_0000_9.png"
        ]
        
        num_layers = len(layer_files)
        for idx, filename in enumerate(layer_files):
            path = os.path.join("dd", "assets", "Background layers", filename)
            try:
                img = pygame.image.load(path).convert_alpha()
                # 2️⃣ [체크] 이 부분에서 반드시 screen_width가 아닌 'self.bg_width'가 들어가야 실제로 크기가 확대됩니다!
                img = pygame.transform.scale(img, (self.bg_width, self.bg_height))
                
                factor = 0.02 + (idx / (num_layers - 1)) * 0.85
                self.layers.append({"image": img, "factor": factor})
            except Exception as e:
                print(f"⚠️ 배경 레이어 로드 실패: {filename} | 에러: {e}")

    def draw(self, surface, camera_x):
        for layer in self.layers:
            img = layer["image"]
            factor = layer["factor"]
            
            # 3️⃣ [체크] 반복 계산 부분도 기존 'self.screen_width'가 아닌 늘어난 가로 크기 'self.bg_width'를 적용해 주어야 합니다.
            scroll_x = int(-camera_x * factor) % self.bg_width
            
            surface.blit(img, (scroll_x - self.bg_width, self.bg_y_offset))
            surface.blit(img, (scroll_x, self.bg_y_offset))

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
        self.font = pygame.font.SysFont("impact", 55)  # 임팩트 있는 폰트
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
            path = os.path.join("dd", "assets", f"{self.char_id}_{suffix}.png")
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
        self.flash_timer = 0

        if char_id == "A1":
            self.hurtbox_w, self.hurtbox_h = 60, 100 # 플레이어는 세로로 긴 형태
        elif char_id == "B1":
            self.hurtbox_w, self.hurtbox_h = 150, 40  # 적(B1)은 낮고 뭉툭한 형태
        else:
            self.hurtbox_w, self.hurtbox_h = 80, 80
            
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
            base_stun = 10 if is_guarding else 35
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
            if attack_type == "HEAVY":
                base_knockback = 5  # 원래는 KNOCKBACK_HIT(12) 였음
            else:
                base_knockback = KNOCKBACK_HIT
                self.is_blocking = False

        final_knockback = base_knockback

        if not self.god_mode:
            self.hp -= final_damage
        else:
            print(f"✨ {self.char_id} is INVINCIBLE!") 
            
        # 🌟 타격 시 캐릭터 흰색 플래시 타이머 작동 (일반 피격 시 6프레임 작동)
        if not is_guarding:
            self.flash_timer = 6
    
        self.hit_stun_timer = final_stun
        self.state = "HIT"
        self.timer = 0 # 피격 애니메이션 첫 프레임부터 시작하도록 초기화
        self.is_attacking = False
        attacker.recovery_frames = base_recovery
    
        if self.hp <= 0:
            self.hp = 0
            # 🌟 [버그 수정] 사망 진입 시 타이머 초기화
            if self.state != "DEATH":
                self.state = "DEATH"
                self.timer = 0
                # 보스가 기를 모으는 중에 체력이 0이 되었을 경우 이펙트 플래그를 명확히 해제합니다.
                if hasattr(self, 'is_transforming'):
                    self.is_transforming = False
                    self.pre_transform_timer = 0
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
                    play_sound("cancel") # 콤보 캔슬음 재생
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

        # 🌟 피격 플래시 타이머 점차 감소 연산
        if hasattr(self, 'flash_timer') and self.flash_timer > 0:
            self.flash_timer -= 1

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
                    
                    play_sound("miss") # 헛방 사운드 재생

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

    def trigger_roman_cancel(self, opponent, active_explosions):
        if self.state == "DEATH" or self.hp <= 0:
            return False

        if self.dash_charges >= 1:
            self.dash_charges -= 1
            
            # 본인의 모든 액션/피격 경직 모션을 강제 취소 및 리셋
            self.state = "IDLE"
            self.hit_stun_timer = 0
            self.vel_x = 0
            self.vel_y = 0
            self.is_attacking = False
            self.recovery_timer = 0
            self.combo_step = 0
            self.combo_timer = 0
            self.used_cancel_in_combo = False
            self.flash_timer = 0
            
            # 푸른색(유저) 또는 적색(보스/적) 충격파 사운드 및 이펙트 소환
            play_sound_slow("cancel", factor=0.7)
            effect_color = (0, 240, 255) if self.char_id == "A1" else (240, 0, 100)
            active_explosions.append(RomanCancelEffect(self.rect.centerx, self.rect.centery + 50, effect_color))
            
            # 주위의 상대를 날려버리는 물리 판정 (반경 260픽셀 이내)
            dist = opponent.rect.centerx - self.rect.centerx
            if abs(dist) < 260 and opponent.state != "DEATH" and opponent.hp > 0:
                opponent.state = "HIT"
                opponent.hit_stun_timer = 40  # 큰 피격 경직 부여
                opponent.vel_x = 18 if dist > 0 else -18  # 좌우로 강하게 넉백
                opponent.vel_y = -8                       # 공중으로 띄움
                opponent.is_attacking = False
                opponent.hitbox = pygame.Rect(0, 0, 0, 0)
                
                # 타격 파편(스파크) 강도 높게 생성
                active_explosions.append(HitSpark(opponent.hurtbox.centerx, opponent.hurtbox.centery, is_heavy=True))
                print(f"💥 {self.char_id} 로망 캔슬! 상대방을 밀쳐냈습니다.")
            return True
        return False

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
            path = os.path.join("dd", "assets", f"{self.char_id}_{suffix}.png")
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


    def update_ai(self, target, active_explosions):
    # 후딜레이(RECOVERY) 상태일 때도 AI가 아무 행동(점프, 이동, 가드)을 못 하게 막음
        if self.state == "DEATH": return 
        
        # 🌟 [신규 추가] AI 탈출 버스트 판정
        # 본인이 피격(HIT) 당하는 중이고 기가 1개 이상 있으며, 상대방(유저)의 콤보가 3타 이상일 때
        if self.state == "HIT" and self.dash_charges >= 1:
            # 1️⃣ 플레이어가 공격을 끊고 '캔슬 대쉬'로 파고드는 순간, 85%의 아주 높은 확률로 즉각 카운터 격발!
            if target.state == "DASH" and getattr(target, 'is_cancel_dash', False):
                if random.random() < 0.85:  # 85% 확률로 유저의 연장 콤보 시도를 차단하고 탈출합니다.
                    self.trigger_roman_cancel(target, active_explosions)
                    return
            
            # 2️⃣ 일반 콤보 공격을 받을 때는 자원을 아끼도록 기존 확률을 낮춥니다 (매 프레임 1% 미만인 0.8% 연산)
            # 이를 통해 왠만해서는 플레이어가 대쉬 캔슬 콤보를 선사할 때만 전략적으로 로망 캔슬을 대응하게 만듭니다.
            elif target.combo_step >= 3:
                if random.random() < 0.008:
                    self.trigger_roman_cancel(target, active_explosions)
                    return
        
        # [추가] 플레이어가 죽으면 AI는 속도를 0으로 만들고 가드를 푼 채 IDLE(대기) 상태로 굳어집니다.
        if target.state == "DEATH":
            self.vel_x = 0
            self.is_guarding = False
            self.state = "IDLE"
            return
        
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
                        # 현재 공격 타입(약/강)에 맞춰 프레임 기준을 유동적으로 결정합니다.
                    atk_type = getattr(self, 'current_atk_type', "LIGHT")
                    total_frames = LIGHT_ATK_TOTAL_FRAMES if atk_type == "LIGHT" else HEAVY_ATK_TOTAL_FRAMES
                        
                    hit_end_f = (state_info[2] + 1) * (total_frames / state_info[1])
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
                # 플레이어의 현재 공격 타입 확인
                player_atk_type = getattr(target, 'current_atk_type', "LIGHT")

                # [정밀 제어] 플레이어가 실제로 AI 방향을 바라보고 공격하는지 판별 (뒤통수 공격에 회피 낭비 방지)
                is_player_facing_me = (dist > 0 and not target.facing_right) or (dist < 0 and target.facing_right)

                # 1. 플레이어 강공격(HEAVY) 감지 시 안전거리를 계산하여 파고들기 회피
                if player_atk_type == "HEAVY" and is_player_facing_me and self.dash_cooldown_timer <= 0:
                    # 수학적 안전 한계선 검사 (abs_dist < 380픽셀이어야 앞대쉬 후 사각지대 진입 또는 역가드 성립)
                    if abs_dist < 380:
                        if random.random() < 0.8:  # 80% 확률로 시도
                            self.trigger_dash(is_forward=True)
                            self.decision_timer = 20
                            print(f"🤖 AI: 안전거리 내 진입 확인({int(abs_dist)}px)! 앞대쉬로 사각지대 돌파!")
                            return

                # [강화] 2. 플레이어가 일반 공격 중일 때, 쿨타임이 없다면 백대쉬로 안전하게 피합니다.
                if self.dash_cooldown_timer <= 0 and random.random() < cfg["dash_back_prob"]: 
                    self.trigger_dash(is_forward=False)
                    self.decision_timer = 15
                    print("🤖 AI: 플레이어 공격 감지! 백대쉬로 거리 벌리기!")
                    return
                
                # 3. 뒤잡기 점프
                if target.state == "ATK1" and random.random() < cfg["back_catch_prob"]: 
                    self.vel_y = JUMP_FORCE 
                    self.state = "DASH" 
                    self.dash_timer = 20 
                    self.vel_x = (DASH_SPEED * 1.3) if self.facing_right else (-DASH_SPEED * 1.3)
                    self.decision_timer = 30 
                    play_sound("jump") 
                    print("🤖 AI: 완벽한 뒤잡기 점프!")
                    return
                
                # 4. 제자리 가드
                if random.random() < cfg["guard_prob"]: 
                    self.is_guarding = True 
                    self.decision_timer = 10
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
                play_sound("jump") # AI 점프음 재생
            else:
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.decision_timer = 5 

        else: 
            self.handle_attack(planned_atk)
            self.decision_timer = 20

    def update(self):
        super().update()

def main():
    global CAMERA_X, GAME_STATE, GLOBAL_VOLUME, SHOW_HITBOXES

    pygame.mixer.pre_init(44100, -16, 2, 512) # 이전 답변에서 적용한 지연 시간 최적화 포함
    pygame.init()

    global SOUNDS

    sound_path = os.path.join("dd", "assets", "sounds")
    sound_files = {
        "3": "threey.wav",
        "2": "two.wav",
        "1": "one.wav",
        "fight": "fight.wav",
        "jump": "jump.wav",
        "cancel": "cancel.wav",
        "light_hit": "low.wav",
        "heavy_hit": "hight.wav",
        "hurt": "hurt.wav",
        "miss": "miss.wav"
    }
    
    # 콤보 사운드 (1~10) 일괄 등록
    for i in range(1, 11):
        sound_files[f"combo_{i}"] = f"combo {i}.wav"

    for key, filename in sound_files.items():
        try:
            SOUNDS[key] = pygame.mixer.Sound(os.path.join(sound_path, filename))
        except Exception as e:
            print(f"⚠️ 사운드 로드 실패 ({filename}): {e}")
            SOUNDS[key] = None

    # 🌟 [추가] 오디오 로드 직후 최초 볼륨(0.5) 크기를 모든 사운드에 주입해 줍니다.
    apply_volume()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand")
    clock = pygame.time.Clock()
    
    # 🌟 [추가] 패럴랙스 배경 인스턴스 생성
    background = ParallaxBackground(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    font_small = pygame.font.SysFont("arial", 20, bold=True)
    font_large = pygame.font.SysFont("arial", 40, bold=True)
    font_huge = pygame.font.SysFont("impact", 120, italic=True) # 🌟 [추가] 카운트다운용 거대 폰트

    current_stage_idx = 0
    stage_info = STAGE_SEQUENCE[current_stage_idx]
    countdown_timer = 240

    active_explosions = []
    death_delay_timer = 0 # 보스 사망 후 화면 멈춤 및 폭발 연출용
    game_over_alpha = 0   # 🌟 플레이어 사망 시 화면 어두워짐 효과를 제어할 변수를 추가합니다.
    game_cleared = False  # 🌟 게임 클리어 상태 플래그를 추가합니다

    game_clear_alpha = 0
    post_clear_timer = 150  # 클리어 문구 노출 대기 시간 (60프레임 = 1초, 약 2.5초 대기)
    post_death_timer = 150  # 사망 DEAD 문구 완료 후 대기 시간 (약 2.5초 대기)

    player = Entity(200, GROUND_Y, "A1", PLAYER_MAX_HP)

    last_down_press_time = 0
    down_double_tap_active = False
    down_double_tap_timestamp = 0


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
    menu_index = 0
    settings_index = 0

    while running:
        keys = pygame.key.get_pressed()
        
        current_time = pygame.time.get_ticks()
        if down_double_tap_active and (current_time - down_double_tap_timestamp > 300):
            down_double_tap_active = False

        # ==========================================
        # 🌟 [메인 메뉴 상태 분기]
        # ==========================================
        if GAME_STATE == "MENU":
            screen.fill((12, 17, 34)) # 짙은 네이비 단색 배경
            
            title_font = pygame.font.SysFont("impact", 75, italic=True)
            menu_font = pygame.font.SysFont("arial", 28, bold=True)
            
            title_surf = title_font.render("THE LAST STAND", True, (255, 200, 0))
            screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 150))
            
            menu_options = ["START GAME", "SETTINGS", "EXIT"]
            for idx, opt in enumerate(menu_options):
                color = (255, 255, 255) if idx == menu_index else (100, 100, 100)
                opt_surf = menu_font.render(opt, True, color)
                screen.blit(opt_surf, (SCREEN_WIDTH // 2 - opt_surf.get_width() // 2, 360 + idx * 65))
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        menu_index = (menu_index - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        menu_index = (menu_index + 1) % len(menu_options)
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if menu_index == 0:
                            GAME_STATE = "GAMEPLAY"
                        elif menu_index == 1:
                            GAME_STATE = "SETTINGS"
                            settings_index = 0
                        elif menu_index == 2:
                            running = False
                            
            pygame.display.flip()
            clock.tick(FPS)
            continue # 메인 메뉴 상태일 땐 하단 인게임 코드 실행 방지

        # ==========================================
        # 🌟 [설정 화면 상태 분기]
        # ==========================================
        elif GAME_STATE == "SETTINGS":
            screen.fill((12, 17, 34))
            
            title_font = pygame.font.SysFont("impact", 60)
            opt_font = pygame.font.SysFont("arial", 24, bold=True)
            
            title_surf = title_font.render("SETTINGS", True, (255, 255, 255))
            screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 80))
            
            # 볼륨 수치 및 바인딩 키 문자화
            volume_str = f"{int(GLOBAL_VOLUME * 100)}%"
            hitboxes_str = "ON" if SHOW_HITBOXES else "OFF"
            
            def get_bound_key_name(action):
                return pygame.key.name(KEY_BINDINGS[action]).upper()

            settings_options = [
                f"VOLUME: <  {volume_str}  >",
                f"SHOW HITBOXES: <  {hitboxes_str}  >",
                f"MOVE LEFT KEY: [ {get_bound_key_name('LEFT')} ]",
                f"MOVE RIGHT KEY: [ {get_bound_key_name('RIGHT')} ]",
                f"MOVE DOWN KEY: [ {get_bound_key_name('DOWN')} ]",  # 🌟 [추가]
                f"JUMP KEY: [ {get_bound_key_name('JUMP')} ]",
                f"LIGHT ATTACK KEY: [ {get_bound_key_name('LIGHT')} ]",
                f"HEAVY ATTACK KEY: [ {get_bound_key_name('HEAVY')} ]",
                "BACK TO MAIN MENU"
            ]
            
            for idx, text in enumerate(settings_options):
                color = (255, 200, 0) if idx == settings_index else (140, 140, 140)
                opt_surf = opt_font.render(text, True, color)
                screen.blit(opt_surf, (SCREEN_WIDTH // 2 - opt_surf.get_width() // 2, 190 + idx * 50))
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        settings_index = (settings_index - 1) % len(settings_options)
                    elif event.key == pygame.K_DOWN:
                        settings_index = (settings_index + 1) % len(settings_options)
                    
                    # 볼륨 미세 제어
                    elif settings_index == 0:
                        if event.key == pygame.K_LEFT:
                            GLOBAL_VOLUME = max(0.0, round(GLOBAL_VOLUME - 0.1, 1))
                            apply_volume()
                        elif event.key == pygame.K_RIGHT:
                            GLOBAL_VOLUME = min(1.0, round(GLOBAL_VOLUME + 0.1, 1))
                            apply_volume()
                            
                    # 히트박스 ON/OFF 스위칭
                    elif settings_index == 1:
                        if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE]:
                            SHOW_HITBOXES = not SHOW_HITBOXES
                            
                    # 키 바인딩 대기 트리거
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if settings_index == 2: REBIND_TARGET = "LEFT"; GAME_STATE = "REBINDING"
                        elif settings_index == 3: REBIND_TARGET = "RIGHT"; GAME_STATE = "REBINDING"
                        elif settings_index == 4: REBIND_TARGET = "DOWN"; GAME_STATE = "REBINDING"  # 🌟 [추가]
                        elif settings_index == 5: REBIND_TARGET = "JUMP"; GAME_STATE = "REBINDING"
                        elif settings_index == 6: REBIND_TARGET = "LIGHT"; GAME_STATE = "REBINDING"
                        elif settings_index == 7: REBIND_TARGET = "HEAVY"; GAME_STATE = "REBINDING"
                        elif settings_index == 8:
                            GAME_STATE = "MENU"
                            settings_index = 0
                            
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # ==========================================
        # 🌟 [키 바인딩 감지 및 저장 분기]
        # ==========================================
        elif GAME_STATE == "REBINDING":
            screen.fill((12, 17, 34))
            rebind_font = pygame.font.SysFont("arial", 26, bold=True)
            
            line1 = rebind_font.render(f"REBINDING ACTION: {REBIND_TARGET}", True, (255, 200, 0))
            line2 = rebind_font.render("PRESS ANY KEY ON KEYBOARD TO DEFINE ACTION...", True, (255, 255, 255))
            
            screen.blit(line1, (SCREEN_WIDTH // 2 - line1.get_width() // 2, SCREEN_HEIGHT // 2 - 35))
            screen.blit(line2, (SCREEN_WIDTH // 2 - line2.get_width() // 2, SCREEN_HEIGHT // 2 + 25))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    # 입력받은 키를 딕셔너리에 매핑 후 원복
                    KEY_BINDINGS[REBIND_TARGET] = event.key
                    GAME_STATE = "SETTINGS"
                    REBIND_TARGET = None
                    
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # (이하 기존 카운트다운 및 인게임 로직이 전개됩니다)
        if countdown_timer > 0:
            # 🌟 텍스트가 바뀌는 정확한 프레임에 음성을 1번씩만 재생
            if countdown_timer == 240: play_sound("3")
            elif countdown_timer == 180: play_sound("2")
            elif countdown_timer == 120: play_sound("1")
            elif countdown_timer == 60: play_sound("fight")
            
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
                
                if event.key == pygame.K_F5:
                    if enemy.state != "DEATH":
                        enemy.hp = 1
                        print("🎯 DEBUG: ENEMY HP SET TO 1!")

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
                    
                    # 🌟 [신규 추가] 아래(DOWN) 키를 더블 탭했는지 감지하는 부분
                    if event.key == KEY_BINDINGS["DOWN"]:
                        if (current_time - last_down_press_time) < DOUBLE_TAP_TIME:
                            down_double_tap_active = True
                            down_double_tap_timestamp = current_time
                        last_down_press_time = current_time
                    
                    # 이동키 설정 기반 대쉬 처리
                    if event.key in [KEY_BINDINGS["LEFT"], KEY_BINDINGS["RIGHT"]]:
                        if event.key == last_key_pressed and (current_time - last_key_time) < DOUBLE_TAP_TIME:
                            is_forward = False
                            if (event.key == KEY_BINDINGS["RIGHT"] and player.facing_right) or (event.key == KEY_BINDINGS["LEFT"] and not player.facing_right):
                                is_forward = True
                            player.trigger_dash(is_forward)
                        last_key_pressed, last_key_time = event.key, current_time
                    
                    # 점프 처리
                    if event.key == KEY_BINDINGS["JUMP"] and player.is_grounded: 
                        if not player.is_attacking and player.state not in ["HIT", "RECOVERY", "DASH"]:
                            player.vel_y = JUMP_FORCE
                            play_sound("jump")
                    
                    # 약공격 / 역방향 콤보
                    if event.key == KEY_BINDINGS["LIGHT"]:
                        # 🌟 [신규 추가] 아래 더블 탭 중 약공격을 가했을 경우 로망 캔슬 가동
                        if down_double_tap_active and player.dash_charges >= 1:
                            player.trigger_roman_cancel(enemy, active_explosions)
                            down_double_tap_active = False
                        else:
                            is_back_pressed = (keys[KEY_BINDINGS["LEFT"]] and player.facing_right) or (keys[KEY_BINDINGS["RIGHT"]] and not player.facing_right)
                            
                            if player.is_grounded and player.state in ["IDLE", "RUN", "DASH"]:
                                if player.char_id == "C1" and is_back_pressed:
                                    player.handle_attack("REVERSE")
                                else:
                                    player.handle_attack("LIGHT")
                            else:
                                if player.char_id == "C1" and is_back_pressed:
                                    player.add_to_buffer("REVERSE")
                                else:
                                    player.add_to_buffer("LIGHT")

                    # 강공격
                    if event.key == KEY_BINDINGS["HEAVY"]:
                        # 🌟 [신규 추가] 아래 더블 탭 중 강공격을 가했을 경우 로망 캔슬 가동
                        if down_double_tap_active and player.dash_charges >= 1:
                            player.trigger_roman_cancel(enemy, active_explosions)
                            down_double_tap_active = False
                        else:
                            if player.is_grounded and player.state in ["IDLE", "RUN", "DASH"]:
                                player.handle_attack("HEAVY")
                            else:
                                player.add_to_buffer("HEAVY")

        if hitstop_timer > 0:
            hitstop_timer -= 1
        else:
            player.is_guarding = False
            
            # 🌟 [수정] 설정된 사용자 키(KEY_BINDINGS)를 기준으로 매칭하여 연속 동작을 연산합니다.
            if countdown_timer <= 0:
                if player.is_grounded and not player.is_attacking and player.state not in ["HIT", "RECOVERY", "DASH"]:
                    if (player.facing_right and keys[KEY_BINDINGS["LEFT"]]) or (not player.facing_right and keys[KEY_BINDINGS["RIGHT"]]):
                        player.is_guarding = True

                if player.state != "DASH":
                    if not player.is_attacking and player.state not in ["HIT", "RECOVERY"]: 
                        if keys[KEY_BINDINGS["LEFT"]]: player.vel_x = -BACK_WALK_SPEED if player.facing_right else -WALK_SPEED
                        elif keys[KEY_BINDINGS["RIGHT"]]: player.vel_x = WALK_SPEED if player.facing_right else BACK_WALK_SPEED
                        else: pass 
                    elif player.state == "HIT": pass
                    elif player.state == "RECOVERY": pass
                    else: pass
                
                # 🌟 [수정] active_explosions를 넘겨주어 AI가 유저 콤보 도중에 로망 캔슬을 격발시킬 수 있도록 합니다.
                enemy.update_ai(player, active_explosions) # 🌟 AI도 여기서 작동 (카운트다운 땐 멍때림)

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

            if enemy.state == "DEATH" and enemy.frame_index == len(enemy.animations["DEATH"]) - 1 and not game_cleared:
                if enemy.is_boss and death_delay_timer == 0:
                    # 🌟 보스가 터지는 순간!
                    active_explosions.append(DeathExplosion(enemy.hurtbox.centerx, enemy.hurtbox.centery - 100))
                    death_delay_timer = 100 
                    
                    # 🌟 대폭발 이펙트와 화면 진동 타이밍에 맞춰 낮고 묵직하게 느려진 슬로우 타격음을 재생합니다.
                    play_sound_slow("light_hit", factor=0.5)
                    
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
                        death_delay_timer = 0 
                        print(f"NEXT STAGE: {next_stage['name']}")
                    else:
                        print("ALL STAGES CLEARED!")
                        game_cleared = True  # 🌟 보스의 상태를 억지로 바꾸지 않고, 클리어 플래그만 세워 루프를 차단합니
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
                    
                    is_boss_fatal = (enemy.is_boss and enemy.state != "DEATH")


                    shake_val = 14 if atk_type == "HEAVY" else 7
                    screen_shake_timer, screen_shake_intensity = 12, shake_val
                    
                    active_explosions.append(HitSpark(enemy.hurtbox.centerx, enemy.hurtbox.centery, atk_type == "HEAVY"))

                    if enemy.take_damage(10, player, atk_type): 
                        # 🌟 [무한 콤보 픽스] 이번 콤보에서 캔슬 대쉬를 안 썼을 때만 게이지 상승!
                        if not player.used_cancel_in_combo:
                            player.hit_gauge += 1
                            if player.hit_gauge >= 3:
                                player.hit_gauge = 0
                                player.dash_charges = 1 
            
                    hitstop_timer = HIT_STOP_LIGHT if atk_type == "LIGHT" else HIT_STOP_HEAVY
                    player.has_hit = True

                    play_sound("light_hit")

                    play_sound("hurt")
                    if combo_count >= 1:
                        play_sound(f"combo_{min(combo_count, 10)}")

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

                    shake_val = 16 if enemy_atk_type == "HEAVY" else 8
                    screen_shake_timer, screen_shake_intensity = 12, shake_val

                    active_explosions.append(HitSpark(player.hurtbox.centerx, player.hurtbox.centery, enemy_atk_type == "HEAVY"))

                    if player.take_damage(10, enemy, enemy_atk_type): 
                        hitstop_timer = HIT_STOP_LIGHT if enemy_atk_type == "LIGHT" else HIT_STOP_HEAVY
                        enemy.has_hit = True
                        
                        # 🌟 [무한 콤보 픽스] AI도 무한 대쉬 콤보 불가!
                        if not enemy.used_cancel_in_combo:
                            enemy.hit_gauge += 1
                            if enemy.hit_gauge >= 3:
                                enemy.hit_gauge = 0
                                enemy.dash_charges = 1
                    
                    play_sound("light_hit")
                    play_sound("hurt")

                    if combo_count >= 1:
                        play_sound(f"combo_{min(combo_count, 10)}")
                    

        # 그리기
        screen.fill((12, 17, 34))

        background.draw(screen, CAMERA_X)
        
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
            # 🌟 [수정] 피격 상태에서 번쩍임 타이머가 도는 중이라면, 흰색 가산 가루를 채워 흰색 플래시를 연출합니다.
            if hasattr(entity, 'flash_timer') and entity.flash_timer > 0:
                flash_img = entity.image.copy()
                flash_img.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(flash_img, (entity.rect.x + offset_x - CAMERA_X, entity.rect.y + offset_y))
            else:
                screen.blit(entity.image, (entity.rect.x + offset_x - CAMERA_X, entity.rect.y + offset_y))

        # 바닥선
        

        # 히트박스/허트박스 디버그 라인 (오프셋 적용)
        if SHOW_HITBOXES:
            if player.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), player.hitbox.move(offset_x - CAMERA_X, offset_y), 2)
            if enemy.hitbox.width > 0: pygame.draw.rect(screen, (255, 0, 0), enemy.hitbox.move(offset_x - CAMERA_X, offset_y), 2)
            pygame.draw.rect(screen, (0, 255, 0), player.hurtbox.move(offset_x - CAMERA_X, offset_y), 1)
            pygame.draw.rect(screen, (0, 255, 0), enemy.hurtbox.move(offset_x - CAMERA_X, offset_y), 1)

            if hasattr(enemy, 'debug_reach'):
                reach_x = enemy.rect.centerx + (enemy.debug_reach if enemy.facing_right else -enemy.debug_reach)
                start_pos = (enemy.rect.centerx + offset_x - CAMERA_X, enemy.rect.bottom + offset_y)
                end_pos = (reach_x + offset_x - CAMERA_X, enemy.rect.bottom + offset_y)
                pygame.draw.line(screen, (255, 255, 0), start_pos, end_pos, 4)

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

        # 🌟 [신규 추가] 플레이어 사망 시 검은 오버레이와 함께 DEAD 텍스트를 출력합니다.
        if player.state == "DEATH":
            if game_over_alpha < 255:
                game_over_alpha += 4  
            
            black_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            black_surf.fill((0, 0, 0))
            black_surf.set_alpha(game_over_alpha)
            screen.blit(black_surf, (0, 0))

            if game_over_alpha >= 180:
                dead_font = pygame.font.SysFont("impact", 130)
                
                dead_text = dead_font.render("DEAD", True, (220, 0, 0))
                dead_shadow = dead_font.render("DEAD", True, (0, 0, 0))
                
                shadow_rect = dead_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 5, SCREEN_HEIGHT // 2 + 5))
                text_rect = dead_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                screen.blit(dead_shadow, shadow_rect)
                screen.blit(dead_text, text_rect)

            # 완전히 어두워진 뒤 타이머 계산 및 메인 메뉴 복귀
            if game_over_alpha >= 255:
                post_death_timer -= 1
                if post_death_timer <= 0:
                    GAME_STATE = "MENU"
                    current_stage_idx = 0
                    stage_info = STAGE_SEQUENCE[current_stage_idx]
                    
                    player.rect.left = 200
                    player.rect.bottom = GROUND_Y
                    player.hp = PLAYER_MAX_HP
                    player.state = "IDLE"
                    player.vel_x = 0
                    player.vel_y = 0
                    player.combo_step = 0
                    player.hit_gauge = 0
                    player.dash_charges = 1
                    player.ghosts.clear()
                    
                    enemy.kill()
                    enemy = Enemy(1000, GROUND_Y, stage_info["id"], stage_info["hp"], stage_info.get("boss", False))
                    all_sprites.empty()
                    all_sprites.add(player, enemy)
                    
                    countdown_timer = 240
                    death_delay_timer = 0
                    game_over_alpha = 0
                    game_cleared = False
                    game_clear_alpha = 0
                    post_clear_timer = 150
                    post_death_timer = 150
                    CAMERA_X = 0
                    p1_combo_display.active = False
                    p2_combo_display.active = False

        # 🌟 [수정 2] 게임 클리어 처리 (플레이어 사망문과 완전히 별개로 독립되어 작동합니다)
        if game_cleared:
            if game_clear_alpha < 255:
                game_clear_alpha += 4
                
            black_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            black_surf.fill((0, 0, 0))
            black_surf.set_alpha(game_clear_alpha)
            screen.blit(black_surf, (0, 0))
            
            if game_clear_alpha >= 180:
                clear_font = pygame.font.SysFont("impact", 110, italic=True)
                clear_text = clear_font.render("GAME CLEAR", True, (255, 200, 0))  # 골드 색상
                clear_shadow = clear_font.render("GAME CLEAR", True, (0, 0, 0))
                
                shadow_rect = clear_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 5, SCREEN_HEIGHT // 2 + 5))
                text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                screen.blit(clear_shadow, shadow_rect)
                screen.blit(clear_text, text_rect)
                
            if game_clear_alpha >= 255:
                post_clear_timer -= 1
                if post_clear_timer <= 0:
                    GAME_STATE = "MENU"
                    current_stage_idx = 0
                    stage_info = STAGE_SEQUENCE[current_stage_idx]
                    
                    # 모든 객체 상태 인스턴스 초기화
                    player.rect.left = 200
                    player.rect.bottom = GROUND_Y
                    player.hp = PLAYER_MAX_HP
                    player.state = "IDLE"
                    player.vel_x = 0
                    player.vel_y = 0
                    player.combo_step = 0
                    player.hit_gauge = 0
                    player.dash_charges = 1
                    player.ghosts.clear()
                    
                    enemy.kill()
                    enemy = Enemy(1000, GROUND_Y, stage_info["id"], stage_info["hp"], stage_info.get("boss", False))
                    all_sprites.empty()
                    all_sprites.add(player, enemy)
                    
                    countdown_timer = 240
                    death_delay_timer = 0
                    game_over_alpha = 0
                    game_cleared = False
                    game_clear_alpha = 0
                    post_clear_timer = 150
                    post_death_timer = 150
                    CAMERA_X = 0
                    p1_combo_display.active = False
                    p2_combo_display.active = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()