import pygame
import json

# --- 설정 데이터 ---
CHAR_DATA = {
    "A1": {"size": (200, 200), "speed": 100, "anims": {"Attack1": 4, "Attack2": 4, "Death": 7, "Fall": 2, "Idle": 4, "Jump": 2, "Run": 8, "Take Hit": 3}},
    "A2": {"size": (200, 200), "speed": 100, "anims": {"Attack1": 6, "Attack2": 6, "Death": 6, "Fall": 2, "Idle": 8, "Jump": 2, "Run": 8, "Take Hit": 4}},
    "B1": {"size": (90, 90), "speed": 100, "anims": {"Attack1": 18, "Death": 8, "Idle": 9, "Run": 9, "Take Hit": 3}},
    "C1": {"size": (162, 162), "speed": 100, "anims": {"Attack1": 7, "Attack2": 7, "Attack3": 8, "Death": 7, "Fall": 3, "Idle": 10, "Jump": 3, "Run": 8, "Take Hit": 3}},
    "C2": {"size": (126, 126), "speed": 100, "anims": {"Attack1": 7, "Attack2": 6, "Attack3": 9, "Death": 10, "Fall": 3, "Idle": 10, "Jump": 3, "Run": 8, "Take Hit": 3}},
}

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
font = pygame.font.SysFont("malgungothic", 20)

# 상태 관리
current_char = "A1"
current_anim = "Attack1"
current_frame = 0
editing_rect = "hitbox" 
final_data = {}

class EditableRect:
    def __init__(self, x, y, w, h, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.dragging = False
        self.resizing = False

    def draw(self, surface, offset_x, offset_y):
        draw_rect = self.rect.copy()
        draw_rect.x += offset_x
        draw_rect.y += offset_y
        pygame.draw.rect(surface, self.color, draw_rect, 2)

    def handle_event(self, event, rel_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(rel_pos):
                if rel_pos[0] > self.rect.right - 10 and rel_pos[1] > self.rect.bottom - 10:
                    self.resizing = True
                else:
                    self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            self.resizing = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.move_ip(event.rel)
            elif self.resizing:
                self.rect.width += event.rel[0]
                self.rect.height += event.rel[1]

hitbox = EditableRect(50, 50, 40, 40, (255, 0, 0)) 
attack_range = EditableRect(100, 50, 60, 40, (0, 0, 255))

def load_image():
    filename = f"{current_char}_{current_anim}.png"
    try:
        full_sheet = pygame.image.load(filename).convert_alpha()
        frame_w, frame_h = CHAR_DATA[current_char]["size"]
        # 현재 프레임 위치 계산하여 잘라내기
        rect = pygame.Rect(current_frame * frame_w, 0, frame_w, frame_h)
        return full_sheet.subsurface(rect)
    except Exception as e:
        surf = pygame.Surface(CHAR_DATA[current_char]["size"])
        surf.fill((100, 100, 100))
        return surf

running = True
while running:
    screen.fill((30, 30, 30))
    
    img = load_image()
    img_rect = img.get_rect(center=(400, 300))
    screen.blit(img, img_rect)

    hitbox.draw(screen, img_rect.x, img_rect.y)
    attack_range.draw(screen, img_rect.x, img_rect.y)

    txt = font.render(f"캐릭터: {current_char} | 애니메이션: {current_anim} | 프레임: {current_frame+1}/{CHAR_DATA[current_char]['anims'][current_anim]}", True, (255, 255, 255))
    screen.blit(txt, (20, 20))
    info = font.render("좌클릭: 이동 / 우하단드래그: 크기조절 | H: 히트박스 | A: 공격범위 | S: 저장", True, (200, 200, 200))
    screen.blit(info, (20, 50))
    nav = font.render("방향키 좌우: 프레임 | 상하: 애니메이션 | 1~5: 캐릭터 변경", True, (200, 200, 200))
    screen.blit(nav, (20, 80))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        rel_pos = (event.pos[0] - img_rect.x, event.pos[1] - img_rect.y) if hasattr(event, 'pos') else (0, 0)
        
        if editing_rect == "hitbox":
            hitbox.handle_event(event, rel_pos)
        else:
            attack_range.handle_event(event, rel_pos)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h: editing_rect = "hitbox"
            if event.key == pygame.K_a: editing_rect = "attack_range"
            if event.key == pygame.K_s: 
                char_name = current_char
                anim_name = current_anim
                if char_name not in final_data: final_data[char_name] = {}
                if anim_name not in final_data[char_name]: 
                    final_data[char_name][anim_name] = {"sprite_size": CHAR_DATA[char_name]["size"], "frames": []}
                
                frames = final_data[char_name][anim_name]["frames"]
                while len(frames) < CHAR_DATA[char_name]["anims"][anim_name]:
                    frames.append({})
                
                frames[current_frame] = {
                    "hitbox": [hitbox.rect.x, hitbox.rect.y, hitbox.rect.w, hitbox.rect.h],
                    "attack_range": [attack_range.rect.x, attack_range.rect.y, attack_range.rect.w, attack_range.rect.h]
                }
                print(f"Saved: {current_char} {current_anim} Frame {current_frame}")

            if event.key == pygame.K_RIGHT: current_frame = (current_frame + 1) % CHAR_DATA[current_char]["anims"][current_anim]
            if event.key == pygame.K_LEFT: current_frame = (current_frame - 1) % CHAR_DATA[current_char]["anims"][current_anim]
            if event.key == pygame.K_UP:
                anims = list(CHAR_DATA[current_char]["anims"].keys())
                current_anim = anims[(anims.index(current_anim) - 1) % len(anims)]
                current_frame = 0
            if event.key == pygame.K_DOWN:
                anims = list(CHAR_DATA[current_char]["anims"].keys())
                current_anim = anims[(anims.index(current_anim) + 1) % len(anims)]
                current_frame = 0

            if event.key == pygame.K_1: current_char = "A1"; current_anim = "Attack1"; current_frame = 0
            if event.key == pygame.K_2: current_char = "A2"; current_anim = "Attack1"; current_frame = 0
            if event.key == pygame.K_3: current_char = "B1"; current_anim = "Attack1"; current_frame = 0
            if event.key == pygame.K_4: current_char = "C1"; current_anim = "Attack1"; current_frame = 0
            if event.key == pygame.K_5: current_char = "C2"; current_anim = "Attack1"; current_frame = 0

    pygame.display.flip()
    clock.tick(60)

# 프로그램 종료 시 JSON 저장 (필요시 주석 해제)
# with open("hitbox_data.json", "w") as f:
#     json.dump(final_data, f, indent=4)

pygame.quit()