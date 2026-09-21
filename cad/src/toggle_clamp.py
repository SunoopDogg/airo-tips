"""토글 클램프.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 누름형(수직형) 토글 클램프 2개를 도어 판 왼쪽 변 바깥의 앞면 패널 바깥면에 단다(`cad/chamber.md` 토글 클램프 모델 행, 사용자 결정 2026-10-07). step.parts에 누름형 토글 클램프가 없어 대표 형상을 단순 솔리드로 직접 그리고, 받침판·몸체·암·레버·스핀들·패드의 크기는 아래의 작업 가정이다. 링크 기구는 그리지 않는다.

클램프의 "위"는 앞면 패널 바깥면에서 바깥으로 나오는 −y 방향이다. 잠긴 상태로 그린다. 받침판 뒷면이 앞면 패널 바깥면 panel_front_y0에 붙고, 몸체가 받침판 위에 서고, 누름 암이 몸체 오른쪽 면에서 +x로 뻗어 도어 판 왼쪽 변 위로 넘어온다. 스핀들은 암을 y 방향으로 꿰뚫고, 스핀들 끝 고무 패드의 뒷면이 도어 판 앞면 door_plate_y0에 면으로 닿아 +y로 누른다. 레버는 수직형 클램프가 잠겼을 때처럼 몸체 윗면에서 −y로 선다.

패드 중심 x는 밀폐재 링 왼쪽 띠(gasket_out_x0–gasket_in_x0)의 가운데이고, 클램프 중심 z는 clamp_z다. 둘 다 params.py에서 계산하며 작업 가정이 아니다. 받침판·몸체의 오른쪽 끝은 도어 판 왼쪽 끝 door_plate_x0에서 DOOR_CLR만큼 왼쪽에 있다.

받침판 평면 외곽 아래에 앞면 패널 볼트 구멍(chamber_panel.bolt_holes())의 Ø panel_bolt_hole_dia 원이 걸리면, 그 구멍 중심에 버튼 볼트 머리 자리 Ø spacer_head_dia × 깊이 spacer_head_depth를 받침판 밑면에서 판다(경첩 받침 블록과 같은 머리 자리). 머리 자리가 받침판 밖으로 빠져나가거나, 볼트 머리 원(Ø spacer_head_dia)이 받침판에 걸리는데 머리 자리를 파지 않게 되면 빌드를 멈춘다. 나사 구멍(클램프 장착 나사, 스핀들 나사산)은 그리지 않는다.

label: clamp_1(위), clamp_2(아래)는 각각 받침판·몸체·암·레버·스핀들·패드 여섯 솔리드(clamp_N_base, clamp_N_body, clamp_N_arm, clamp_N_lever, clamp_N_spindle, clamp_N_pad)를 담은 compound다. 암에서 스핀들 원기둥을 빼서 솔리드끼리 부피로 겹치지 않고, 나머지는 면으로 맞닿는다.
"""

from cadgen import build123d as bd
from cadgen import step

from chamber_panel import bolt_holes
from params import (
    clamp_N,
    clamp_z,
    door_plate_x0,
    door_plate_y0,
    frame_x0,
    gasket_in_x0,
    gasket_out_x0,
    gasket_W,
    panel_bolt_hole_dia,
    panel_front_y0,
    spacer_head_depth,
    spacer_head_dia,
)

