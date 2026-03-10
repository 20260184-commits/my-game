import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fancy Particle Playground")

clock = pygame.time.Clock()

particles = []

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        # 더 넓은 각도와 속도 범위를 주어 파티클이 사방으로 퍼지게 함
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 8) 

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # 수명을 조금 더 길게 설정하여 화면에 오래 머물게 함
        self.life = random.randint(60, 120)
        self.size = random.randint(3, 7)

        self.color = (
            random.randint(150, 255),
            random.randint(100, 255),
            random.randint(150, 255)
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # 중력 효과를 아주 살짝 줄여서 더 높이 솟구치게 함
        self.vy += 0.05 
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            # 투명도 효과를 위해 파티클이 죽어갈수록 작아지게 만듦
            current_size = max(1, int(self.size * (self.life / 100)))
            pygame.draw.circle(
                surf,
                self.color,
                (int(self.x), int(self.y)),
                current_size
            )

    def alive(self):
        return self.life > 0

def draw_background(surface, t):
    # 배경 그리기 속도를 개선하기 위해 루프를 조금 더 효율적으로 (생략 가능)
    for y in range(0, HEIGHT, 5): # 5픽셀 간격으로 그리면 성능이 좋아집니다
        c = int(40 + 30 * math.sin(y * 0.01 + t))
        color = (10, c, 50 + c//2)
        pygame.draw.line(surface, color, (0, y), (WIDTH, y+4))

running = True
time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    mouse = pygame.mouse.get_pos()
    buttons = pygame.mouse.get_pressed()

    # [핵심 수정] 마우스 클릭 시 생성되는 파티클 개수를 8개에서 15개로 증가
    if buttons[0]:
        for _ in range(15):
            particles.append(Particle(mouse[0], mouse[1]))

    time += 0.03
    draw_background(screen, time)

    for p in particles:
        p.update()
        p.draw(screen)

    # 리스트 컴프리헨션을 사용하여 죽은 파티클 정리
    particles = [p for p in particles if p.alive()]

    pygame.display.flip()
    clock.tick(60)

pygame.quit()