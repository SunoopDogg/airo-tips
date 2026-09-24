"""도어.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 두께 t_door의 아크릴 판 하나이고, 도어 개구 둘레에 door_overlap씩 겹친다(사용자 결정 2026-10-07). 닫힌 상태로, 뒷면이 밀폐재 앞면에 닿은 압착 전 위치에 그린다.

판에는 구멍을 내지 않는다. 경첩·토글 클램프·손잡이를 다는 구멍은 각 철물 모델에서만 보인다.
"""

from cadgen import build123d as bd
from cadgen import srgb
from cadgen import step

from params import (
    door_plate_H,
    door_plate_W,
    door_plate_x0,
    door_plate_y0,
    door_plate_y1,
    door_plate_z0,
    t_door,
)
from style import acrylic, acrylic_opacity


@step(out="../step/door.step")
def door():
    assert abs((door_plate_y1 - door_plate_y0) - t_door) < 1e-6, "도어 판 y 구간이 t_door와 다르다"
    body = bd.Box(door_plate_W, t_door, door_plate_H, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    body = body.moved(bd.Location((door_plate_x0, door_plate_y0, door_plate_z0)))
    body.label = "door"
    body.color = srgb(acrylic, acrylic_opacity)
    # 솔리드 하나를 그대로 반환하면 STEP에 label이 남지 않으므로 compound로 감싼다.
    return bd.Compound(children=[body])


if __name__ == "__main__":
    door()