# 크기는 모두 작업 가정 — 사용자 확인 필요. 흔한 소형 수직형 누름 클램프를 본뜬 대표값이다.
DOOR_CLR = 2.0  # 작업 가정 — 사용자 확인 필요. 받침판·몸체 오른쪽 끝과 도어 판 왼쪽 끝(x 20) 사이 틈
BASE_LX = 44.0  # 작업 가정 — 사용자 확인 필요. 받침판 x 길이
BASE_LZ = 55.0  # 작업 가정 — 사용자 확인 필요. 받침판 z 길이. 아래 클램프 받침판이 볼트 구멍 (−15, 0)의 머리 자리를 통째로 품고(아래 끝까지 2) 볼트 구멍 (0, −15)의 머리 원에서 2 떨어지는 길이
BASE_T = 6.0  # 작업 가정 — 사용자 확인 필요. 받침판 두께. 머리 자리 깊이(4)보다 두꺼워야 한다
BODY_LX = 38.0  # 작업 가정 — 사용자 확인 필요. 몸체 x 길이, 오른쪽 끝은 받침판과 같다
BODY_W = 16.0  # 작업 가정 — 사용자 확인 필요. 몸체 폭(z)
ARM_W = 16.0  # 작업 가정 — 사용자 확인 필요. 누름 암 폭(z)
ARM_T = 8.0  # 작업 가정 — 사용자 확인 필요. 누름 암 두께(y)
ARM_TIP = 10.0  # 작업 가정 — 사용자 확인 필요. 스핀들 축에서 암 끝까지(x)
SPINDLE_DIA = 6.0  # 작업 가정 — 사용자 확인 필요. 스핀들 지름(M6 상당, 나사산은 그리지 않는다)
SPINDLE_GAP = 10.0  # 작업 가정 — 사용자 확인 필요. 패드 앞면에서 암 뒷면까지 스핀들이 드러난 길이
SPINDLE_TOP = 10.0  # 작업 가정 — 사용자 확인 필요. 암 앞면 밖으로 스핀들이 나온 길이
PAD_DIA = 14.0  # 작업 가정 — 사용자 확인 필요. 고무 패드 지름. 밀폐재 띠 폭(15) 안에 들도록 그보다 작게 골랐다
PAD_T = 8.0  # 작업 가정 — 사용자 확인 필요. 고무 패드 두께(y)
LEVER_W = 10.0  # 작업 가정 — 사용자 확인 필요. 레버 막대 단면 한 변(x, z). 막대 왼쪽 면은 몸체 왼쪽 면과 같다
LEVER_H = 36.0  # 작업 가정 — 사용자 확인 필요. 몸체 앞면에서 손잡이 덮개까지 레버 막대 길이(−y)
GRIP_DIA = 18.0  # 작업 가정 — 사용자 확인 필요. 레버 끝 손잡이 덮개 지름
GRIP_L = 40.0  # 작업 가정 — 사용자 확인 필요. 레버 끝 손잡이 덮개 길이(−y)

PAD_X = (gasket_out_x0 + gasket_in_x0) / 2  # 패드·스핀들 축 x — 밀폐재 링 왼쪽 띠의 가운데 (35)
BASE_X1 = door_plate_x0 - DOOR_CLR  # 받침판·몸체 오른쪽 끝 (18)
BASE_X0 = BASE_X1 - BASE_LX  # 받침판 왼쪽 끝 (−26)
BODY_X0 = BASE_X1 - BODY_LX  # 몸체 왼쪽 끝 (−20)

# y는 패널 바깥면(−33)에서 바깥(−y)으로 쌓는다.
BASE_Y1 = panel_front_y0  # 받침판 뒷면, 앞면 패널 바깥면 (−33)
BASE_Y0 = BASE_Y1 - BASE_T  # 받침판 앞면 (−39)
PAD_Y1 = door_plate_y0  # 패드 뒷면, 도어 판 앞면 (−51)
PAD_Y0 = PAD_Y1 - PAD_T  # 패드 앞면 (−59)
ARM_Y1 = PAD_Y0 - SPINDLE_GAP  # 암 뒷면 (−69)
ARM_Y0 = ARM_Y1 - ARM_T  # 암 앞면 (−77)
SPINDLE_Y1 = PAD_Y0  # 스핀들 뒤 끝, 패드 앞면 (−59)
SPINDLE_Y0 = ARM_Y0 - SPINDLE_TOP  # 스핀들 앞 끝 (−87)
BODY_Y1 = BASE_Y0  # 몸체 뒷면, 받침판 앞면 (−39)
BODY_Y0 = ARM_Y0  # 몸체 앞면, 암 앞면과 같은 높이 (−77)
LEVER_Y1 = BODY_Y0  # 레버 막대 뒤 끝, 몸체 앞면 (−77)
LEVER_Y0 = LEVER_Y1 - LEVER_H  # 레버 막대 앞 끝 = 손잡이 덮개 뒤 끝 (−113)
GRIP_Y0 = LEVER_Y0 - GRIP_L  # 손잡이 덮개 앞 끝 (−153)
LEVER_CX = BODY_X0 + LEVER_W / 2  # 레버 막대·손잡이 덮개 축 x (−15)


def _box(x0, x1, y0, y1, z0, z1):
    box = bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    return box.moved(bd.Location((x0, y0, z0)))


def _cyl_y(cx, cz, dia, y0, y1):
    """축이 y 방향이고 (cx, cz)를 지나는 원기둥, y0–y1."""
    return bd.Solid.make_cylinder(dia / 2, y1 - y0, plane=bd.Plane(origin=(cx, y0, cz), z_dir=(0, 1, 0)))


def _dist_to_rect(cx, cz, x0, x1, z0, z1):
    """점 (cx, cz)에서 사각형 [x0, x1] × [z0, z1]까지 거리(안이면 0)."""
    dx = max(x0 - cx, 0.0, cx - x1)
    dz = max(z0 - cz, 0.0, cz - z1)
    return (dx * dx + dz * dz) ** 0.5


