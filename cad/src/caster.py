"""캐스터.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 바퀴 지름 caster_wheel_dia(100)의 브레이크 달린 회전 캐스터 caster_N(4)개를 바닥 패널 아래 네 모서리에 단다(`cad/chamber.md` 캐스터 모델 · 바퀴 지름 행, 사용자 결정 2026-10-06, 2026-10-07). step.parts `locking_swivel_caster_wheel_d100`은 바퀴가 장착판을 뚫고 올라오는 결함 모델이라 쓰지 않고, 흔한 브레이크 달린 회전 캐스터(사각 장착판 + 회전부 + 포크 + 바퀴 + 브레이크 페달)의 대표 형상을 단순 솔리드로 직접 그린다(루프 중 추천안 자동 선택, 사용자 확인 대기). 장착판·회전부·포크·바퀴 폭·전체 높이·오프셋·페달 치수는 아래의 작업 가정이다.

장착판 윗면이 바닥 패널 아랫면 caster_mount_z(−33)에 붙고, 장착판의 바깥 두 변이 외형 모서리(out_x0 또는 out_x1, out_y0 또는 out_y1)에 맞는다. 회전축은 장착판 중심을 지나는 z축이다. 아래로 회전부 원판, 포크 머리판, 포크 다리 둘이 이어지고, 다리 아래 끝을 꿰는 x 방향 차축에 바퀴가 걸린다. 바퀴는 굴러가는 방향이 y인 자세(차축이 x 방향)다. 회전 캐스터의 자세는 정해져 있지 않으므로, 바퀴가 외형 밖으로 나가지 않게 차축을 회전축에서 챔버 안쪽(앞쪽 캐스터는 +y, 뒤쪽 캐스터는 −y)으로 OFFSET만큼 뒤에 둔 자세로 그린다. 브레이크 페달은 바퀴 반대쪽(바깥쪽)에서 포크 머리판 앞면에 붙고, 발로 밟을 수 있게 끝이 장착판 바깥 변(= 외형 변) 밖으로 PEDAL_OUT만큼 나온다.

장착 구멍 4개는 정사각 배치다. 바깥쪽 두 줄은 장착판 바깥 변에서 t_panel + prof_W / 2(18) 안쪽, 즉 장착판 위 골조 프로파일(바닥 수평재·세로재)의 중심선 위에 오고, 안쪽 두 줄은 장착판 안쪽 변에서 같은 거리다.

장착판 평면 외곽 아래에 바닥 패널 볼트 구멍(chamber_panel.bolt_holes()의 panel_bottom)의 Ø panel_bolt_hole_dia 원이 걸리면, 그 구멍 중심에 버튼 볼트 머리 자리 Ø spacer_head_dia × 깊이 spacer_head_depth를 장착판 윗면에서 판다(경첩 받침 블록·토글 클램프 받침판과 같은 머리 자리). 머리 자리가 장착판 밖으로 빠져나가거나, 볼트 머리 원이 장착판에 걸리는데 머리 자리를 파지 않게 되면 빌드를 멈춘다. 나사산, 볼 베어링, 킹핀, 브레이크 내부 기구는 그리지 않는다.

label: caster_FL(x −33, y −33 모서리), caster_FR(x 1413, y −33), caster_BL(x −33, y 1003), caster_BR(x 1413, y 1003)은 각각 장착판·회전부·포크·바퀴·브레이크 다섯 솔리드(caster_XX_plate, caster_XX_swivel, caster_XX_fork, caster_XX_wheel, caster_XX_brake)를 담은 compound다. 포크는 머리판·다리 둘·차축·차축 머리 둘을 합친 한 솔리드이고, 바퀴에는 차축 지름의 구멍을 뚫어 두 솔리드가 부피로 겹치지 않고 차축 원통면과 바퀴 허브 옆면으로 맞닿는다. 나머지도 면으로만 맞닿는다(장착판 ↔ 회전부 ↔ 포크 머리판, 페달 ↔ 포크 머리판 앞면).
"""

from __future__ import annotations

from cadgen import build123d as bd
from cadgen import srgb
from cadgen import step

