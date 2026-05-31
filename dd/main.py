import pygame
import sys
import os
import random
import math  # 🌟 이 줄을 반드시 추가해야 합니다!

PRELOADED_ANIMATIONS = {}  # 🌟 [신규 추가] 보스 및 캐릭터 전역 애니메이션 저장용 캐시
FLASH_CACHE = {}           # 🌟 [최적화용 추가] 피격 흰색 깜빡임 캐시
GHOST_BLUE_CACHE = {}      # 🌟 [최적화용 추가] 일반 캐릭터 푸른 잔상 캐시
GHOST_RED_CACHE = {}       # 🌟 [최적화용 추가] 보스 캐릭터 붉은 잔상 캐시
FLIP_CACHE = {}

# 🌟 [전역 스코프 버그 해결] 하단의 모든 클래스가 인스턴스 전방 참조 에러 없이 즉시 식별하도록 전역 변수와 구조 클래스를 파일 최상단으로 이관합니다.
KO_CINEMATIC_TIMER = 0     # 드라마틱 KO 연출용 타이머 (남은 프레임 수)
KO_TRIGGERED = False       # KO 슬로우 모션이 라운드당 딱 한 번만 트리거되도록 제어하는 플래그
ACTIVE_DAMAGE_NUMBERS = [] # 실시간으로 연산 및 렌더링할 데미지 폰트 오브젝트들의 글로벌 목록

# 🌟 [피격 프레임 드랍 해결] 실시간 SysFont 탐색으로 인한 프레임 스파이크를 없애기 위한 전역 데미지 폰트 레퍼런스 선언
DAMAGE_FONT_NORMAL = None
DAMAGE_FONT_CRIT = None

# 🌟 [전방 참조 해결] Entity 클래스 등 하단에서 호출될 때 에러를 유발하지 않도록 상단 배치
class FloatingDamage:
    def __init__(self, x, y, damage, is_critical=False):
        self.x = x + random.randint(-25, 25)
        self.y = y - random.randint(15, 30)
        self.damage = int(damage)
        self.is_critical = is_critical
        self.life = 45      
        self.vel_y = -4.0   
        
        # 🌟 [프레임 드랍 해결] 피격 생성자 시점에서 SysFont를 불러오는 하드웨어 입출력 병목을 완전히 소거하고 전역 캐싱 폰트를 즉시 인가합니다.
        font = DAMAGE_FONT_CRIT if is_critical else DAMAGE_FONT_NORMAL
        self.color = (255, 60, 0) if is_critical else (255, 220, 0)
        
        # 선행 렌더링된 폰트 이미지만을 고속 메모리 블릿합니다.
        self.text_surf = font.render(str(self.damage), True, self.color)
        self.shadow_surf = font.render(str(self.damage), True, (0, 0, 0))

    def update(self):
        self.y += self.vel_y
        self.vel_y *= 0.90  
        self.life -= 1

    def draw(self, surface, camera_x):
        alpha = min(255, self.life * 12)
        self.text_surf.set_alpha(alpha)
        self.shadow_surf.set_alpha(alpha)
        
        rx = self.x - camera_x
        surface.blit(self.shadow_surf, (rx + 2, self.y + 2))
        surface.blit(self.text_surf, (rx, self.y))


def get_flash_frame(surface, cache_key):
    if cache_key not in FLASH_CACHE:
        flash_surf = surface.copy()
        flash_surf.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
        FLASH_CACHE[cache_key] = flash_surf
    return FLASH_CACHE[cache_key] # 🌟 [메모리 누수 해결 2] 플래시는 투명도 조작이 없으므로 .copy()를 제거하여 메모리 낭비 차단

