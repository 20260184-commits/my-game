import pygame
import sys
import random

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")

font = pygame.font.SysFont("Arial", 24)

# 색상 정의
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

circle_x, circle_y = 400, 300
speed = 5

# 타이머 및 객체 관리 변수
clock = pygame.time.Clock()
last_spawn_time = pygame.time.get_ticks()
squares = [] 

running = True
while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # 키 입력 처리
    keys = pygame.key.get_pressed()
    is_moving = any([keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP], keys[pygame.K_DOWN]])
    
    if keys[pygame.K_LEFT]: circle_x -= speed
    if keys[pygame.K_RIGHT]: circle_x += speed
    if keys[pygame.K_UP]: circle_y -= speed
    if keys[pygame.K_DOWN]: circle_y += speed

    # 색상 결정 (움직이면 검정, 아니면 흰색)
    circle_color = BLACK if is_moving else WHITE

    # 2초(2000ms)마다 사각형 생성
    if current_time - last_spawn_time > 2000:
        # 원에서 약 200픽셀 떨어진 곳에 생성 (랜덤 오프셋)
        offset_x = random.randint(-200, 200)
        offset_y = random.randint(-200, 200)
        squares.append({'pos': (circle_x + offset_x, circle_y + offset_y), 'time': current_time})
        last_spawn_time = current_time

    screen.fill(GRAY) # 배경 회색
    
    # 사각형 그리기 및 3초(3000ms) 지났으면 제거
    squares = [s for s in squares if current_time - s['time'] < 3000]
    for s in squares:
        # 30x30 크기의 검은색 사각형
        pygame.draw.rect(screen, BLACK, (s['pos'][0]-15, s['pos'][1]-15, 30, 30))
    
    # 원 그리기
    pygame.draw.circle(screen, circle_color, (circle_x, circle_y), 50)
    
    # FPS 표시
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
    screen.blit(fps_text, (720, 10))
    
    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()
sys.exit()