from chamber_panel import bolt_holes
from params import (
    caster_mount_z,
    caster_N,
    caster_wheel_dia,
    out_x0,
    out_x1,
    out_y0,
    out_y1,
    panel_bolt_hole_dia,
    prof_W,
    spacer_head_depth,
    spacer_head_dia,
    t_panel,
)
from style import hardware, rubber

# 크기는 모두 작업 가정 — 사용자 확인 필요. 흔한 바퀴 지름 100 mm 브레이크 회전 캐스터를 본뜬 대표값이다.
PLATE_L = 100.0  # 작업 가정 — 사용자 확인 필요. 장착판 한 변(정사각, x = y)
PLATE_T = 6.0  # 작업 가정 — 사용자 확인 필요. 장착판 두께. 머리 자리 깊이(4)보다 두꺼워야 한다
MOUNT_HOLE_DIA = 9.0  # 작업 가정 — 사용자 확인 필요. 장착 구멍 지름(M8 통과 구멍)
CASTER_H = 128.0  # 작업 가정 — 사용자 확인 필요. 캐스터 전체 높이, 바닥 접지면에서 장착판 윗면까지
OFFSET = 35.0  # 작업 가정 — 사용자 확인 필요. 회전축과 차축 사이 수평 거리(y)
SWIVEL_DIA = 64.0  # 작업 가정 — 사용자 확인 필요. 회전부(베어링 레이스) 원판 지름
SWIVEL_H = 8.0  # 작업 가정 — 사용자 확인 필요. 회전부 원판 높이
CROWN_T = 5.0  # 작업 가정 — 사용자 확인 필요. 포크 머리판 두께
CROWN_LEAD = 25.0  # 작업 가정 — 사용자 확인 필요. 포크 머리판이 회전축에서 바퀴 반대쪽으로 나간 길이(y)
LEG_T = 4.0  # 작업 가정 — 사용자 확인 필요. 포크 다리 두께(x)
LEG_BOSS_R = 15.0  # 작업 가정 — 사용자 확인 필요. 포크 다리 아래 끝(차축 둘레) 반지름
WHEEL_W = 32.0  # 작업 가정 — 사용자 확인 필요. 바퀴 트레드 폭(x)
HUB_DIA = 26.0  # 작업 가정 — 사용자 확인 필요. 바퀴 허브 지름. 다리 아래 끝(Ø30) 안에 들도록 그보다 작게 골랐다
HUB_PROTRUDE = 2.0  # 작업 가정 — 사용자 확인 필요. 허브가 트레드 옆면 밖으로 나온 길이(한쪽). 허브 옆면이 다리 안쪽 면에 닿는다
AXLE_DIA = 10.0  # 작업 가정 — 사용자 확인 필요. 차축 지름
AXLE_HEAD_DIA = 16.0  # 작업 가정 — 사용자 확인 필요. 차축 머리·너트를 본뜬 원판 지름
AXLE_HEAD_T = 3.0  # 작업 가정 — 사용자 확인 필요. 차축 머리·너트를 본뜬 원판 두께(x)
PEDAL_W = 30.0  # 작업 가정 — 사용자 확인 필요. 브레이크 페달 폭(x)
PEDAL_T = 4.0  # 작업 가정 — 사용자 확인 필요. 브레이크 페달 두께(z)
PEDAL_OUT = 30.0  # 작업 가정 — 사용자 확인 필요. 페달 끝이 장착판 바깥 변(= 외형 변) 밖으로 나간 길이. 흔한 캐스터의 20–30 범위에서 위쪽 끝을 골랐다: 드러난 발판이 30 × 30이 되고, 앞쪽 캐스터는 도어 판 앞면(y −51)보다 12 더 나와 도어 판 밑에 들지 않는 발판이 생기며, 끝(y −63)이 토글 클램프 레버(y −153)·손잡이(y −88)보다 안쪽이라 앞쪽 외곽을 넓히지 않는다

# 장착 구멍 바깥 줄 — 외형 모서리에서 골조 프로파일 중심선까지 (18). 값은 params에서 계산하지만, 바깥 줄을 프로파일 중심선에 두고 안쪽 줄을 안쪽 변에서 같은 거리에 두는 배치 선택은 작업 가정 — 사용자 확인 필요
HOLE_INSET = t_panel + prof_W / 2