def base_plate(i: int, zc: float) -> tuple[bd.Solid, list]:
    """받침판과, 그 밑면에 머리 자리를 판 볼트 구멍 중심 목록."""
    z0, z1 = zc - BASE_LZ / 2, zc + BASE_LZ / 2
    plate = _box(BASE_X0, BASE_X1, BASE_Y0, BASE_Y1, z0, z1)
    under = []
    for hx, hz in bolt_holes()["panel_front"]:
        d = _dist_to_rect(hx, hz, BASE_X0, BASE_X1, z0, z1)
        if d >= spacer_head_dia / 2:
            continue  # 볼트 머리 원이 받침판에 걸리지 않는다
        if d >= panel_bolt_hole_dia / 2:
            raise ValueError(f"clamp_{i}: 볼트 ({hx}, {hz})의 머리가 받침판 가장자리에 걸리지만 구멍은 받침판 밖이다 — 받침판 크기를 바꿔야 한다")
        inside = BASE_X0 + spacer_head_dia / 2 <= hx <= BASE_X1 - spacer_head_dia / 2 and z0 + spacer_head_dia / 2 <= hz <= z1 - spacer_head_dia / 2
        if not inside:
            raise ValueError(f"clamp_{i}: 볼트 ({hx}, {hz})의 머리 자리가 받침판 밖으로 빠져나간다 — 받침판 크기를 바꿔야 한다")
        recess = _cyl_y(hx, hz, spacer_head_dia, BASE_Y1 - spacer_head_depth, BASE_Y1)
        plate = plate - recess
        under.append((hx, hz))
    plate.label = f"clamp_{i}_base"
    return plate, under


def clamp(i: int, zc: float) -> tuple[bd.Compound, list]:
    base, under = base_plate(i, zc)
    body = _box(BODY_X0, BASE_X1, BODY_Y0, BODY_Y1, zc - BODY_W / 2, zc + BODY_W / 2)
    body.label = f"clamp_{i}_body"
    spindle = _cyl_y(PAD_X, zc, SPINDLE_DIA, SPINDLE_Y0, SPINDLE_Y1)
    spindle.label = f"clamp_{i}_spindle"
    arm = _box(BASE_X1, PAD_X + ARM_TIP, ARM_Y0, ARM_Y1, zc - ARM_W / 2, zc + ARM_W / 2) - spindle
    arm.label = f"clamp_{i}_arm"
    lever = _box(BODY_X0, BODY_X0 + LEVER_W, LEVER_Y0, LEVER_Y1, zc - LEVER_W / 2, zc + LEVER_W / 2) + _cyl_y(LEVER_CX, zc, GRIP_DIA, GRIP_Y0, LEVER_Y0)
    lever.label = f"clamp_{i}_lever"
    pad = _cyl_y(PAD_X, zc, PAD_DIA, PAD_Y0, PAD_Y1)
    pad.label = f"clamp_{i}_pad"
    parts = [base, body, arm, lever, spindle, pad]
    for p in parts:
        if not p.is_valid or len(p.solids()) != 1:
            raise ValueError(f"{p.label} 솔리드가 올바르지 않다 (solids {len(p.solids())})")
    return bd.Compound(children=parts, label=f"clamp_{i}"), under


@step(out="../step/toggle_clamp.step")
def toggle_clamp():
    assert len(clamp_z) == clamp_N
    assert BASE_T > spacer_head_depth, "받침판이 머리 자리 깊이보다 얇다"
    assert PAD_DIA <= gasket_W, "패드가 밀폐재 띠 폭보다 넓다"
    assert door_plate_x0 < PAD_X - PAD_DIA / 2, "패드가 도어 판 왼쪽 끝 밖으로 나간다"
    assert min(BASE_X0, BODY_X0, LEVER_CX - GRIP_DIA / 2) >= frame_x0, "클램프가 앞면 패널 외곽(x −30) 밖으로 나간다"
    assert BODY_X0 + LEVER_W <= BASE_X1 and SPINDLE_Y0 < ARM_Y0 and ARM_Y1 < SPINDLE_Y1
    clamps = []
    for i, zc in enumerate(clamp_z, 1):
        c, under = clamp(i, zc)
        print(f"clamp_{i}_base: 밑면 아래 볼트 구멍 {under if under else '없음 — 머리 자리를 파지 않는다'}")
        clamps.append(c)
    return bd.Compound(children=clamps)


if __name__ == "__main__":
    toggle_clamp()
