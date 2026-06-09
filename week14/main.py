from ursina import *

app = Ursina(borderless=False)

# 자동차 본체 생성
car = Entity(model='cube', color=color.orange, scale=Vec3(2, 0.5, 1))

# 바퀴 4개 생성 (자동차의 자식(parent=car)으로 설정하여 함께 이동하게 함)
wheel_fl = Entity(model='sphere', color=color.black, parent=car,
                  scale=0.4, position=Vec3(-0.6, -0.4,  0.6))
wheel_fr = Entity(model='sphere', color=color.black, parent=car,
                  scale=0.4, position=Vec3( 0.6, -0.4,  0.6))
wheel_rl = Entity(model='sphere', color=color.black, parent=car,
                  scale=0.4, position=Vec3(-0.6, -0.4, -0.6))
wheel_rr = Entity(model='sphere', color=color.black, parent=car,
                  scale=0.4, position=Vec3( 0.6, -0.4, -0.6))

# 카메라 설정
camera.position = (0, 3, -8)
camera.look_at(car)

def update():
    # 'd'키를 누르면 오른쪽 이동, 'a'키를 누르면 왼쪽 이동
    if held_keys['d']: car.x += 3 * time.dt
    if held_keys['a']: car.x -= 3 * time.dt
    
    # 이동 중일 때(a 또는 d를 누르고 있을 때) 바퀴 회전 애니메이션
    if held_keys['d'] or held_keys['a']:
        for w in [wheel_fl, wheel_fr, wheel_rl, wheel_rr]:
            w.rotation_z -= 200 * time.dt

app.run()