# z는 장착판 윗면(−33)에서 아래로 쌓는다.
PLATE_Z1 = caster_mount_z  # 장착판 윗면, 바닥 패널 아랫면 (−33)
PLATE_Z0 = PLATE_Z1 - PLATE_T  # 장착판 밑면 (−39)
SWIVEL_Z1 = PLATE_Z0  # 회전부 윗면 (−39)
SWIVEL_Z0 = SWIVEL_Z1 - SWIVEL_H  # 회전부 밑면 (−47)
CROWN_Z1 = SWIVEL_Z0  # 포크 머리판 윗면 (−47)
CROWN_Z0 = CROWN_Z1 - CROWN_T  # 포크 머리판 밑면 (−52)
GROUND_Z = PLATE_Z1 - CASTER_H  # 바닥 접지면, 바퀴 맨 아래 (−161)
AXLE_Z = GROUND_Z + caster_wheel_dia / 2  # 차축 z (−111)
WHEEL_TOP_Z = AXLE_Z + caster_wheel_dia / 2  # 바퀴 맨 위 (−61)
PEDAL_Z0 = CROWN_Z0  # 페달 밑면, 머리판 밑면과 같다 (−52)
PEDAL_Z1 = PEDAL_Z0 + PEDAL_T  # 페달 윗면 (−48)

# x는 회전축(cx)에서 양쪽으로 잰다.
LEG_IN = WHEEL_W / 2 + HUB_PROTRUDE  # 다리 안쪽 면, 허브 옆면 (18)
LEG_OUT = LEG_IN + LEG_T  # 다리 바깥 면, 머리판 옆면 (22)
AXLE_OUT = LEG_OUT + AXLE_HEAD_T  # 차축 머리 바깥 면 (25)

# t는 회전축에서 바퀴 쪽(챔버 안쪽)으로 잰 수평 거리다.
CROWN_T0 = -CROWN_LEAD  # 머리판 앞(바깥) 끝, 페달이 붙는 면 (−25)
CROWN_T1 = OFFSET + LEG_BOSS_R  # 머리판 뒤(안쪽) 끝, 다리 아래 끝 원의 바깥 접선 (50)
PEDAL_T0 = -(PLATE_L / 2 + PEDAL_OUT)  # 페달 끝 (−80)

# 이름, 모서리 x, x 방향(−1이면 모서리가 x 최소 쪽), 모서리 y, y 방향
CORNERS = (
    ("caster_FL", out_x0, -1, out_y0, -1),
    ("caster_FR", out_x1, +1, out_y0, -1),
    ("caster_BL", out_x0, -1, out_y1, +1),
    ("caster_BR", out_x1, +1, out_y1, +1),
)


def _box(x0, x1, y0, y1, z0, z1):
    box = bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    return box.moved(bd.Location((x0, y0, z0)))


def _cyl_x(cy, cz, dia, x0, x1):
    """축이 x 방향이고 (cy, cz)를 지나는 원기둥, x0–x1."""
    return bd.Solid.make_cylinder(dia / 2, x1 - x0, plane=bd.Plane(origin=(x0, cy, cz), z_dir=(1, 0, 0)))


def _cyl_z(cx, cy, dia, z0, z1):
    """축이 z 방향이고 (cx, cy)를 지나는 원기둥, z0–z1."""
    return bd.Solid.make_cylinder(dia / 2, z1 - z0, plane=bd.Plane(origin=(cx, cy, z0), z_dir=(0, 0, 1)))


def _span(corner, sign, length):
    """모서리 corner에서 안쪽(−sign)으로 length만큼의 구간 (작은 값, 큰 값)."""
    return (corner, corner + length) if sign < 0 else (corner - length, corner)


def _dist_to_rect(px, py, x0, x1, y0, y1):
    """점 (px, py)에서 사각형 [x0, x1] × [y0, y1]까지 거리(안이면 0)."""
    dx = max(x0 - px, 0.0, px - x1)
    dy = max(y0 - py, 0.0, py - y1)
    return (dx * dx + dy * dy) ** 0.5


