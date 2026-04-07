import pygame

pygame.init()
WIDTH, HEIGHT = 400, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sprite Wrapping")
clock = pygame.time.Clock()

# ── ① 이미지 로드 및 변환 ────────────────────────
img = pygame.image.load("assets\images\player.png").convert_alpha()
img = pygame.transform.scale(img, (80, 120))
img = pygame.transform.rotate(img, 45)  # 회전

rect = img.get_rect()
rect.center = (200, 150)

# ── 이동 속도 설정 ──────────────────────────────
speed_x = 3
speed_y = 2

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ── 이동 로직 ──────────────────────────────
    rect.x += speed_x
    rect.y += speed_y

    # ── 화면 래핑(Wrapping) 로직 ─────────────────
    # 오른쪽으로 나갔을 때 -> 왼쪽 끝으로 이동
    if rect.left > WIDTH:
        rect.right = 0
    # 왼쪽으로 나갔을 때 -> 오른쪽 끝으로 이동
    elif rect.right < 0:
        rect.left = WIDTH
        
    # 아래로 나갔을 때 -> 위쪽 끝으로 이동
    if rect.top > HEIGHT:
        rect.bottom = 0
    # 위로 나갔을 때 -> 아래쪽 끝으로 이동
    elif rect.bottom < 0:
        rect.top = HEIGHT

    screen.fill((30, 30, 40))
    screen.blit(img, rect)
    pygame.display.flip()

pygame.quit()