def get_ghost_blue(surface, cache_key):
    if cache_key not in GHOST_BLUE_CACHE:
        ghost_surf = surface.copy()
        ghost_surf.fill((150, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        GHOST_BLUE_CACHE[cache_key] = ghost_surf
    return GHOST_BLUE_CACHE[cache_key] # 🌟 [렉 해결] 매 프레임 대량의 메모리를 할당하던 .copy()를 완전히 제거

def get_ghost_red(surface, cache_key):
    if cache_key not in GHOST_RED_CACHE:
        ghost_surf = surface.copy()
        ghost_surf.fill((200, 30, 30, 255), special_flags=pygame.BLEND_RGBA_MULT)
        GHOST_RED_CACHE[cache_key] = ghost_surf
    return GHOST_RED_CACHE[cache_key] # 🌟 [렉 해결]


def resource_path(relative_path):
    # 1. PyInstaller로 패키징된 실행 파일 환경인 경우
    try:
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    except Exception:
        pass

    # 2. 소스 코드 직접 실행 환경인 경우
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd_dir = os.path.abspath(".")

    # 경로를 시스템 규격에 맞게 표준화하고 분할합니다.
    normalized_rel = os.path.normpath(relative_path)
    parts = normalized_rel.split(os.sep)

    # 기본 매칭 시도 (스크립트 위치 + 상대 경로)
    path_attempt = os.path.join(script_dir, relative_path)
    if os.path.exists(path_attempt):
        return path_attempt

    # 스크립트 파일 자체가 'dd' 폴더 안에 이미 들어있어 'dd' 경로가 중복되는 경우 예외 처리
    if parts[0] == "dd" and len(parts) > 1:
        truncated_rel = os.path.join(*parts[1:])
        
        # 스크립트 디렉토리 기준에서 'dd'를 제외하고 탐색
        path_attempt_truncated = os.path.join(script_dir, truncated_rel)
        if os.path.exists(path_attempt_truncated):
            return path_attempt_truncated
            
        # 현재 작업 디렉토리 기준에서 'dd'를 제외하고 탐색
        path_cwd_truncated = os.path.join(cwd_dir, truncated_rel)
        if os.path.exists(path_cwd_truncated):
            return path_cwd_truncated

    # 현재 작업 디렉토리(CWD) 기준으로 탐색
    path_cwd = os.path.join(cwd_dir, relative_path)
    if os.path.exists(path_cwd):
        return path_cwd

    # 어떤 조건에도 맞지 않을 경우 기본 경로를 반환하여 에러 처리를 위임합니다.
    return path_attempt

# --- 설정 및 상수 ---
FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCALE_FACTOR = 4 
TOP_CROP = 20 

GRAVITY = 0.8
WALK_SPEED = 12
BACK_WALK_SPEED = 5    # 🌟 [추가] 후진 속도 (더 느리게)
JUMP_FORCE = -20
GROUND_Y = 550

DASH_SPEED = 20
BACK_DASH_SPEED = 8
DASH_DURATION = 12
DASH_COOLDOWN = 30
DOUBLE_TAP_TIME = 250
BUFFER_WINDOW = 12

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
GAME_STATE = "MENU"   # "MENU" (메인), "SETTINGS" (설정), "REBINDING" (키 변경 대기), "GAMEPLAY" (인게임), "PAUSE" (🌟 일시정지 추가)
pause_menu_index = 0  # 🌟 [신규 추가] 일시정지 창 조작용 포인터
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
KNOCKBACK_GUARD = 3  # 가드 피격 넉백



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
    "B1": { # 1스테이지: 쉬움 (샌드백 수준)
        "guard_prob": 0.15, "react_prob": 0.10, "back_catch_prob": 0.3, 
        "jump_in_prob": 0.03, "dash_back_prob": 0.02, "aggressive_dash": 0.05      
    },
    "A2": { # 2스테이지: 보통 (약간의 방어)
        "guard_prob": 0.35, "react_prob": 0.22, "back_catch_prob": 0.5,
        "jump_in_prob": 0.07, "dash_back_prob": 0.04, "aggressive_dash": 0.10      
    },
    "C1": { # 3스테이지: 조금 어려움
        "guard_prob": 0.45, "react_prob": 0.35, "back_catch_prob": 0.6,
        "jump_in_prob": 0.15, "dash_back_prob": 0.08, "aggressive_dash": 0.20      
    },
    "BOSS": { # 4스테이지: 보스 (너무 불합리하지 않게 하향)
        "guard_prob": 0.60, "react_prob": 0.50, "back_catch_prob": 0.7,
        "jump_in_prob": 0.18, "dash_back_prob": 0.12, "aggressive_dash": 0.24      
    }
}


SOUNDS = {}

def apply_volume():
    for sound in SOUNDS.values():
        if sound:
            sound.set_volume(GLOBAL_VOLUME)
     # 🌟 [버그 수정] 캐싱된 특수 효과음(슬로우 사운드)도 볼륨 변경 적용
    for sound in SLOW_SOUNDS_CACHE.values():
        if sound:
            sound.set_volume(GLOBAL_VOLUME)


def play_sound(name):
    if name in SOUNDS and SOUNDS[name]:
        SOUNDS[name].play()

SLOW_SOUNDS_CACHE = {}  # 전역 캐시 딕셔너리 추가


def play_sound_slow(name, factor=0.5):
    if name not in SOUNDS or not SOUNDS[name]:
        return
        
    cache_key = (name, factor)
    if cache_key in SLOW_SOUNDS_CACHE:
        # 캐싱된 사운드 존재 시 연산 생략하고 바로 플레이
        SLOW_SOUNDS_CACHE[cache_key].play()
        return

    try:
        sound = SOUNDS[name]
        raw_bytes = sound.get_raw()
        frame_size = 4
        repeat_factor = int(1.0 / factor)
        
        new_bytes = bytearray()
        for i in range(0, len(raw_bytes), frame_size):
            frame = raw_bytes[i : i + frame_size]
            if len(frame) == frame_size:
                new_bytes.extend(frame * repeat_factor)
                
        slowed_sound = pygame.mixer.Sound(buffer=bytes(new_bytes))
        slowed_sound.set_volume(GLOBAL_VOLUME)
        
        # 캐시 보관
        SLOW_SOUNDS_CACHE[cache_key] = slowed_sound
        slowed_sound.play()
    except Exception as e:
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
            # 🌟 [극강 최적화] 무거운 알파 채널 블릿 대신 단 한 줄의 고속 덧셈 비디오 연산으로 플래시 광원 구현
            surface.fill((self.flash_alpha, self.flash_alpha, self.flash_alpha), special_flags=pygame.BLEND_RGB_ADD)

        for s in self.shards:
            # 🌟 [극강 최적화] 파티클을 그릴 때 draw.rect 대신 Pygame 내부 속도가 가장 빠른 고속 .fill() 기법 사용
            surface.fill(s["color"], (s["pos"][0] - camera_x, s["pos"][1], s["size"][0], s["size"][1]))


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
            # 🌟 draw 함수 무거운 래스터 라이징 오버헤드를 걷어내고 순수 메모리 고속 fill 기법으로 대체
            surface.fill(s["color"], (s["pos"][0] - camera_x, s["pos"][1], s["size"][0], s["size"][1]))



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
        self.radius += 25  # 🌟 [버그 수정] 넓어진 판정에 맞게 이펙트 확산 속도와 크기 상향
        self.alpha = max(0, self.alpha - 13)
        self.life -= 1
        if self.life <= 0:
            self.shards = []  # 수명이 다하면 리스트에서 자동 제거되도록 비웁니다.

    def draw(self, surface, camera_x):
        if self.life > 0:
            # 🌟 [극강 최적화] 매 프레임 무거운 투명 이미지를 생성하는 최악의 로직을 버리고 
            # 자연스럽게 어두워지는 직접 그리기(Direct Draw) 방식으로 변경하여 렉 원천 차단
            ratio = self.life / 15.0  # 수명에 따라 1.0 -> 0.0 으로 감소
            r = int(self.color[0] * ratio)
            g = int(self.color[1] * ratio)
            b = int(self.color[2] * ratio)
            
            draw_x = int(self.x - camera_x)
            draw_y = int(self.y)
            pygame.draw.circle(surface, (r, g, b), (draw_x, draw_y), int(self.radius), 8)


class LeafParticle:
    def __init__(self):
        self.reset(random_y=True)

    def reset(self, random_y=False):
        self.x = random.uniform(-200, SCREEN_WIDTH + 200)
        self.y = random.uniform(-100, SCREEN_HEIGHT) if random_y else -50
        self.speed_x = random.uniform(-2.2, -0.6)  # 좌측으로 부드럽게 유입
        self.speed_y = random.uniform(1.0, 2.5)    # 하강 속도
        self.size = random.uniform(4, 9)           # 벚꽃잎보다 살짝 더 큰 크기감 제공
        
        # 숲속 느낌을 살리기 위해 초록색, 올리브색, 황갈색(낙엽) 무작위 배합
        rand_val = random.random()
        if rand_val < 0.65:
            # 싱그러운 나뭇잎 색상 (초록 ~ 짙은 초록)
            self.color = (random.randint(45, 95), random.randint(115, 155), random.randint(45, 80))
        elif rand_val < 0.85:
            # 약간 시들어가는 올리브색 및 연두색
            self.color = (random.randint(110, 145), random.randint(130, 160), random.randint(50, 75))
        else:
            # 바닥에 굴러다니는 낙엽 갈색 계열
            self.color = (random.randint(155, 185), random.randint(100, 130), random.randint(45, 65))
            
        self.parallax = random.uniform(0.12, 0.35) # 입자 공간감 계수
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-1.5, 1.5) # 회전 속도

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.angle += self.rot_speed
        # 화면 경계를 벗어나면 재생성
        if self.y > SCREEN_HEIGHT + 30 or self.x < -300:
            self.reset()

    def draw(self, surface, camera_x):
        render_x = self.x - camera_x * self.parallax
        
        if render_x < -300:
            render_x += (SCREEN_WIDTH + 500)
        elif render_x > SCREEN_WIDTH + 300:
            render_x -= (SCREEN_WIDTH + 500)

        # 🌟 [최적화] 삼각함수 연산을 절반으로 감소 (cos, sin을 단 한 번씩만 계산하여 모든 좌표 구함)
        rad_long = math.radians(self.angle)
        c = math.cos(rad_long)
        s = math.sin(rad_long)
        
        # 긴 축 (나뭇잎 길이 방향)
        p1_x = render_x + c * (self.size * 1.5)
        p1_y = self.y + s * (self.size * 0.5)
        p3_x = render_x - c * (self.size * 1.5)
        p3_y = self.y - s * (self.size * 0.5)
        
        # 짧은 축 (나뭇잎 너비 방향 - cos(x+90) = -sin(x), sin(x+90) = cos(x) 수학 공식 활용)
        p2_x = render_x - s * (self.size * 0.4)
        p2_y = self.y + c * (self.size * 0.25)
        p4_x = render_x + s * (self.size * 0.4)
        p4_y = self.y - c * (self.size * 0.25)

        points = [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), (p4_x, p4_y)]
        pygame.draw.polygon(surface, self.color, points)

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
                resolved_path = resource_path(path)
                # 🌟 하늘, 먼 산 등 불투명한 뒷 레이어 2개는 알파 없는 .convert()로 불러와 비디오 연산 가중치를 50% 이상 낮춤
                if idx < 2:
                    img = pygame.image.load(resolved_path).convert()
                else:
                    img = pygame.image.load(resolved_path).convert_alpha()

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
            
            scroll_x = int(-camera_x * factor) % self.bg_width
            
            # 🌟 [최적화] 화면(0 ~ SCREEN_WIDTH) 영역에 조금이라도 걸쳐있을 때만 블릿을 수행하여 불필요한 GPU 오버헤드 차단
            # 왼쪽 이미지 그리기 검사 (우측 끝 좌표가 0보다 클 때만 그리기)
            if scroll_x > 0:
                surface.blit(img, (scroll_x - self.bg_width, self.bg_y_offset))
            
            # 오른쪽 이미지 그리기 검사 (좌측 시작 좌표가 화면 가로 크기보다 작을 때만 그리기)
            if scroll_x < SCREEN_WIDTH:
                surface.blit(img, (scroll_x, self.bg_y_offset))

