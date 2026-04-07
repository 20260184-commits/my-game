import pygame

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Sound Basics")
clock = pygame.time.Clock()

# ── ① 효과음 로드
shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.ogg")

# ── ② 배경음악 로드
pygame.mixer.music.load("assets/sounds/bgm.wav")

# ── ③ 볼륨 조절
shoot_sound.set_volume(0.5)
pygame.mixer.music.set_volume(0.3)

# ── ④ 배경음악 재생
pygame.mixer.music.play(-1)

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # ── 키보드 이벤트 (종료) ──
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        
        # ── 마우스 클릭 이벤트 (효과음 재생) ──
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 1: 왼쪽 마우스 버튼
                shoot_sound.stop()
                shoot_sound.play()

    screen.fill((30, 30, 40))
    pygame.display.flip()

pygame.quit()