"""도어 경첩.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 50 × 50 맞대기 경첩 3개와 그 받침 블록 3개다. step.parts `butt_hinge_50x50`은 날개 폭이 0.05 mm인 결함 모델이라 쓰지 않고, 펼친 전체 50 × 50(날개 하나 25 × 50)의 대표 형상을 직접 그린다(`cad/chamber.md` 경첩 모델 행, 루프 중 추천안 자동 선택 2026-10-07, 사용자 확인 대기). 날개 두께, 너클 지름, 너클 축의 y 위치는 아래의 작업 가정이다.

닫힌 상태로 그린다. 너클 축은 z 방향이고 도어 판 오른쪽 끝 x door_plate_x1 선 위에 있다. 두 날개는 뒷면이 도어 판 앞면과 같은 평면 y door_plate_y0에 펼쳐지고, 도어 쪽 날개(x < door_plate_x1)는 도어 판 앞면에, 프레임 쪽 날개(x > door_plate_x1)는 받침 블록 앞면에 붙는다. 날개와 너클은 그 평면보다 앞(−y)에 있다. 문은 이 너클 축을 중심으로 돈다.

받침 블록은 프레임 쪽 날개의 평면 외곽과 같은 크기이고, 두께 t_spacer로 앞면 패널 바깥면에 붙는다(사용자 결정 2026-10-07). 블록 밑면 아래에 앞면 패널 볼트 구멍(chamber_panel.bolt_holes())이 걸리면 그 구멍 중심에 머리 자리를 블록 밑면에서 판다. 나사 구멍은 그리지 않는다.

label: hinge_1(위) … hinge_3(아래)는 각각 날개 둘과 너클 하나(hinge_N_leaf_door, hinge_N_leaf_frame, hinge_N_knuckle)를 담은 compound이고, hinge_spacer_1 … hinge_spacer_3은 솔리드 하나다. 날개에서 너클 원기둥을 빼서 세 솔리드가 부피로 겹치지 않게 한다.
"""

from cadgen import build123d as bd
from cadgen import step

from chamber_panel import bolt_holes
from params import (
    door_plate_x1,
    door_plate_y0,
    frame_x1,
    hinge_L,
    hinge_leaf_W,
    hinge_N,
    hinge_open_W,
    hinge_z,
    panel_bolt_hole_dia,
    panel_front_y0,
    spacer_head_depth,
    spacer_head_dia,
    t_spacer,
)

LEAF_T = 2.0  # 작업 가정 — 사용자 확인 필요. 날개 두께
KNUCKLE_DIA = 7.0  # 작업 가정 — 사용자 확인 필요. 너클 바깥지름(핀은 따로 그리지 않는다)
KNUCKLE_EMBED = 0.5  # 작업 가정 — 사용자 확인 필요. 너클 뒤 끝이 날개 뒷면 평면보다 앞(−y)으로 들어온 거리. 0이면 너클이 그 평면에 접해 날개에서 뺄 때 접선 퇴화가 생긴다

AXIS_X = door_plate_x1  # 너클 축 x — 도어 판 오른쪽 끝 (1310)
LEAF_Y1 = door_plate_y0  # 날개 뒷면 — 도어 판 앞면 (−51)
LEAF_Y0 = LEAF_Y1 - LEAF_T  # 날개 앞면
AXIS_Y = LEAF_Y1 - KNUCKLE_EMBED - KNUCKLE_DIA / 2  # 너클 축 y


def _box(x0, x1, y0, y1, z0, z1):
    box = bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    return box.moved(bd.Location((x0, y0, z0)))


def _overlaps_rect(cx, cz, r, x0, x1, z0, z1):
    """원 (cx, cz, r)이 사각형 [x0, x1] × [z0, z1]과 넓이로 겹치는지."""
    dx = max(x0 - cx, 0.0, cx - x1)
    dz = max(z0 - cz, 0.0, cz - z1)
    return dx * dx + dz * dz < r * r


def hinge(i: int, zc: float) -> bd.Compound:
    z0, z1 = zc - hinge_L / 2, zc + hinge_L / 2
    knuckle = bd.Solid.make_cylinder(KNUCKLE_DIA / 2, hinge_L, plane=bd.Plane(origin=(AXIS_X, AXIS_Y, z0), z_dir=(0, 0, 1)))
    knuckle.label = f"hinge_{i}_knuckle"
    leaf_door = _box(AXIS_X - hinge_leaf_W, AXIS_X, LEAF_Y0, LEAF_Y1, z0, z1) - knuckle
    leaf_door.label = f"hinge_{i}_leaf_door"
    leaf_frame = _box(AXIS_X, AXIS_X + hinge_leaf_W, LEAF_Y0, LEAF_Y1, z0, z1) - knuckle
    leaf_frame.label = f"hinge_{i}_leaf_frame"
    parts = [leaf_door, leaf_frame, knuckle]
    for p in parts:
        if not p.is_valid or len(p.solids()) != 1:
            raise ValueError(f"{p.label} 솔리드가 올바르지 않다 (solids {len(p.solids())})")
    return bd.Compound(children=parts, label=f"hinge_{i}")


def spacer(i: int, zc: float) -> tuple[bd.Solid, list]:
    """받침 블록과, 그 밑면에 머리 자리를 판 볼트 구멍 중심 목록."""
    x0, x1 = AXIS_X, AXIS_X + hinge_leaf_W  # 프레임 쪽 날개의 평면 외곽
    z0, z1 = zc - hinge_L / 2, zc + hinge_L / 2
    block = _box(x0, x1, LEAF_Y1, panel_front_y0, z0, z1)
    under = [(hx, hz) for hx, hz in bolt_holes()["panel_front"] if _overlaps_rect(hx, hz, panel_bolt_hole_dia / 2, x0, x1, z0, z1)]
    for hx, hz in under:
        recess = bd.Solid.make_cylinder(spacer_head_dia / 2, spacer_head_depth, plane=bd.Plane(origin=(hx, panel_front_y0, hz), z_dir=(0, -1, 0)))
        block = block - recess
    block.label = f"hinge_spacer_{i}"
    if not block.is_valid or len(block.solids()) != 1:
        raise ValueError(f"{block.label} 솔리드가 올바르지 않다")
    return block, under


@step(out="../step/door_hinge.step")
def door_hinge():
    assert abs(2 * hinge_leaf_W - hinge_open_W) < 1e-6, "날개 둘의 폭이 펼친 전체 폭과 다르다"
    assert abs((panel_front_y0 - LEAF_Y1) - t_spacer) < 1e-6, "받침 블록 y 구간이 t_spacer와 다르다"
    assert AXIS_X + hinge_leaf_W <= frame_x1, "받침 블록이 앞면 패널 외곽 밖으로 나간다"
    assert len(hinge_z) == hinge_N
    hinges = [hinge(i, zc) for i, zc in enumerate(hinge_z, 1)]
    spacers = []
    for i, zc in enumerate(hinge_z, 1):
        block, under = spacer(i, zc)
        print(f"hinge_spacer_{i}: 밑면 아래 볼트 구멍 {under if under else '없음 — 머리 자리를 파지 않는다'}")
        spacers.append(block)
    return bd.Compound(children=hinges + spacers)


if __name__ == "__main__":
    door_hinge()