class PixelGuard:
    def __init__(self):
        self.pixel_scale = SCALE_FACTOR
        self.width = 32
        self.height = 64
        self.particles = []

    def draw(self, surface, cx, cy, facing, y_offset=100):
        scaled_w = self.width * self.pixel_scale
        scaled_h = self.height * self.pixel_scale
        
        if facing == -1:
            start_x = cx - 70 - (scaled_w // 2)
        else:
            start_x = cx + 70 - (scaled_w // 2)
            
        start_y = cy - (scaled_h // 2) + y_offset

        if random.random() < 0.3:
            self.particles.append([random.randint(10, 25), self.height, random.uniform(1, 2.5)])
        
        # 메인 화면에 크기를 수치 계산하여 직배치 드로우
        for y in range(0, self.height, 2):  # 그리기 간격을 조절해 루프 연산 50% 감축
            dy = y - (self.height // 2)
            base_x = 22 - (dy * dy * 0.015) 
            noise = random.randint(-1, 1)
            x = int(base_x + noise)
            
            if 0 <= x < self.width:
                draw_x = (self.width - x) if facing == -1 else x
                rect_x = start_x + (draw_x * self.pixel_scale)
                rect_y = start_y + (y * self.pixel_scale)
                
                offset_blue = 8 if facing == -1 else -8
                pygame.draw.rect(surface, (0, 100, 255, 120), 
                                 (rect_x + (offset_blue * self.pixel_scale), rect_y, 10 * self.pixel_scale, 2 * self.pixel_scale))
                offset_cyan = 3 if facing == -1 else -3
                pygame.draw.rect(surface, (150, 255, 255, 220), 
                                 (rect_x + (offset_cyan * self.pixel_scale), rect_y, 4 * self.pixel_scale, 2 * self.pixel_scale))

        # 파티클 드로우
        for p in self.particles[:]:
            p[1] -= p[2]
            if p[1] < 0:
                self.particles.remove(p)
            else:
                px = (self.width - p[0]) if facing == -1 else p[0]
                part_x = start_x + (px * self.pixel_scale)
                part_y = start_y + (p[1] * self.pixel_scale)
                pygame.draw.rect(surface, (0, 200, 255, 255), 
                                 (part_x, part_y, self.pixel_scale, self.pixel_scale))

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
        self.base_text_surf = self.font.render(f"{self.combo_count} HIT!", True, (255, 200, 0))
        self.base_shadow_surf = self.font.render(f"{self.combo_count} HIT!", True, (0, 0, 0))


    def update(self):
        if self.timer > 0:
            self.timer -= 1
        else:
            self.active = False

    def draw(self, surface, player_rect):
        if not self.active or self.combo_count <= 1: # 2타부터 콤보 표시
            return

        # 🌟 팝 애니메이션 계산 (바이브레이션 스케일)
        scale = 1.0 + (math.sin((self.timer / 20) * 3.14) * 0.5)
        
        # 🌟 [최적화] 드로잉 루프 내에서 매 프레임 무겁게 중복 수행되던 .render()를 전부 지우고 trigger()에서 이미 만들어진 base 서페이스를 재활용하여 렉을 방지합니다.
        w, h = self.base_text_surf.get_size()
        scaled_w, scaled_h = int(w * scale), int(h * scale)
        
        text_surf = pygame.transform.scale(self.base_text_surf, (scaled_w, scaled_h))
        shadow_surf = pygame.transform.scale(self.base_shadow_surf, (scaled_w, scaled_h))

        # 플레이어 머리 위쪽 약간 오른쪽에 배치
        pos_x = player_rect.centerx + 60
        pos_y = player_rect.bottom - 300 - (scaled_h // 2)

        surface.blit(shadow_surf, (pos_x + 4, pos_y + 4)) # 그림자 먼저
        surface.blit(text_surf, (pos_x, pos_y))

LIGHT_ATK_TOTAL_FRAMES = 18
HEAVY_ATK_TOTAL_FRAMES = 26

def load_sprite_sheet(filename, frame_count):
    try:
        # 🌟 [변경] PyInstaller 가상 경로가 적용된 파일 주소로 매핑
        resolved_path = resource_path(filename)
        sheet = pygame.image.load(resolved_path).convert_alpha()
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
        self.dash_invul_timer = 0 # 🌟 [추가] 백대쉬 무적 시간 타이머 추가
        self.ghost_spawn_tick = 0 # 🌟 [추가] 잔상 스폰 동기화용 프레임 타이머
        self.god_mode = False  # 🌟 [추가] 무적 모드 기본값은 꺼짐
        self.is_guarding = False # 🌟 [추가] 가드 상태 변수

        # 🌟 [추가] 체력 설정
        self.hp = hp
        self.max_hp = hp
        self.display_hp = hp # 🌟 [신규 추가] 피격 시 천천히 깎이는 잔상용 체력 데이터
        
        # 🌟 [최적화] 전역 캐시로부터 조립이 끝난 스프라이트 주소만 초고속으로 참조
        self.animations = PRELOADED_ANIMATIONS.get(self.char_id, {}).get(self.is_boss, {})
        if not self.animations:
            self.animations = {}
            data = CHAR_DATA.get(char_id, CHAR_DATA["A1"])
            for state, (suffix, count, hit_idx) in data.items(): 
                path = os.path.join("dd", "assets", f"{self.char_id}_{suffix}.png")
                frames = load_sprite_sheet(path, count)
                if self.is_boss:
                    tinted_frames = []
                    for frame in frames:
                        new_frame = frame.copy()
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
        self.is_moving = False

    def take_damage(self, amount, attacker, attack_type): # attack_type 인자 추가
        global KO_CINEMATIC_TIMER, KO_TRIGGERED # 🌟 [구문 에러 해결] 전역 네임스페이스 컴파일 선언을 함수 시작부에 먼저 안전하게 바인딩합니다.
        if self.state == "DEATH": return False

        # 🌟 무적 시간이 남아 있다면 피격 및 가드 연산을 아예 무시하고 탈출 (완전 회피)
        if getattr(self, "dash_invul_timer", 0) > 0:
            print(f"✨ {self.char_id} DODGED with Backdash Invincibility!")
            play_sound("cancel")             # 🌟 캔슬 사운드(cancel.wav)로 변경 완료!
            self.cancel_ui_timer = 20        
            self.dodge_flag = True           
            return False

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
            
            # 🌟 [신규 추가] 데미지가 성공적으로 적용되었을 때 데미지 폰트 생성 후 글로벌 전역 리스트에 등재
            is_crit = (attack_type == "HEAVY" and not is_guarding)
            ACTIVE_DAMAGE_NUMBERS.append(FloatingDamage(self.hurtbox.centerx, self.hurtbox.top, final_damage, is_crit))
        else:
            print(f"✨ {self.char_id} is INVINCIBLE!") 
            # 🌟 무적 상태(F1/F2 활성화)일 때는 0 데미지 팝업
            ACTIVE_DAMAGE_NUMBERS.append(FloatingDamage(self.hurtbox.centerx, self.hurtbox.top, 0, False))
            
        # 🌟 타격 시 캐릭터 흰색 플래시 타이머 작동 (일반 피격 시 6프레임 작동)
        if not is_guarding:
            self.flash_timer = 6
    
        self.hit_stun_timer = final_stun
        self.state = "HIT"
        self.timer = 0 
        self.is_attacking = False
        self.hitbox = pygame.Rect(0, 0, 0, 0) # 🌟 [버그 수정] 피격 즉시 공격 판정 삭제
        
        # 🌟 [버그 수정] 피격 즉시 이미지를 갱신하여 직전 공격 모션이 1프레임 남는 글리치 방지
        frames = self.animations.get("HIT", self.animations["IDLE"])
        self.image = frames[0]
        
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
                
                # 🌟 [신규 추가] 승패를 결정하는 치명타(Fatal Blow) 성립 시 드라마틱 KO 슬로우 모션 연출 기동
                if not KO_TRIGGERED:
                    KO_CINEMATIC_TIMER = 80  # 약 1.3초 동안 시간이 극한으로 지연됨
                    KO_TRIGGERED = True
                    play_sound("ko")         # 🌟 [신규 추가] 구하신 KO 사운드 오디오 즉시 격발!
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
        if self.state == "DEATH": return False
        
        # 🌟 [버그 수정] 공격 중 캔슬 대쉬는 일반 대쉬 쿨타임을 무시하도록 분리
        if self.is_attacking:
            if self.dash_charges > 0:
                print("✨ 콤보 캔슬 대쉬! 콤보 유지시간 확장!")
                self.dash_charges -= 1
                self.is_cancel_dash = True 
                self.combo_timer = 120
                self.cancel_ui_timer = 30 
                self.used_cancel_in_combo = True # 이번 콤보에선 게이지 획득 불가
                play_sound("cancel")
            else:
                return False
        else:
            # 일반 대쉬는 쿨타임이 없을 때만 작동
            if self.dash_cooldown_timer > 0:
                return False
            self.is_cancel_dash = False # 그냥 대쉬로 설정
            
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
            self.dash_invul_timer = 0 # 전진 대쉬는 무적 판정 없음
        else:
            self.vel_x = -current_dash_speed if self.facing_right else current_dash_speed
            self.dash_invul_timer = 8 # 🌟 백대쉬 시작 시 첫 8프레임 동안 무적 판정 부여
            return True
        return False
    
    def handle_attack(self, attack_type):
        if self.state == "DEATH": return False  # 🌟 [신규 추가] 사망 연출 도중 공격 차단
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
                friction = 1.0  # 대쉬 중에는 관성 속도 100% 보존
        elif self.state == "HIT":
                friction = 0.98  # 피격 넉백 상황 시에는 자연스럽게 밀려나도록 마찰력 최소화 (넉백 물리 보장!)
        else:
            if not self.is_grounded:
                friction = 0.95  # 점프 공중 상태에서는 답답하지 않게 비행 관성 유지
            else:
                    # 🌟 [변경] 이동 명령을 받는 중일 때는 마찰 없이 쾌적하게 걷고(0.92), 키를 떼면(False) 즉각 브레이크를 잡듯이 제동 마찰(0.15)을 가함
                friction = 0.92 if getattr(self, "is_moving", False) else 0.15

        self.vel_x *= friction
        if abs(self.vel_x) < 0.1: 
            self.vel_x = 0

        self.rect.x += self.vel_x

        

    def update(self):
        self.apply_physics()
        
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_step = 0 # 시간이 다 지나면 콤보 초기화
                self.used_cancel_in_combo = False

        # 🌟 백대쉬 무적 프레임 타이머 감소 연산 추가
        if getattr(self, "dash_invul_timer", 0) > 0:
            self.dash_invul_timer -= 1

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

        # 🌟 [신규 추가] 잔상 체력이 실제 체력 값까지 서서히 추격하며 감소
        if hasattr(self, 'display_hp'):
            if self.display_hp > self.hp:
                self.display_hp -= (self.display_hp - self.hp) * 0.05  # 매 프레임 조금씩 추격
                if self.display_hp - self.hp < 0.2:
                    self.display_hp = self.hp
            else:
                self.display_hp = self.hp

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
                self.state = "IDLE" 
                self.vel_x = 0
                self.is_cancel_dash = False 
                
                # 🌟 [잔상 버그 완벽 해결 3] 대쉬가 끝날 때도 프레임을 안전하게 초기화
                self.frame_index = 0                      
                self.image = self.animations["IDLE"][0]   
                
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
                    whiff_penalty = 20 if atk_type == "LIGHT" else 35
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
                self.frame_index = 0
                self.image = self.animations["IDLE"][0]
            
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
            self.frame_index = 0  # 🌟 [잔상 버그 완벽 해결 2] 후딜레이 중에도 프레임 인덱스를 확실하게 0으로 고정
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
            # 🌟 [메모리 누수 해결 1] 매 프레임 flip()으로 이미지를 무한 생성하던 치명적 누수 차단
            flip_key = (self.char_id, self.state, self.frame_index, self.is_boss)
            if flip_key not in FLIP_CACHE:
                FLIP_CACHE[flip_key] = pygame.transform.flip(self.image, True, False)
            self.image = FLIP_CACHE[flip_key]

        self.hurtbox = pygame.Rect(
            self.rect.centerx - self.hurtbox_w // 2, 
            self.rect.bottom - self.hurtbox_h, 
            self.hurtbox_w, 
            self.hurtbox_h
        )

        is_active = (self.state == "DASH" or self.state == "HIT" or self.is_attacking)
        if is_active or (self.is_boss and self.state != "DEATH"):
            tick = 3 if self.is_boss else 6 
            self.ghost_spawn_tick += 1 # 🌟 동기화 타이머 갱신
            if self.ghost_spawn_tick % tick == 0: # 🌟 시스템 임의 시간이 아닌 60프레임 동기화 연산으로 완벽 고정
                # 🌟 [버그 수정] 상태값을 키로 사용하여 잔상이 엉뚱하게 남는 현상 완벽 차단
                cache_key = (self.char_id, self.state, self.frame_index, self.facing_right, self.is_boss)
                if self.is_boss:
                    ghost_img = get_ghost_red(self.image, cache_key)
                    self.ghosts.append([ghost_img, self.rect.copy(), 150]) 
                else:
                    ghost_img = get_ghost_blue(self.image, cache_key) 
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
            if abs(dist) < 450 and opponent.state != "DEATH" and opponent.hp > 0:
                opponent.state = "HIT"
                
                # 🌟 [버그 수정] 버스트에 맞았을 때 공격 모션이 1프레임 굳는 현상 방지 (즉시 피격 갱신)
                opponent.timer = 0            
                opponent.frame_index = 0
                frames = opponent.animations.get("HIT", opponent.animations["IDLE"])
                opponent.image = frames[0]
                
                opponent.hit_stun_timer = 40  
                opponent.vel_x = 18 if dist > 0 else -18  
                opponent.vel_y = -8                       
                opponent.is_attacking = False
                opponent.hitbox = pygame.Rect(0, 0, 0, 0)
                
                active_explosions.append(HitSpark(opponent.hurtbox.centerx, opponent.hurtbox.centery, is_heavy=True))
                print(f"💥 {self.char_id} 로망 캔슬! 상대방을 밀쳐냈습니다.")
            return True
        return False

class Enemy(Entity):
    def __init__(self, x, y, char_id, hp, is_boss=False):
        super().__init__(x, y, char_id, hp, is_boss)
        self.ai_timer = 0
        self.ai_state = "IDLE"
        self.decision_timer = 0
        self.is_boss = is_boss

        self.transform_timer = 0
        self.is_transforming = False
        self.pre_transform_timer = 0

        self.ai_tick_timer = 0
        self.can_heavy = ("ATK2" in self.animations) or ("ATK3" in self.animations)

        # 🌟 [AI 최적화] 타격 거리를 매번 실시간으로 정수 나눗셈/사칙연산하지 않도록 캐릭터 생성 시점에 사전 캐싱 처리
        self.reaches = {}
        for atk, cfg in HITBOX_CONFIG.items():
            self.reaches[atk] = (cfg["offset"] + cfg["w"]) * SCALE_FACTOR + 30 # 30 = 플레이어 피격박스(60) // 2

    def change_form(self, new_id):
        old_bottom_pos = self.rect.midbottom 
        self.char_id = new_id
        
        self.animations = PRELOADED_ANIMATIONS[new_id][self.is_boss]

        self.state = "IDLE"
        self.image = self.animations["IDLE"][0]
        self.rect = self.image.get_rect(midbottom=old_bottom_pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        
        if new_id == "C1":
            self.hurtbox_w, self.hurtbox_h = 60, 80
        elif new_id == "A2":
            self.hurtbox_w, self.hurtbox_h = 60, 80
            
        self.can_heavy = ("ATK2" in self.animations) or ("ATK3" in self.animations)
        
        # 🌟 [AI 최적화] 캐릭터 변신 및 기교가 변경되는 시점에도 타격 거리 상수 풀을 즉각 재갱신하여 메모리에 등록합니다.
        self.reaches = {}
        for atk, cfg in HITBOX_CONFIG.items():
            self.reaches[atk] = (cfg["offset"] + cfg["w"]) * SCALE_FACTOR + 30


    def update_ai(self, target, active_explosions):
        # 1. 🌟 [AI 최적화 1순위] 기절(HIT)/사망/후딜 상태일 때는 복잡한 논리 회로를 훑기 전에 조기 탈출하여 무의미한 CPU 소비를 완벽히 틀어막습니다.
        if self.state in ["DEATH", "HIT", "RECOVERY"] and not getattr(self, 'is_transforming', False):
            # 조기 차단 중 유일한 예외: 피격 도중 기(자원)가 있을 때의 'AI 버스트 카운터 로망 캔슬' 계산만 허용
            if self.state == "HIT" and self.dash_charges >= 1:
                if target.state == "DASH" and getattr(target, 'is_cancel_dash', False):
                    if random.random() < 0.85:
                        self.trigger_roman_cancel(target, active_explosions)
                        return
                elif target.combo_step >= 3:
                    if random.random() < 0.008:
                        self.trigger_roman_cancel(target, active_explosions)
                        return
            return

        # 2. 🌟 [AI 최적화 2순위] AI 논리 탐색 틱 주기를 60Hz에서 20Hz(3프레임당 1회)로 분리하여 CPU 연산 부하를 70% 가량 감축시킵니다.
        self.ai_tick_timer += 1
        if self.ai_tick_timer % 3 != 0:
            return

        # [상황 예외] 플레이어가 완전히 사망했을 경우 AI 동작 정지
        if target.state == "DEATH":
            self.vel_x = 0
            self.is_guarding = False
            self.state = "IDLE"
            return
        
        # 3. 보스 변신 이펙트 및 연출 로직 제어
        if self.is_boss:
            if not self.is_transforming:
                self.transform_timer += 1
                if self.transform_timer >= 480: # 8초 주기
                    self.is_transforming = True
                    self.pre_transform_timer = 60
                    self.state = "IDLE"
                    self.vel_x = 0
                    return

            if self.is_transforming:
                self.pre_transform_timer -= 1
                self.vel_x = 0
                if self.state == "HIT":
                    self.state = "IDLE" 
                if self.pre_transform_timer <= 0:
                    new_form = "C1" if self.char_id == "A2" else "A2"
                    self.change_form(new_form)
                    self.is_transforming = False
                    self.transform_timer = 0
                    
                    dist = target.rect.centerx - self.rect.centerx
                    target.vel_x = 15 if dist > 0 else -15
                    target.hit_stun_timer = 10
                    target.state = "HIT"
                return

        if not self.is_grounded:
            return

        dist = target.rect.centerx - self.rect.centerx
        abs_dist = abs(dist)
        
        # 🌟 [AI 최적화] 전역 딕셔너리 무차별 문자열 조회를 소거하고, 캐싱해 둔 Boolean(self.can_heavy) 상수로 초고속 치환
        counter_atk = "HEAVY" if self.can_heavy else "LIGHT"

        # 🌟 [AI 최적화] 실시간으로 매번 계산하던 물리 범위 산출 공식을 사전 빌딩된 범위 해시 맵(self.reaches) 즉각 조회로 대체
        counter_reach = self.reaches[counter_atk]

        cfg_id = "BOSS" if self.is_boss else self.char_id
        cfg = AI_BRAIN_CONFIG.get(cfg_id, AI_BRAIN_CONFIG["B1"]) 

        # 점프해 오는 상대에 대한 공중 격추 카운터 심리전
        if abs_dist < counter_reach and not target.is_grounded:
            if self.decision_timer <= 0 and not self.is_attacking and self.state not in ["DASH"]:
                rand_val = random.random()
                if rand_val < 0.35:
                    if self.dash_cooldown_timer <= 0:
                        self.trigger_dash(is_forward=False)
                        self.add_to_buffer(counter_atk)
                        self.decision_timer = 15
                        return
                    else:
                        self.vel_x = -WALK_SPEED if dist > 0 else WALK_SPEED
                        self.decision_timer = 12
                        return
                elif rand_val < 0.70:
                    if self.dash_cooldown_timer <= 0:
                        self.trigger_dash(is_forward=True)
                        self.add_to_buffer(counter_atk)
                        self.decision_timer = 15
                        return
                    else:
                        self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                        self.decision_timer = 12
                        return
                elif rand_val < 0.85:
                    self.vel_x = -WALK_SPEED if dist > 0 else WALK_SPEED
                    self.decision_timer = 12
                    return
                else:
                    self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                    self.decision_timer = 12
                    return

        if self.state in ["IDLE", "RUN"]:
            self.facing_right = dist > 0

        # 철벽 방어 제어
        if self.is_guarding:
            if not target.is_attacking:
                self.is_guarding = False 
            else:
                return

        is_target_vulnerable = (target.state == "RECOVERY")
        is_target_whiffing = (target.is_attacking and not target.has_hit)
        
        # 🌟 [AI 최적화] planned_atk 의사 결정 로직에 캐싱 상수 참조 구조 도입
        if self.char_id == "C1":
            rand = random.random()
            if rand < 0.4: planned_atk = "LIGHT"
            elif rand < 0.7: planned_atk = "REVERSE"
            else: planned_atk = "HEAVY"
        else:
            planned_atk = "LIGHT" if (not self.can_heavy or random.random() < 0.7) else "HEAVY"
            
        attack_reach = self.reaches[planned_atk]
        self.debug_reach = attack_reach 

        if self.is_attacking:
            if self.has_hit and self.dash_charges > 0 and random.random() < 0.7: 
                state_info = CHAR_DATA[self.char_id].get(self.state)
                if state_info and state_info[2] is not None:
                    atk_type = getattr(self, 'current_atk_type', "LIGHT")
                    total_frames = LIGHT_ATK_TOTAL_FRAMES if atk_type == "LIGHT" else HEAVY_ATK_TOTAL_FRAMES
                    hit_end_f = (state_info[2] + 1) * (total_frames / state_info[1])
                    if self.timer > hit_end_f:
                        self.trigger_dash(is_forward=True)
                        self.decision_timer = 0 
            return 

        if self.state == "DASH":
            return

        # ====================================================================
        # 🛡️ [우선순위 1] 방어 및 회피 (상대가 공격 중일 때)
        # ====================================================================
        if target.is_attacking and abs_dist < attack_reach * 1.5:
            player_atk_type = getattr(target, 'current_atk_type', "LIGHT")
            if player_atk_type == "LIGHT" and attack_reach * 0.8 < abs_dist < attack_reach * 1.3:
                if random.random() < 0.40:
                    self.vel_x = -WALK_SPEED if dist > 0 else WALK_SPEED
                    self.decision_timer = 10
                    return
            
            react_prob = cfg.get("react_prob", 0.50)
            if self.decision_timer <= 0 or random.random() < react_prob:
                player_atk_type = getattr(target, 'current_atk_type', "LIGHT")
                is_player_facing_me = (dist > 0 and not target.facing_right) or (dist < 0 and target.facing_right)

                if player_atk_type == "HEAVY" and is_player_facing_me and self.dash_cooldown_timer <= 0:
                    if abs_dist < 380:
                        if random.random() < 0.8:
                            self.trigger_dash(is_forward=True)
                            self.decision_timer = 20
                            return

                if self.dash_cooldown_timer <= 0 and random.random() < cfg["dash_back_prob"]: 
                    self.trigger_dash(is_forward=False)
                    self.decision_timer = 15
                    return
                
                if target.state == "ATK1" and random.random() < cfg["back_catch_prob"]: 
                    self.vel_y = JUMP_FORCE 
                    self.vel_x = (DASH_SPEED * 1.3) if self.facing_right else (-DASH_SPEED * 1.3)
                    self.decision_timer = 30 
                    play_sound("jump") 
                    return
                
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
                play_sound("jump")
            else:
                self.vel_x = WALK_SPEED if dist > 0 else -WALK_SPEED
                self.decision_timer = 5 

        else: 
            self.handle_attack(planned_atk)
            self.decision_timer = 20

    def update(self):
        # 🌟 [신규 추가] AI도 이동 명령이 끊기면 미끄러짐 없이 즉각 멈출 수 있도록, 속도를 역추적해 이동 여부를 물리 공식에 연동
        self.is_moving = (abs(self.vel_x) > WALK_SPEED * 0.5)
        super().update()

FREEZE_TIMER = False  

def main():
    # 🌟 [전역 스코프 등록] 데미지 폰트 캐시 변수 추가 바인딩
    global CAMERA_X, GAME_STATE, GLOBAL_VOLUME, SHOW_HITBOXES, PRELOADED_ANIMATIONS, FLIP_CACHE, FREEZE_TIMER, KO_CINEMATIC_TIMER, KO_TRIGGERED
    global DAMAGE_FONT_NORMAL, DAMAGE_FONT_CRIT

    pygame.mixer.pre_init(44100, -16, 2, 512) 
    pygame.init()
    pygame.mixer.set_num_channels(32)

    # 🌟 [프레임 드랍 차단] 게임 시동 단계에서 대용량 폰트 리소스를 메모리에 안전하게 미리 바인딩합니다.
    DAMAGE_FONT_NORMAL = pygame.font.SysFont("impact", 30)
    DAMAGE_FONT_CRIT = pygame.font.SysFont("impact", 42)


    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Last Stand")

    # =================================================================
    # 🌟 [렉 해결 핵심] 로딩 화면 UI 생성 및 진행률 계산기
    # =================================================================
    loading_font = pygame.font.SysFont("impact", 55, italic=True)
    info_font = pygame.font.SysFont("arial", 22, bold=True)
    
    def draw_loading_screen(progress, current_task):
        pygame.event.pump() # OS 응답 없음(프리징) 방지
        screen.fill((12, 17, 34))
        
        title_surf = loading_font.render("INITIALIZING...", True, (0, 245, 255))
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        
        task_surf = info_font.render(current_task, True, (200, 200, 200))
        screen.blit(task_surf, (SCREEN_WIDTH // 2 - task_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        
        bar_width = 500
        bar_height = 20
        pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH//2 - bar_width//2, SCREEN_HEIGHT//2 + 70, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 100), (SCREEN_WIDTH//2 - bar_width//2, SCREEN_HEIGHT//2 + 70, bar_width * progress, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (SCREEN_WIDTH//2 - bar_width//2, SCREEN_HEIGHT//2 + 70, bar_width, bar_height), 2)
        
        pygame.display.flip()

    total_tasks = len(CHAR_DATA) + 2 # 캐릭터 로딩들 + 사운드 로딩 + 배경 로딩
    task_count = 0

    # 1. 캐릭터 애니메이션 로딩 및 1라운드 렉(FLIP) 사전 연산
    for char_id, data in CHAR_DATA.items():
        draw_loading_screen(task_count / total_tasks, f"Loading Character Data: [ {char_id} ]")
        PRELOADED_ANIMATIONS[char_id] = {False: {}, True: {}}
        
        for state, (suffix, count, hit_idx) in data.items():
            path = os.path.join("dd", "assets", f"{char_id}_{suffix}.png")
            frames = load_sprite_sheet(path, count)
            PRELOADED_ANIMATIONS[char_id][False][state] = frames
            
            # 🌟 [극강 최적화] 1라운드에서 캐릭터가 처음 왼쪽을 볼 때 생기는 심각한 렉을 차단!
            # 로딩하는 김에 좌우 반전 이미지도 미리 전부 구워서 FLIP_CACHE에 넣어버립니다.
            for i, f in enumerate(frames):
                FLIP_CACHE[(char_id, state, i, False)] = pygame.transform.flip(f, True, False)
            
            tinted_frames = []
            for i, frame in enumerate(frames):
                new_frame = frame.copy()
                new_frame.fill((255, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
                tinted_frames.append(new_frame)
                
                # 보스용 붉은색 필터가 씌워진 좌우 반전 이미지도 미리 캐싱
                FLIP_CACHE[(char_id, state, i, True)] = pygame.transform.flip(new_frame, True, False)
                
            PRELOADED_ANIMATIONS[char_id][True][state] = tinted_frames
            
        task_count += 1
    # =================================================================

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
        "miss": "miss.wav",
        "bgm": "background_music.wav",
        "ko": "ko.wav"             # 🌟 [신규 추가] 구하신 KO 사운드 파일(ko.wav)을 시스템에 영구 등록합니다.
    }
    
    # 콤보 사운드 (1~10) 일괄 등록
    for i in range(1, 11):
        sound_files[f"combo_{i}"] = f"combo {i}.wav"

    for key, filename in sound_files.items():
        try:
            # 🌟 [변경] 효과음 사운드 데이터도 가상 폴더 내부 주소로 변환
            resolved_sound_path = resource_path(os.path.join(sound_path, filename))
            SOUNDS[key] = pygame.mixer.Sound(resolved_sound_path)
        except Exception as e:
            print(f"⚠️ 사운드 로드 실패 ({filename}): {e}")

            SOUNDS[key] = None

    # 🌟 [추가] 오디오 로드 직후 최초 볼륨(0.5) 크기를 모든 사운드에 주입해 줍니다.
    apply_volume()
    
    # 중복 생성 구문 소거 완료
    clock = pygame.time.Clock()
    
    # 3. 무거운 패럴랙스 배경 로딩 단계 표출
    task_count += 1
    draw_loading_screen(task_count / total_tasks, "Loading Environment & Parallax Layers...")
    
    # 🌟 [추가] 패럴랙스 배경 인스턴스 생성
    background = ParallaxBackground(SCREEN_WIDTH, SCREEN_HEIGHT)

    
    font_small = pygame.font.SysFont("arial", 20, bold=True)
    CACHED_DASH_TEXTS = {i: font_small.render(f"DASH: {i}", True, (255, 255, 255)) for i in range(4)} # 0~3까지 미리 생성
    CACHED_TEXT_EVADE = font_small.render("EVADE!", True, (0, 255, 100))
    CACHED_TEXT_CANCEL = font_small.render("CANCEL!", True, (0, 255, 255))
    font_large = pygame.font.SysFont("arial", 40, bold=True)
    font_huge = pygame.font.SysFont("impact", 120, italic=True) 
    font_dead = pygame.font.SysFont("impact", 130)                 
    font_clear = pygame.font.SysFont("impact", 110, italic=True)   
    font_timer = pygame.font.SysFont("impact", 80) # 🌟 [추가] 타이머 전용 아주 큰 폰트

    # 🌟 [극강 최적화] 프레임 드랍을 원천 차단하기 위해 연출에 필요한 무거운 자원들을 루프 진입 전 비디오 메모리에 사전 확보합니다.
    ko_red_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
    ko_red_overlay.fill((160, 10, 10))
    ko_red_overlay.set_alpha(70) # 매 프레임 알파값 변경 연산을 수행하지 않도록 고정 설정
    
    ko_white_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
    ko_white_overlay.fill((255, 255, 255))
    ko_white_overlay.set_alpha(70)
    
    font_ko = pygame.font.SysFont("impact", 170, italic=True)
    ko_text_base = font_ko.render("K.O.", True, (255, 20, 20)).convert_alpha() # 텍스트 선행 이미지 변환화
    ko_shadow_base = font_ko.render("K.O.", True, (0, 0, 0)).convert_alpha()
    ko_base_w, ko_base_h = ko_text_base.get_size()

    # 🌟 [메모리 누수 해결 3] 변하지 않는 고정 UI 텍스트를 루프 밖에서 딱 1번만 생성
    vs_text_surf = font_large.render("VS", True, (255, 200, 0))
    p1_name_surf = font_small.render("PLAYER 1", True, (255, 255, 255))
    p2_name_surf = font_small.render("PLAYER 2 (AI)", True, (255, 255, 255))

    current_stage_idx = 0

    stage_info = STAGE_SEQUENCE[current_stage_idx]
    countdown_timer = 240

    last_timer_val = -1
    cached_timer_surf = None
    last_stage_idx_cached = -1
    cached_stage_surf = None
    fps_update_timer = 0
    cached_fps_surf = None

    match_timer = 60.0  # 🌟 [추가] 라운드 시간 (60초)
    time_over = False    # 🌟 [추가] 시간 종료 여부 플래그

    transition_state = "IDLE"          # "IDLE" (대기), "WIPE_IN" (화면 가려짐), "WIPE_OUT" (화면 걷힘)
    transition_x = -SCREEN_WIDTH - 400 # 트랜지션 막대의 가로 위치 초기값
    transition_speed = 20              # 연출 처리 속도 (1프레임당 이동 픽셀)


    active_explosions = []
    death_delay_timer = 0 # 보스 사망 후 화면 멈춤 및 폭발 연출용
    game_over_alpha = 0   # 🌟 플레이어 사망 시 화면 어두워짐 효과를 제어할 변수를 추가합니다.
    game_cleared = False  # 🌟 게임 클리어 상태 플래그를 추가합니다

    game_clear_alpha = 0
    post_clear_timer = 150  # 클리어 문구 노출 대기 시간 (60프레임 = 1초, 약 2.5초 대기)
    post_death_timer = 150  # 사망 DEAD 문구 완료 후 대기 시간 (약 2.5초 대기)

    player = Entity(200, GROUND_Y, "A1", PLAYER_MAX_HP)
    
    # 🌟 [변경] 나뭇잎 35개 목록 생성
    ambient_particles = [LeafParticle() for _ in range(10)]

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
                            match_timer = 60.0        # 🌟 시작 시 라운드 시간 60초 초기화
                            time_over = False          # 🌟 시작 시 시간 초과 여부 초기화
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

        # 🌟 [신규 추가] 일시정지(PAUSE) 상태 UI 및 조작 로직
        elif GAME_STATE == "PAUSE":
            # 기존 인게임 스크린에 가볍게 반투명 어두운 레이어 씌우기
            dim_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            dim_overlay.fill((0, 0, 0))
            dim_overlay.set_alpha(140)
            screen.blit(dim_overlay, (0, 0))

            title_font = pygame.font.SysFont("impact", 65, italic=True)
            menu_font = pygame.font.SysFont("arial", 26, bold=True)

            title_surf = title_font.render("GAME PAUSED", True, (0, 245, 255))
            screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 170))

            pause_options = ["RESUME GAME", "SETTINGS MENU", "RETURN TO MAIN MENU"]
            for idx, opt_text in enumerate(pause_options):
                color = (255, 205, 0) if idx == pause_menu_index else (150, 150, 150)
                opt_surf = menu_font.render(opt_text, True, color)
                screen.blit(opt_surf, (SCREEN_WIDTH // 2 - opt_surf.get_width() // 2, 330 + idx * 60))

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        GAME_STATE = "GAMEPLAY"
                    elif event.key == pygame.K_UP:
                        pause_menu_index = (pause_menu_index - 1) % len(pause_options)
                    elif event.key == pygame.K_DOWN:
                        pause_menu_index = (pause_menu_index + 1) % len(pause_options)
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if pause_menu_index == 0:
                            GAME_STATE = "GAMEPLAY"
                        elif pause_menu_index == 1:
                            GAME_STATE = "SETTINGS"
                            settings_index = 0
                        elif pause_menu_index == 2:
                            # 게임 리셋 후 메인 메뉴로 강제 탈출
                            GAME_STATE = "MENU"
                            KO_CINEMATIC_TIMER = 0
                            KO_TRIGGERED = False
                            ACTIVE_DAMAGE_NUMBERS.clear()
                            transition_state = "IDLE"                  # 🌟 추가
                            transition_x = -SCREEN_WIDTH - 400         # 🌟 추가
                            current_stage_idx = 0
                            stage_info = STAGE_SEQUENCE[current_stage_idx]
                            
                            match_timer = 60.0        # 🌟 메뉴로 나갈 때 시간 초기화
                            time_over = False          # 🌟 메뉴로 나갈 때 타임오버 플래그 초기화

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
                            if "bgm" in SOUNDS and SOUNDS["bgm"]: SOUNDS["bgm"].stop() # 🌟 [추가] 메인메뉴 강제 탈출 시 BGM 정지
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
            continue

        # (이하 기존 카운트다운 및 인게임 로직이 전개됩니다)
        if countdown_timer > 0:
            # 🌟 텍스트가 바뀌는 정확한 프레임에 음성을 1번씩만 재생
            if countdown_timer == 240: play_sound("3")
            elif countdown_timer == 180: play_sound("2")
            elif countdown_timer == 120: play_sound("1")
            elif countdown_timer == 60: play_sound("fight")
            
            countdown_timer -= 1 # 🌟 [추가] 카운트다운 줄이기
            if countdown_timer == 0:
                if "bgm" in SOUNDS and SOUNDS["bgm"]:
                    SOUNDS["bgm"].play(loops=-1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                # 🌟 [신규 추가] 인게임 중 ESC 입력을 인식하여 일시정지 상태로 전환
                if GAME_STATE == "GAMEPLAY" and event.key == pygame.K_ESCAPE:
                    GAME_STATE = "PAUSE"
                    pause_menu_index = 0
                    continue
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

                if event.key == pygame.K_F6:
                    FREEZE_TIMER = not FREEZE_TIMER
                    state_str = "PAUSED (무한 시간)" if FREEZE_TIMER else "RESUMED (시간 흐름)"
                    print(f"⏱️ DEBUG: TIMER {state_str}!")

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
                        if "bgm" in SOUNDS and SOUNDS["bgm"]: SOUNDS["bgm"].stop() # 🌟 [추가] 기존 BGM 정지

                        # 카메라 및 콤보 텍스트 등 초기화
                        CAMERA_X = 0 
                        player.combo_step = 0
                        p1_combo_display.active = False
                        p2_combo_display.active = False
                        KO_CINEMATIC_TIMER = 0
                        KO_TRIGGERED = False
                        ACTIVE_DAMAGE_NUMBERS.clear()
                        print(f"⏩ STAGE SKIPPED! NEXT STAGE: {next_stage['name']}")
                    else:
                        print("⏩ ALREADY AT THE LAST STAGE (OR CLEARED)!")

                # 🌟 [추가] 카운트다운이 끝난 상태에서만 플레이어 조작 가능
                if countdown_timer <= 0:
                    if player.state == "DEATH": # 🌟 [신규 추가] 사망 중엔 단발성 단축 조작 차단
                        continue
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
                    else:
                        # 🌟 [버그 수정] 이동키 외의 키(공격, 점프 등)를 누르면 대쉬 더블탭 연결을 강제 끊음
                        last_key_pressed = None

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

        # 🌟 함수 상단에서 global 정의가 완료되었으므로 불필요하고 에러를 유발하는 로컬 인라인 global 선언을 걷어냅니다.
        if KO_TRIGGERED and KO_CINEMATIC_TIMER > 0:
            KO_CINEMATIC_TIMER -= 1

        if hitstop_timer > 0:
            hitstop_timer -= 1
        else:
            player.is_guarding = False
            
            # 🌟 [신규 추가] 시간 제한 로직
            if countdown_timer <= 0 and not time_over:
                if not FREEZE_TIMER:          # 🌟 F6키로 시간이 멈춘 상태가 아닐 때만 초가 줄어듭니다!
                    match_timer -= 1/FPS  # 매 프레임 1/60초씩 감소
                if match_timer <= 0:
                    match_timer = 0
                    time_over = True
                    
                    # 🌟 [판정 승] 체력이 더 낮은 사람이 사망
                    if player.hp <= enemy.hp:
                        player.hp = 0
                        player.state = "DEATH"
                        player.timer = 0
                        print("⏰ TIME OVER: Player 1 loses by HP!")
                    else:
                        enemy.hp = 0
                        enemy.state = "DEATH"
                        enemy.timer = 0
                        print("⏰ TIME OVER: Enemy loses by HP!")

            # 🌟 [수정] 시간이 종료(time_over)되었다면 조작 및 AI를 완전히 정지시킴
            if countdown_timer <= 0 and not time_over:
                if player.state != "DEATH":  # 🌟 [병합 수정] 캐릭터가 완벽히 살아있을 때만 모든 방향키 이동 감지
                    if player.is_grounded and not player.is_attacking and player.state not in ["HIT", "RECOVERY", "DASH"]:
                        if (player.facing_right and keys[KEY_BINDINGS["LEFT"]]) or (not player.facing_right and keys[KEY_BINDINGS["RIGHT"]]):
                            player.is_guarding = True

                # 🌟 연속 걷기 제어 로직을 사망 차단 구문 안으로 통합하여 미끄러짐 현상을 완벽히 방지합니다.
                    if player.state != "DASH":
                        if not player.is_attacking and player.state not in ["HIT", "RECOVERY"]: 
                            if keys[KEY_BINDINGS["LEFT"]]: 
                                player.vel_x = -BACK_WALK_SPEED if player.facing_right else -WALK_SPEED
                                player.is_moving = True  
                            elif keys[KEY_BINDINGS["RIGHT"]]: 
                                player.vel_x = WALK_SPEED if player.facing_right else BACK_WALK_SPEED
                                player.is_moving = True  
                            else: 
                                player.is_moving = False 
                        else:
                            # 🌟 [버그 수정] 공격/피격/후딜 중에는 강제로 이동 상태를 꺼서 미끄러짐 방지
                            player.is_moving = False
                
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
            
            # 🌟 [슬로우모션 최적화] 렌더링 주사율은 60FPS로 유지하여 부드러운 파티클 및 화면 진동을 보장하되, 캐릭터 물리/스프라이트 연산만 1/5 속도로 정교하게 낮춥니다.
            if KO_TRIGGERED and KO_CINEMATIC_TIMER > 0:
                if pygame.time.get_ticks() % 5 == 0:
                    all_sprites.update()
            else:
                all_sprites.update()
            
            # 🌟 [신규 추가] 화면 내 데미지 폰트 수식 업데이트 및 소멸된 연출 데이터 청소
            for dmg in ACTIVE_DAMAGE_NUMBERS:
                dmg.update()
            ACTIVE_DAMAGE_NUMBERS[:] = [d for d in ACTIVE_DAMAGE_NUMBERS if d.life > 0]

            if transition_state == "WIPE_IN":
                transition_x += transition_speed
                if transition_x >= 0:
                    transition_x = 0
                    transition_state = "WIPE_OUT"
                
                # --- [장막이 화면을 채웠을 때 실행] 다음 스테이지 데이터 로드 ---
                    current_stage_idx += 1
                    next_stage = STAGE_SEQUENCE[current_stage_idx]
                
                    enemy.kill() 
                    enemy = Enemy(1100, GROUND_Y, next_stage["id"], next_stage["hp"], next_stage.get("boss", False))
                    all_sprites.add(enemy)
                
                    player.rect.left = 200
                    player.hp = player.max_hp
                    player.state = "IDLE"
                    player.vel_x = 0
                    player.vel_y = 0
                
                    countdown_timer = 240 
                    if "bgm" in SOUNDS and SOUNDS["bgm"]: SOUNDS["bgm"].stop() # 🌟 [추가] 기존 BGM 정지
                    KO_CINEMATIC_TIMER = 0
                    KO_TRIGGERED = False
                    ACTIVE_DAMAGE_NUMBERS.clear()

                    match_timer = 60.0        # 🌟 [추가] 시간 초기화
                    time_over = False          # 🌟 [추가] 시간 종료 플래그 초기화
                    death_delay_timer = 0 
                    CAMERA_X = 0 
                    player.combo_step = 0
                
                    p1_combo_display.active = False
                    p2_combo_display.active = False
                    print(f"NEXT STAGE: {next_stage['name']}")

            elif transition_state == "WIPE_OUT":
                transition_x += transition_speed
                if transition_x >= SCREEN_WIDTH + 400:
                    transition_state = "IDLE"

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
                    # 🌟 [변경] 즉시 리셋하지 않고 왼쪽에서 오른쪽으로 화면을 가리는 트랜지션 연출을 가동합니다.
                        if transition_state == "IDLE":
                            transition_state = "WIPE_IN"
                            transition_x = -SCREEN_WIDTH - 400
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
        
        for particle in ambient_particles:
            particle.update()
            particle.draw(screen, CAMERA_X)

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
            if hasattr(entity, 'flash_timer') and entity.flash_timer > 0:
                # 🌟 [버그 수정] 플래시 효과도 고유 키를 사용하도록 변경
                cache_key = (entity.char_id, entity.state, entity.frame_index, entity.facing_right, entity.is_boss)
                flash_img = get_flash_frame(entity.image, cache_key)
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
                
                # 🌟 [버그 수정] 똑바로 서서 가드하는 적인 A2(중갑 전사)와 C1(암살자)의 방어막 오프셋을 플레이어(A1)와 똑같이 100으로 상향 일치시킵니다.
                y_val = 100 if entity.char_id in ["A1", "A2", "C1"] else 10
                
                entity.guard_effect.draw(screen, entity.rect.centerx + offset_x - CAMERA_X, entity.rect.centery + offset_y, facing_val, y_val)

        # 캔슬 대쉬 UI (캐릭터 머리 위)
        for entity in all_sprites:
            if hasattr(entity, 'cancel_ui_timer') and entity.cancel_ui_timer > 0:
                entity.cancel_ui_timer -= 1
                y_offset = 30 - entity.cancel_ui_timer
                
                if getattr(entity, 'dodge_flag', False):
                    cancel_text = CACHED_TEXT_EVADE   # 🌟 미리 구워둔 이미지 즉시 사용
                    if entity.cancel_ui_timer <= 0: entity.dodge_flag = False
                else:
                    cancel_text = CACHED_TEXT_CANCEL  # 🌟 미리 구워둔 이미지 즉시 사용
                
                screen.blit(cancel_text, (entity.rect.centerx - CAMERA_X - cancel_text.get_width()//2, entity.rect.top - 20 - y_offset))

        # 콤보 디스플레이
        p1_combo_rect = player.rect.copy()
        p1_combo_rect.x -= CAMERA_X
        p1_combo_display.draw(screen, p1_combo_rect)

        p2_combo_rect = enemy.rect.copy()
        p2_combo_rect.x -= CAMERA_X
        p2_combo_display.draw(screen, p2_combo_rect)

        # 🌟 [신규 추가] 생성되어 있는 모든 타격 데미지 폰트를 화면 좌표 오프셋에 매핑하여 출력
        for dmg in ACTIVE_DAMAGE_NUMBERS:
            dmg.draw(screen, CAMERA_X)

        # ========================================================
        # 🌟 격투 게임 대칭형 HUD (Heads Up Display)
        # ========================================================
        
        # [중앙 VS 마크]
        if countdown_timer <= 0:
            # 1. 남은 시간 표시 (🌟 매 프레임 재랜더링하지 않고 1초마다 변경될 때만 캐시를 갱신)
            current_timer_int = int(match_timer)
            if current_timer_int != last_timer_val or cached_timer_surf is None:
                last_timer_val = current_timer_int
                cached_timer_surf = font_timer.render(str(current_timer_int), True, (255, 255, 255))
            screen.blit(cached_timer_surf, (SCREEN_WIDTH//2 - cached_timer_surf.get_width()//2, 20))
            
            # 2. 스테이지 표시 (🌟 스테이지 번호가 변경되었을 때만 딱 1회 새로 랜더링)
            if current_stage_idx != last_stage_idx_cached or cached_stage_surf is None:
                last_stage_idx_cached = current_stage_idx
                stage_label = f"STAGE {current_stage_idx + 1}" if current_stage_idx < len(STAGE_SEQUENCE) - 1 else "FINAL STAGE"
                cached_stage_surf = font_small.render(stage_label, True, (200, 200, 200))
            screen.blit(cached_stage_surf, (SCREEN_WIDTH//2 - cached_stage_surf.get_width()//2, 110))

        # [Player 1 (왼쪽) UI]
        p1_hp_ratio = player.hp / player.max_hp
        p1_disp_ratio = player.display_hp / player.max_hp 
        p1_color = (0, 255, 0) if p1_hp_ratio > 0.5 else (255, 255, 0) if p1_hp_ratio > 0.2 else (255, 0, 0)
        pygame.draw.rect(screen, (80, 0, 0), (50, 40, 450, 30)) 
        pygame.draw.rect(screen, (180, 35, 35), (50, 40, 450 * p1_disp_ratio, 30)) 
        pygame.draw.rect(screen, p1_color, (50, 40, 450 * p1_hp_ratio, 30)) 
        pygame.draw.rect(screen, (255, 255, 255), (50, 40, 450, 30), 3) 
        
        screen.blit(p1_name_surf, (50, 15))

        # Player 1 게이지 (좌측 하단)
        for i in range(3):
            color = (0, 200, 255) if i < player.hit_gauge else (60, 60, 60)
            pygame.draw.circle(screen, color, (60 + (i * 30), 680), 10)
        p1_dash_text = CACHED_DASH_TEXTS.get(player.dash_charges, CACHED_DASH_TEXTS[0]) # 🌟 연산 대신 캐시 참조
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
        p2_disp_ratio = enemy.display_hp / enemy.max_hp # 🌟 [신규 추가] P2 잔상 체력 비율
        p2_color = (0, 255, 0) if p2_hp_ratio > 0.5 else (255, 255, 0) if p2_hp_ratio > 0.2 else (255, 0, 0)
        p2_bar_x = SCREEN_WIDTH - 50 - 450
        pygame.draw.rect(screen, (80, 0, 0), (p2_bar_x, 40, 450, 30)) # 배경
        # 🌟 [신규 추가] 역방향 우측 잔상 HP바 먼저 드로잉
        pygame.draw.rect(screen, (180, 35, 35), (p2_bar_x + 450 * (1 - p2_disp_ratio), 40, 450 * p2_disp_ratio, 30))
        # 🌟 격투게임식 역방향 HP바 (오른쪽 끝 고정, 가운데로 줄어듦)
        pygame.draw.rect(screen, p2_color, (p2_bar_x + 450 * (1 - p2_hp_ratio), 40, 450 * p2_hp_ratio, 30)) 
        pygame.draw.rect(screen, (255, 255, 255), (p2_bar_x, 40, 450, 30), 3) # 테두리
        
        screen.blit(p2_name_surf, (SCREEN_WIDTH - 50 - p2_name_surf.get_width(), 15))

        # Player 2 게이지 (우측 하단, 대칭 배치)
        for i in range(3):
            color = (255, 50, 50) if i < enemy.hit_gauge else (60, 60, 60) 
            pygame.draw.circle(screen, color, (SCREEN_WIDTH - 60 - (i * 30), 680), 10)
        p2_dash_text = CACHED_DASH_TEXTS.get(enemy.dash_charges, CACHED_DASH_TEXTS[0])  # 🌟 연산 대신 캐시 참조
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
                # 🌟 [버그 수정] 위에서 미리 만든 폰트 사용
                dead_text = font_dead.render("DEAD", True, (220, 0, 0))
                dead_shadow = font_dead.render("DEAD", True, (0, 0, 0))
                
                shadow_rect = dead_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 5, SCREEN_HEIGHT // 2 + 5))
                text_rect = dead_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                screen.blit(dead_shadow, shadow_rect)
                screen.blit(dead_text, text_rect)

            # 완전히 어두워진 뒤 타이머 계산 및 메인 메뉴 복귀
            if game_over_alpha >= 255:
                post_death_timer -= 1
                if post_death_timer <= 0:
                    GAME_STATE = "MENU"
                    transition_state = "IDLE"                  # 🌟 추가
                    transition_x = -SCREEN_WIDTH - 400         # 🌟 추가
                    current_stage_idx = 0
                    stage_info = STAGE_SEQUENCE[current_stage_idx]
                    
                    match_timer = 60.0        # 🌟 사망 복귀 시 시간 초기화
                    time_over = False          # 🌟 사망 복귀 시 타임오버 플래그 초기화

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
                    if "bgm" in SOUNDS and SOUNDS["bgm"]: SOUNDS["bgm"].stop() # 🌟 [추가] 클리어 후 리셋 시 BGM 정지
                    KO_CINEMATIC_TIMER = 0
                    KO_TRIGGERED = False
                    ACTIVE_DAMAGE_NUMBERS.clear()
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
                # 🌟 [버그 수정] 위에서 미리 만든 폰트 사용
                clear_text = font_clear.render("GAME CLEAR", True, (255, 200, 0))  # 골드 색상
                clear_shadow = font_clear.render("GAME CLEAR", True, (0, 0, 0))
                
                shadow_rect = clear_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 5, SCREEN_HEIGHT // 2 + 5))
                text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                screen.blit(clear_shadow, shadow_rect)
                screen.blit(clear_text, text_rect)
                
            if game_clear_alpha >= 255:
                post_clear_timer -= 1
                if post_clear_timer <= 0:
                    GAME_STATE = "MENU"
                    transition_state = "IDLE"
                    transition_x = -SCREEN_WIDTH - 400
                    current_stage_idx = 0
                    stage_info = STAGE_SEQUENCE[current_stage_idx]
                    
                    match_timer = 60.0        # 🌟 클리어 복귀 시 시간 초기화
                    time_over = False          # 🌟 클리어 복귀 시 타임오버 플래그 초기화

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
                    if "bgm" in SOUNDS and SOUNDS["bgm"]: SOUNDS["bgm"].stop() # 🌟 [추가] 사망 후 리셋 시 BGM 정지
                    KO_CINEMATIC_TIMER = 0
                    KO_TRIGGERED = False
                    ACTIVE_DAMAGE_NUMBERS.clear()
                    death_delay_timer = 0
                    game_over_alpha = 0
                    game_cleared = False
                    game_clear_alpha = 0
                    post_clear_timer = 150
                    post_death_timer = 150
                    CAMERA_X = 0
                    p1_combo_display.active = False
                    p2_combo_display.active = False
        
        if KO_TRIGGERED and KO_CINEMATIC_TIMER > 0:
            # 🌟 [최적화] 매 프레임 무겁게 Surface 생성 및 Alpha 연산 연동을 제거하고 사전 캐싱된 전용 오버레이 서페이스만 고속 블릿합니다.
            if (KO_CINEMATIC_TIMER // 5) % 2 == 0:
                screen.blit(ko_red_overlay, (0, 0))
            else:
                screen.blit(ko_white_overlay, (0, 0))

            # 🌟 [최적화] 매 프레임 디스크 접근 및 무거운 글씨 래스터라이징 연산을 생략하고 이미 구워진 베이스 고해상도 자막을 축소/확대(scale)만 적용하여 그립니다.
            scale_pulse = 1.0 + math.sin((KO_CINEMATIC_TIMER / 80) * 3.14) * 0.25
            scaled_w = int(ko_base_w * scale_pulse)
            scaled_h = int(ko_base_h * scale_pulse)
            
            ko_text = pygame.transform.scale(ko_text_base, (scaled_w, scaled_h))
            ko_shadow = pygame.transform.scale(ko_shadow_base, (scaled_w, scaled_h))

            # 그림자 연출 오프셋(10px)을 두어 정중앙에 블릿
            screen.blit(ko_shadow, (SCREEN_WIDTH // 2 - scaled_w // 2 + 10, SCREEN_HEIGHT // 2 - scaled_h // 2 + 10))
            screen.blit(ko_text, (SCREEN_WIDTH // 2 - scaled_w // 2, SCREEN_HEIGHT // 2 - scaled_h // 2))

            # 슬로우 진입 시 단 1회 극적인 시각 충격을 가하기 위한 강제 대화면 흔들림 유발
            if KO_CINEMATIC_TIMER == 79:
                screen_shake_timer = 45
                screen_shake_intensity = 25

        if transition_state != "IDLE":
        # 사선 슬라이드 와이프를 위해 4개의 포인트로 평행사변형 구조 다각형 제작
        # 사선 슬라이드 와이프를 위해 4개의 포인트로 평행사변형 구조 다각형 제작
            wipe_polygon = [
            (transition_x + 300, 0),                        # 우측 상단 단추
            (transition_x + SCREEN_WIDTH + 500, 0),         # 좌측 상단 단추
            (transition_x + SCREEN_WIDTH, SCREEN_HEIGHT),    # 우측 하단 단추
            (transition_x - 200, SCREEN_HEIGHT)             # 좌측 하단 단추
            ]
            pygame.draw.polygon(screen, (10, 10, 15), wipe_polygon) # 완전한 검은색 계열 배색

        fps_update_timer += 1
        if fps_update_timer >= 15 or cached_fps_surf is None:
            fps_update_timer = 0
            current_fps = clock.get_fps()
            fps_color = (0, 255, 0) if current_fps >= 55 else (255, 120, 0)
            cached_fps_surf = font_small.render(f"FPS: {int(current_fps)}", True, fps_color)
        screen.blit(cached_fps_surf, (20, 80)) # 체력바 레이아웃 아래쪽 여백에 정렬


        pygame.display.flip()
        clock.tick(FPS) # 🌟 [렉 현상 해결] 전체 프레임 레이트를 인위적으로 떨어트리던 락을 해제하여 언제나 부드럽고 쾌적한 60 FPS 화면 재생률을 유지합니다.

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()