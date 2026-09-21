"""도어 손잡이.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 장착 구멍 간격 handle_spacing(128)의 당김 손잡이 하나를 도어 판 앞면에 세로로 단다(`cad/chamber.md` 손잡이 모델 행, 사용자 결정 2026-10-07). step.parts `pull_handle_mount_spacing128`은 손잡이 봉이 기둥에서 2 mm 떠 있는 결함 모델이라 쓰지 않고, 흔한 당김 손잡이(기둥 2개 + 손잡이 봉)의 대표 형상을 한 몸의 단순 솔리드로 직접 그린다(루프 중 추천안 자동 선택 2026-10-07, 사용자 확인 대기). 기둥 지름, 봉 지름, 봉이 기둥 밖으로 나가는 길이, 손가락 틈은 아래의 작업 가정이다.

기둥 2개는 축이 y 방향인 원기둥이고, 축은 (handle_x, handle_post_z) = (60, 166) · (60, 294)를 지난다. 기둥 밑면이 도어 판 앞면 door_plate_y0(−51)에 닿고 기둥은 바깥(−y)으로 선다. 손잡이 봉은 축이 z 방향인 원기둥이고, 봉 뒷면과 도어 판 앞면 사이에 손가락이 들어갈 틈 FINGER_GAP을 둔다. 기둥 윗면은 봉 축까지 올라가 봉 속에 묻히므로(기둥 지름 < 봉 지름) 기둥과 봉이 접선이 아니라 제대로 교차해 한 몸이 된다.

장착 나사 구멍은 그리지 않는다(경첩·토글 클램프처럼). 도어 판에도 구멍이 없다.

label: door_handle — 기둥 2개와 봉을 합친 솔리드 하나.
"""

from __future__ import annotations

from cadgen import build123d as bd
from cadgen import step

from params import (
    door_plate_x0,
    door_plate_x1,
    door_plate_y0,
    door_plate_z0,
    door_plate_z1,
    handle_post_z,
    handle_spacing,
    handle_x,
)

# 크기는 모두 작업 가정 — 사용자 확인 필요. 흔한 장착 간격 128 mm 스테인리스 봉 손잡이를 본뜬 대표값이다.
POST_DIA = 10.0  # 작업 가정 — 사용자 확인 필요. 기둥 지름. 봉 지름보다 작아야 기둥 윗면이 봉 속에 묻힌다
BAR_DIA = 12.0  # 작업 가정 — 사용자 확인 필요. 손잡이 봉 지름(원형 단면)
BAR_OVERHANG = 10.0  # 작업 가정 — 사용자 확인 필요. 봉 끝이 기둥 축 밖으로 나가는 길이(z), 위·아래 같다
FINGER_GAP = 25.0  # 작업 가정 — 사용자 확인 필요. 봉 뒷면과 도어 판 앞면 사이 손가락 틈(y)

# y는 도어 판 앞면(−51)에서 바깥(−y)으로 쌓는다.
POST_Y1 = door_plate_y0  # 기둥 밑면, 도어 판 앞면 (−51)
BAR_Y1 = POST_Y1 - FINGER_GAP  # 봉 뒷면 (−76)
BAR_AXIS_Y = BAR_Y1 - BAR_DIA / 2  # 봉 축 y (−82)
BAR_Y0 = BAR_Y1 - BAR_DIA  # 봉 앞면 (−88)
POST_Y0 = BAR_AXIS_Y  # 기둥 윗면, 봉 축 (−82)
POST_H = POST_Y1 - POST_Y0  # 기둥 높이(y), 손가락 틈 + 봉 반지름 (31)
BAR_Z0 = min(handle_post_z) - BAR_OVERHANG  # 봉 아래 끝 (156)
BAR_Z1 = max(handle_post_z) + BAR_OVERHANG  # 봉 위 끝 (304)


def post(zc: float) -> bd.Solid:
    """축이 y 방향이고 (handle_x, zc)를 지나는 기둥, y POST_Y0–POST_Y1."""
    return bd.Solid.make_cylinder(POST_DIA / 2, POST_H, plane=bd.Plane(origin=(handle_x, POST_Y0, zc), z_dir=(0, 1, 0)))


def bar() -> bd.Solid:
    """축이 z 방향이고 (handle_x, BAR_AXIS_Y)를 지나는 손잡이 봉, z BAR_Z0–BAR_Z1."""
    return bd.Solid.make_cylinder(BAR_DIA / 2, BAR_Z1 - BAR_Z0, plane=bd.Plane(origin=(handle_x, BAR_AXIS_Y, BAR_Z0), z_dir=(0, 0, 1)))


@step(out="../step/door_handle.step")
def door_handle():
    assert len(handle_post_z) == 2 and abs((max(handle_post_z) - min(handle_post_z)) - handle_spacing) < 1e-6
    assert POST_DIA < BAR_DIA, "기둥이 봉보다 굵으면 기둥 윗면이 봉 밖으로 드러난다"
    assert FINGER_GAP > 0 and BAR_OVERHANG >= POST_DIA / 2, "봉이 기둥을 다 덮지 못한다"
    assert door_plate_x0 <= handle_x - BAR_DIA / 2 and handle_x + BAR_DIA / 2 <= door_plate_x1, "손잡이가 도어 판 x 범위 밖으로 나간다"
    assert door_plate_z0 <= BAR_Z0 and BAR_Z1 <= door_plate_z1, "손잡이가 도어 판 z 범위 밖으로 나간다"
    body = bar()
    for zc in handle_post_z:
        body = body + post(zc)
    solids = body.solids()
    if not body.is_valid or len(solids) != 1:
        raise ValueError(f"door_handle 솔리드가 올바르지 않다 (solids {len(solids)})")
    handle = solids[0]
    handle.label = "door_handle"
    # 솔리드 하나를 그대로 반환하면 STEP에 label이 남지 않으므로 compound로 감싼다.
    return bd.Compound(children=[handle])


if __name__ == "__main__":
    door_handle()
