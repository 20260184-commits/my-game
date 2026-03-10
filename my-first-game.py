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
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(40, 80) # 수명을 다시 적절하게 조절
        self.size = random.randint(3, 7)
        self.color = (random.randint(150, 255), random.randint(100, 255), random.randint(150, 255))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15 # 중력을 조금 더 강하게 주어 빠르게 아래로 떨어지게 함
        self.life -= 1

    def draw(self, surf):
        # 파티클이 죽어갈 때 투명도 대신 크기를 줄여 사라지는 효과
        size = max(0, int(self.size * (self.life / 80)))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), size)

    def alive(self):
        return self.life > 0

running = True
time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # [핵심] 배경을 매번 새로 그리기 (화면 지우기)
    # 배경을 매번 지우지 않으면 파티클의 잔상이 남게 됩니다.
    screen.fill((10, 10, 20)) 

    mouse = pygame.mouse.get_pos()
    buttons = pygame.mouse.get_pressed()

    if buttons[0]:
        for _ in range(10):
            particles.append(Particle(mouse[0], mouse[1]))

    # 파티클 업데이트 및 그리기
    for p in particles:
        p.update()
        p.draw(screen)

    # 죽은 파티클 제거
    particles = [p for p in particles if p.alive()]

    pygame.display.flip()
    clock.tick(60)

pygame.quit()