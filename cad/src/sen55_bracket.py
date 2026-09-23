"""SEN55 브래킷.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 천장 패널 안쪽 면(panel_top_z0, z 690)에 M4 볼트 2개로 다는 PETG 3D 프린트 브래킷 3개이고, 각각 SEN55 한 대를 큰 면이 천장과 평행하게, 평평한 면이 위로, 커넥터가 천장 중심을 향하게 잡는다. 모듈 윗면은 z sen_top_z(670)이고 윗판 윗면에서 sen_gap(20) 아래다(`cad/chamber.md` SEN55 장착 자세 · 고정 방식, SEN55 높이, brk_wall 행, 사용자 결정 2026-10-07).

브래킷 국소 좌표 (u, v, w) — 원점은 모듈 외곽 52.3 × 43.3의 가운데, 모듈 윗면 높이. u는 모듈 중심에서 천장 중심을 향하는 방향(커넥터 쪽, 모듈 긴 변 방향), w는 위(+z), v = w × u. 이 좌표에서 SEN5x 데이터시트 Figure 7과 벤더 STEP으로 확인한 모듈 배치는 이렇다.
- 커넥터가 있는 짧은 측면은 +u 끝(u +26.15), 커넥터 자체는 그 면의 −v 쪽 절반에 있다.
- 공기 흡입구(사각 그릴과 아래로 튀어나온 후드)와 배출구(팬, Ø19)는 둘 다 +v 쪽 긴 측면에 있다. 흡입구는 −u 쪽(벤더 STEP에서 본체 밑면 아래 후드 u −23.2 … −8.1), 팬 블록은 +u 쪽(데이터시트 27.24 → u −1.09 … +26.15)이고 팬 블록은 본체 밑으로 22.3까지 내려온다.
- −v 쪽 긴 측면은 막힌 면이다.

형상(국소 좌표). 클립 안쪽 치수는 데이터시트 공차의 최대값이다 — 폭 CLIP_W = 43.3 + 0.2 = 43.5, 길이 CLIP_L = 52.3 + 0.4 = 52.7, 본체 두께 CATCH_H = 13.2 + 0.4 = 13.6.
- 윗판: u ±CLIP_L/2, v ±(CLIP_W/2 + brk_wall), w sen_gap − brk_wall … sen_gap. 윗면이 천장 패널 안쪽 면에 닿는다. M4 통과 구멍 Ø4.5 2개.
- 뒤 벽(−v): 막힌 긴 측면을 따라 클립 길이 전체에 선다. 안쪽 면 v −CLIP_W/2. 위 턱(w 0 … brk_wall)이 모듈 윗면 가장자리를 누르고, 아래 걸림(윗면 w −CATCH_H, 아래로 갈수록 좁아지는 경사)이 본체 밑면 가장자리를 받친다. 뒤 벽 바깥면이 P82B715 센서측 기판을 다는 평면이고 M3 통과 구멍 Ø3.2 2개가 있다.
- 앞 팔(+v): 흡입·배출구가 있는 긴 측면에서는 흡입구 후드와 팬 블록 사이의 빈 구간에만 폭 ARM_W의 팔 하나를 세운다. 안쪽 면 v +CLIP_W/2, 위 턱과 아래 걸림은 뒤 벽과 같다. 팔의 걸림이 후드와 팬 블록 사이에 들어가 모듈이 u 방향으로 빠지지 않는다.
- 커넥터 쪽(+u)과 반대쪽(−u) 끝, 아래쪽은 열려 있다. 모듈은 아래에서 밀어 올려 뒤 벽과 팔을 벌리며 끼우고, 팔을 바깥으로 젖혀 뺀다.

다른 부품이 쓰는 자세 함수 — i는 1, 2, 3.
- bracket_location(i): 브래킷 국소 좌표 → 챔버 좌표.
- sen55_location(i): 벤더 STEP `step/imported/Sensirion_STEP_SEN5x.STEP`의 자기 좌표 → 챔버 좌표. `read_step(...).moved(sen55_location(i))`로 쓴다.
- extender_location(i): P82B715 센서측 기판의 자기 좌표 → 챔버 좌표. 기판 자기 좌표는 외곽 모서리가 원점이고 x가 긴 변(ext_W), y가 짧은 변(ext_D), z가 두께(ext_T)이며, z = 0 면이 브래킷 뒤 벽 바깥면에 닿고 +z가 브래킷 바깥쪽이다. 구멍 중심은 기판 자기 좌표 (ext_hole_edge, ext_D/2), (ext_W − ext_hole_edge, ext_D/2)이고 브래킷 M3 구멍과 같은 축이다.

label: bracket_1(앞, sen_xy[0]), bracket_2(뒤 왼쪽, sen_xy[1]), bracket_3(뒤 오른쪽, sen_xy[2]) — 각각 솔리드 하나. 세 개는 같은 형상을 천장 중심 기준으로 120°씩 돌린 배치다.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step

from params import (
    brk_bolt_hole_dia,
    brk_bolt_N,
    brk_wall,
    ceil_cx,
    ceil_cy,
    ext_D,
    ext_hole_dia,
    ext_hole_edge,
    ext_hole_N,
    ext_W,
    panel_top_z0,
    sen_body_T,
    sen_gap,
    sen_L,
    sen_N,
    sen_tol,
    sen_top_z,
    sen_W,
    sen_W_tol_plus,
    sen_xy,
)

# --- 클립 안쪽 치수: 데이터시트 공차의 최대값 (11번 명세, 사용자 결정 2026-10-07) ---
CLIP_W = sen_W + sen_W_tol_plus  # 클립 안쪽 폭, 뒤 벽 안쪽 면과 앞 팔 안쪽 면 사이 (43.5)
CLIP_L = sen_L + sen_tol  # 클립 길이, 윗판과 뒤 벽의 u 길이 (52.7)
CATCH_H = sen_body_T + sen_tol  # 위 턱 아랫면(모듈 윗면)에서 아래 걸림 윗면까지 (13.6)

# --- 데이터시트 Figure 7 참고 치수 ---
FAN_BLOCK_L = 27.24  # 팬 쪽 블록의 u 길이, 커넥터 쪽 끝에서 잰다 (데이터시트 Figure 7 참고 치수)
FAN_BLOCK_U0 = sen_L / 2 - FAN_BLOCK_L  # 팬 블록이 시작하는 u (−1.09)

# --- 작업 가정 — 사용자 확인 필요 ---
LEDGE_D = 2.0  # 작업 가정 — 사용자 확인 필요. 위 턱이 벽 안쪽 면에서 안으로 나온 폭(모듈 윗면에 걸리는 폭)
LIP_D = 1.5  # 작업 가정 — 사용자 확인 필요. 아래 걸림이 벽 안쪽 면에서 안으로 나온 폭(본체 밑면에 걸리는 폭). 걸림 높이는 brk_wall이고 아래로 갈수록 0으로 좁아지는 경사다
ARM_W = 5.0  # 작업 가정 — 사용자 확인 필요. 앞 팔의 u 폭
ARM_UC = -4.6  # 작업 가정 — 사용자 확인 필요. 앞 팔 중심 u. 본체 밑면 아래로 나온 흡입구 후드의 끝(벤더 STEP에서 잰 u −8.1)과 팬 블록 시작(FAN_BLOCK_U0, u −1.09) 사이의 가운데라 양쪽 여유가 약 1 mm다
BOLT_U = 18.0  # 작업 가정 — 사용자 확인 필요. M4 구멍 중심의 u (±), 두 구멍은 v 0 선 위
BOARD_U1 = CLIP_L / 2  # 작업 가정 — 사용자 확인 필요. 기판의 커넥터 쪽 끝 u를 브래킷 끝에 맞춘다(배선을 짧게)
BOARD_W1 = sen_gap - brk_wall  # 작업 가정 — 사용자 확인 필요. 기판 윗변 w를 윗판 아랫면 높이에 맞춘다(구멍이 모듈 위 빈 공간에 와 안쪽에서 너트를 댈 수 있다)
EXT_HOLE_THROUGH = True  # 작업 가정 — 사용자 확인 필요. 뒤 벽의 M3 구멍은 ext_hole_dia(Ø3.2) 통과 구멍이고 안쪽에서 너트로 조인다

# --- 벤더 STEP 좌표의 기준 (step/imported/Sensirion_STEP_SEN5x.STEP에서 잰 값) ---
VENDOR_CENTER_X = -12.75  # 벤더 좌표에서 외곽 43.3 폭의 가운데 x (양 긴 측면 −34.10 · 8.60의 가운데)
VENDOR_CENTER_Z = -6.30  # 벤더 좌표에서 외곽 52.3 길이의 가운데 z (양 끝 면 −32.40 · 19.80의 가운데)
VENDOR_TOP_Y = 7.00  # 벤더 좌표에서 평평한 면의 y
# 벤더 좌표의 방향: 평평한 면의 법선 +y, 커넥터 쪽 끝 면의 법선 −z, 흡입·배출구 쪽 긴 측면의 법선 −x.
# 그러므로 벤더 +x → 국소 −v, 벤더 +y → 국소 +w, 벤더 +z → 국소 −u.

# --- 국소 좌표에서 파생되는 위치 ---
V_IN = CLIP_W / 2  # 벽 안쪽 면의 |v| (21.75)
V_OUT = V_IN + brk_wall  # 벽 바깥면의 |v| (24.25)
W_PLATE1 = sen_gap  # 윗판 윗면 w (20)
W_PLATE0 = W_PLATE1 - brk_wall  # 윗판 아랫면 w (17.5)
W_CATCH = -CATCH_H  # 아래 걸림 윗면 w (−13.6)
W_BOTTOM = W_CATCH - brk_wall  # 벽과 걸림의 아랫면 w (−16.1)
ARM_U0 = ARM_UC - ARM_W / 2  # 앞 팔 −u 끝 (−7.1)
ARM_U1 = ARM_UC + ARM_W / 2  # 앞 팔 +u 끝 (−2.1)
BOARD_U0 = BOARD_U1 - ext_W  # 기판 −u 끝 (−3.65)
BOARD_W0 = BOARD_W1 - ext_D  # 기판 아랫변 w (−2.5)
EXT_HOLE_W = (BOARD_W0 + BOARD_W1) / 2  # 기판 구멍 중심 w, 긴 변 중심선 (7.5)
EXT_HOLE_U = (BOARD_U0 + ext_hole_edge, BOARD_U1 - ext_hole_edge)  # 기판 구멍 중심 u (0.35 · 22.35)


def _box(u0, u1, v0, v1, w0, w1) -> bd.Solid:
    return bd.Solid.make_box(u1 - u0, v1 - v0, w1 - w0).moved(bd.Location((u0, v0, w0)))


def _lip(u0: float, u1: float, side: int) -> bd.Solid:
    """벽 안쪽 면에서 안으로 나온 아래 걸림. side −1은 뒤 벽(−v), +1은 앞 팔(+v). 윗면은 w W_CATCH에서 수평이고 아래로 갈수록 벽 쪽으로 좁아진다."""
    v_wall = side * V_IN
    pts = [(u0, v_wall, W_CATCH), (u0, v_wall - side * LIP_D, W_CATCH), (u0, v_wall, W_BOTTOM)]
    face = bd.Face(bd.Wire.make_polygon(pts, close=True))
    return bd.Solid.extrude(face, bd.Vector(u1 - u0, 0, 0))


def _side(u0: float, u1: float, side: int) -> bd.Solid:
    """벽(또는 팔) 하나와 그 위 턱 · 아래 걸림. 벽은 아래 걸림 아랫면에서 윗판 아랫면까지 선다."""
    v0, v1 = sorted((side * V_IN, side * V_OUT))
    wall = _box(u0, u1, v0, v1, W_BOTTOM, W_PLATE0)
    l0, l1 = sorted((side * V_IN, side * (V_IN - LEDGE_D)))
    ledge = _box(u0, u1, l0, l1, 0.0, brk_wall)
    return wall + ledge + _lip(u0, u1, side)


def bracket_local() -> bd.Solid:
    """국소 좌표의 브래킷 솔리드 하나."""
    plate = _box(-CLIP_L / 2, CLIP_L / 2, -V_OUT, V_OUT, W_PLATE0, W_PLATE1)
    body = plate + _side(-CLIP_L / 2, CLIP_L / 2, -1) + _side(ARM_U0, ARM_U1, +1)
    for u in (-BOLT_U, BOLT_U):
        body = body - bd.Solid.make_cylinder(brk_bolt_hole_dia / 2, W_PLATE1 - W_PLATE0 + 2, plane=bd.Plane(origin=(u, 0, W_PLATE0 - 1), z_dir=(0, 0, 1)))
    for u in EXT_HOLE_U:
        body = body - bd.Solid.make_cylinder(ext_hole_dia / 2, brk_wall + 2, plane=bd.Plane(origin=(u, -V_OUT - 1, EXT_HOLE_W), z_dir=(0, 1, 0)))
    solids = body.solids()
    if not body.is_valid or len(solids) != 1:
        raise ValueError(f"브래킷 솔리드가 올바르지 않다 (solids {len(solids)})")
    return solids[0]


def bracket_location(i: int) -> bd.Location:
    """브래킷 i의 국소 좌표 (u, v, w) → 챔버 좌표. 원점은 (sen_xy[i−1], sen_top_z), u는 천장 중심을 향한다."""
    sx, sy = sen_xy[i - 1]
    dx, dy = ceil_cx - sx, ceil_cy - sy
    r = math.hypot(dx, dy)
    return bd.Location(bd.Plane(origin=(sx, sy, sen_top_z), x_dir=(dx / r, dy / r, 0), z_dir=(0, 0, 1)))


def _vendor_to_local() -> bd.Location:
    """벤더 STEP 좌표 → 국소 좌표. 벤더 (VENDOR_CENTER_X, VENDOR_TOP_Y, VENDOR_CENTER_Z)가 국소 원점에 온다."""
    # 국소 = (−(z − cz), −(x − cx), y − cy). 벤더 원점의 국소 위치가 평면 원점이고, 벤더 x · z 축의 국소 방향이 평면의 x · z 축이다.
    origin = (VENDOR_CENTER_Z, VENDOR_CENTER_X, -VENDOR_TOP_Y)
    return bd.Location(bd.Plane(origin=origin, x_dir=(0, -1, 0), z_dir=(-1, 0, 0)))


def sen55_location(i: int) -> bd.Location:
    """(a) 벤더 STEP SEN55를 브래킷 i에 놓는 변환. 벤더 STEP 자기 좌표 → 챔버 좌표."""
    return bracket_location(i) * _vendor_to_local()


def extender_location(i: int) -> bd.Location:
    """(b) P82B715 센서측 기판을 브래킷 i의 뒤 벽 바깥면에 놓는 변환. 기판 자기 좌표(외곽 모서리 원점, x 긴 변, y 짧은 변, z 두께, z = 0 면이 브래킷에 닿음) → 챔버 좌표."""
    board = bd.Location(bd.Plane(origin=(BOARD_U0, -V_OUT, BOARD_W0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)))
    return bracket_location(i) * board


@step(out="../step/sen55_bracket.step")
def sen55_bracket():
    assert abs(sen_top_z + W_PLATE1 - panel_top_z0) < 1e-9, "윗판 윗면이 천장 패널 안쪽 면에 오지 않는다"
    assert brk_bolt_N == 2 and ext_hole_N == 2 and sen_N == 3 and len(sen_xy) == 3
    assert FAN_BLOCK_U0 < 0 < BOLT_U < CLIP_L / 2 - brk_bolt_hole_dia / 2
    assert ARM_U1 < FAN_BLOCK_U0, "앞 팔이 팬 블록에 걸린다"
    assert LIP_D < LEDGE_D < V_IN and W_PLATE0 > brk_wall, "턱 · 걸림 치수가 맞지 않는다"
    assert EXT_HOLE_THROUGH and EXT_HOLE_W - ext_hole_dia / 2 > brk_wall, "기판 구멍이 위 턱에 걸린다"
    local = bracket_local()
    brackets = []
    for i in range(1, sen_N + 1):
        b = local.moved(bracket_location(i))
        b.label = f"bracket_{i}"
        brackets.append(b)
    return bd.Compound(children=brackets)


if __name__ == "__main__":
    sen55_bracket()