def mount_holes(cx0, sx, cy0, sy):
    """장착 구멍 4개 중심. 바깥 줄은 외형 모서리에서 HOLE_INSET, 안쪽 줄은 PLATE_L − HOLE_INSET."""
    xs = (cx0 - sx * HOLE_INSET, cx0 - sx * (PLATE_L - HOLE_INSET))
    ys = (cy0 - sy * HOLE_INSET, cy0 - sy * (PLATE_L - HOLE_INSET))
    return [(x, y) for x in xs for y in ys]


def plate(name, cx0, sx, cy0, sy):
    """장착판과, 그 윗면에 머리 자리를 판 바닥 패널 볼트 구멍 중심 목록."""
    x0, x1 = _span(cx0, sx, PLATE_L)
    y0, y1 = _span(cy0, sy, PLATE_L)
    body = _box(x0, x1, y0, y1, PLATE_Z0, PLATE_Z1)
    holes = mount_holes(cx0, sx, cy0, sy)
    for hx, hy in holes:
        body = body - _cyl_z(hx, hy, MOUNT_HOLE_DIA, PLATE_Z0, PLATE_Z1)
    under = []
    for hx, hy in bolt_holes()["panel_bottom"]:
        d = _dist_to_rect(hx, hy, x0, x1, y0, y1)
        if d >= spacer_head_dia / 2:
            continue  # 볼트 머리 원이 장착판에 걸리지 않는다
        if d >= panel_bolt_hole_dia / 2:
            raise ValueError(f"{name}: 볼트 ({hx}, {hy})의 머리가 장착판 가장자리에 걸리지만 구멍은 장착판 밖이다 — 장착판 크기를 바꿔야 한다")
        r = spacer_head_dia / 2
        if not (x0 + r <= hx <= x1 - r and y0 + r <= hy <= y1 - r):
            raise ValueError(f"{name}: 볼트 ({hx}, {hy})의 머리 자리가 장착판 밖으로 빠져나간다 — 장착판 크기를 바꿔야 한다")
        for mx, my in holes:
            if ((mx - hx) ** 2 + (my - hy) ** 2) ** 0.5 < r + MOUNT_HOLE_DIA / 2:
                raise ValueError(f"{name}: 볼트 ({hx}, {hy})의 머리 자리가 장착 구멍 ({mx}, {my})과 겹친다")
        body = body - _cyl_z(hx, hy, spacer_head_dia, PLATE_Z1 - spacer_head_depth, PLATE_Z1)
        under.append((hx, hy))
    body.label = f"{name}_plate"
    body.color = srgb(hardware)
    return body, under


def leg(cx, cy, s, x0):
    """포크 다리 하나. x0–x0+LEG_T 판이고, (t, z) 윤곽은 머리판 구간에서 차축 둘레 원으로 내려온다."""
    def p(t, z):
        return bd.Vector(x0, cy + s * t, z)

    outline = [
        p(CROWN_T0, CROWN_Z1),
        p(CROWN_T1, CROWN_Z1),
        p(CROWN_T1, AXLE_Z),
        p(OFFSET - LEG_BOSS_R, AXLE_Z),
        p(CROWN_T0, CROWN_Z0),
    ]
    face = bd.Face(bd.Wire.make_polygon(outline, close=True))
    web = bd.Solid.extrude(face, bd.Vector(LEG_T, 0, 0))
    boss = _cyl_x(cy + s * OFFSET, AXLE_Z, 2 * LEG_BOSS_R, x0, x0 + LEG_T)
    return web + boss


def fork(name, cx, cy, s):
    """머리판 + 다리 둘 + 차축 + 차축 머리 둘을 합친 솔리드."""
    t0, t1 = sorted((cy + s * CROWN_T0, cy + s * CROWN_T1))
    body = _box(cx - LEG_OUT, cx + LEG_OUT, t0, t1, CROWN_Z0, CROWN_Z1)
    body = body + leg(cx, cy, s, cx - LEG_OUT) + leg(cx, cy, s, cx + LEG_IN)
    ay = cy + s * OFFSET
    body = body + _cyl_x(ay, AXLE_Z, AXLE_DIA, cx - LEG_OUT, cx + LEG_OUT)
    body = body + _cyl_x(ay, AXLE_Z, AXLE_HEAD_DIA, cx - AXLE_OUT, cx - LEG_OUT)
    body = body + _cyl_x(ay, AXLE_Z, AXLE_HEAD_DIA, cx + LEG_OUT, cx + AXLE_OUT)
    body.label = f"{name}_fork"
    body.color = srgb(hardware)
    return body


def wheel(name, cx, cy, s):
    """트레드 원기둥 + 양쪽 허브, 가운데에 차축 구멍."""
    ay = cy + s * OFFSET
    body = _cyl_x(ay, AXLE_Z, caster_wheel_dia, cx - WHEEL_W / 2, cx + WHEEL_W / 2)
    body = body + _cyl_x(ay, AXLE_Z, HUB_DIA, cx - LEG_IN, cx + LEG_IN)
    body = body - _cyl_x(ay, AXLE_Z, AXLE_DIA, cx - LEG_IN, cx + LEG_IN)
    body.label = f"{name}_wheel"
    body.color = srgb(rubber)
    return body


def brake(name, cx, cy, s):
    """머리판 앞면(t = CROWN_T0)에서 바깥으로 장착판 바깥 변 밖 PEDAL_OUT까지 나온 페달 판."""
    y0, y1 = sorted((cy + s * PEDAL_T0, cy + s * CROWN_T0))
    body = _box(cx - PEDAL_W / 2, cx + PEDAL_W / 2, y0, y1, PEDAL_Z0, PEDAL_Z1)
    body.label = f"{name}_brake"
    body.color = srgb(hardware)
    return body


def one_caster(name, cx0, sx, cy0, sy):
    x0, x1 = _span(cx0, sx, PLATE_L)
    y0, y1 = _span(cy0, sy, PLATE_L)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2  # 회전축, 장착판 중심
    s = -sy  # 바퀴 쪽, 챔버 안쪽
    base, under = plate(name, cx0, sx, cy0, sy)
    swivel = _cyl_z(cx, cy, SWIVEL_DIA, SWIVEL_Z0, SWIVEL_Z1)
    swivel.label = f"{name}_swivel"
    swivel.color = srgb(hardware)
    parts = [base, swivel, fork(name, cx, cy, s), wheel(name, cx, cy, s), brake(name, cx, cy, s)]
    for part in parts:
        if not part.is_valid or len(part.solids()) != 1:
            raise ValueError(f"{part.label} 솔리드가 올바르지 않다 (solids {len(part.solids())})")
    return bd.Compound(children=parts, label=name), under


@step(out="../step/caster.step")
def caster():
    assert len(CORNERS) == caster_N
    assert PLATE_T > spacer_head_depth, "장착판이 머리 자리 깊이보다 얇다"
    assert WHEEL_TOP_Z < CROWN_Z0, "바퀴가 포크 머리판에 닿는다"
    assert OFFSET - caster_wheel_dia / 2 >= -PLATE_L / 2, "바퀴가 장착판 바깥 변(외형) 밖으로 나간다"
    assert HUB_DIA < 2 * LEG_BOSS_R and AXLE_DIA < HUB_DIA and AXLE_HEAD_DIA < 2 * LEG_BOSS_R
    assert PEDAL_W / 2 < LEG_IN, "페달이 다리와 겹친다"
    assert SWIVEL_DIA / 2 < PLATE_L / 2 and LEG_OUT < SWIVEL_DIA / 2
    assert -PEDAL_T0 > CROWN_LEAD and PEDAL_Z1 < CROWN_Z1
    assert AXLE_Z - LEG_BOSS_R > GROUND_Z and AXLE_Z - AXLE_HEAD_DIA / 2 > GROUND_Z, "포크가 바퀴보다 아래로 내려간다"
    casters = []
    for name, cx0, sx, cy0, sy in CORNERS:
        c, under = one_caster(name, cx0, sx, cy0, sy)
        print(f"{name}_plate: 윗면 아래 바닥 패널 볼트 구멍 {under if under else '없음 — 머리 자리를 파지 않는다'}")
        casters.append(c)
    return bd.Compound(children=casters)


if __name__ == "__main__":
    caster()
