"""조립품.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)를 그대로 쓴다. 부품 모델은 모두 이 좌표계에서 조립 위치에 놓인 채로 모델링되어 있으므로, 조립품은 각 모델을 불러 옮기지 않고 한 문서로 묶는다. 벤더 STEP으로 더하는 것은 SEN55 3대뿐이고, `sen55_bracket.sen55_location(i)`로 브래킷 i에 놓는다. ESP32 모듈은 `control_board`가 이미 갖고 있고, 캐스터 4개와 글랜드 3개는 `caster` · `cable_gland` 모델이 이미 조립 위치에 놓아 두었다(`cad/parts.md` 조립품 절).

label: 부품 모델마다 모델 이름(pack, chamber_frame, pack_rail, chamber_panel, door, door_gasket, door_hinge, toggle_clamp, door_handle, inlet_port, exhaust_port, sen55_bracket, extender_board, cable_gland, control_board, electronics_box, caster)이고 그 아래는 각 모델의 트리 그대로다. SEN55는 sen55_1(앞, bracket_1), sen55_2(뒤 왼쪽, bracket_2), sen55_3(뒤 오른쪽, bracket_3).

도어 열림: STEP에는 메이트·관절이 실리지 않으므로 열린 모습은 형상을 그 자세로 써서 보여 준다. 열린 조립품이 필요하면 아래 DOOR_ANGLE을 바꾸고 cad/ 안에서 `./cadgen python src/assembly.py`로 다시 빌드한다(저장소 루트에서는 `cad/cadgen python cad/src/assembly.py`). 커밋하는 step/assembly.step은 DOOR_ANGLE = 0(닫힌 상태)으로 빌드한 것이다.

- DOOR_ANGLE은 도(°)이고 0은 닫힌 상태, 양수는 도어를 바깥(−y)으로 연다. 회전축은 경첩 너클 축(door_hinge.AXIS_X, AXIS_Y)을 지나는 +z이고, 양의 각도에서 도어 왼쪽 끝이 −y로 나간다.
- 함께 도는 것은 door, door_handle, hinge_N_leaf_door(N = 1…3)뿐이다. 너클은 축 대칭이라, 프레임 쪽 날개와 받침 블록은 프레임에 붙어 있어 그대로 둔다.
- DOOR_ANGLE > 0이면 토글 클램프 2개를 풀린 자세로 그린다. 누름 암·스핀들·패드(clamp_N_arm, clamp_N_spindle, clamp_N_pad)를 z 방향 회전축 (CLAMP_PIVOT_X, CLAMP_PIVOT_Y)를 중심으로 CLAMP_RELEASE만큼 젖혀(위에서 보아 시계 방향, 암 끝이 −y로) 패드가 도어 앞면에서 떨어지고 도어가 도는 자리에서 비키게 한다. 받침판·몸체·레버는 움직이지 않는다(링크 기구는 그리지 않는다). 회전축 위치와 각도는 작업 가정이다.
- 개체 구조와 label은 각도와 상관없이 같다. 도는 leaf만 자리가 바뀐다.
"""

from __future__ import annotations

import os

from cadgen import build123d as bd
from cadgen import read_step
from cadgen import step

from cable_gland import cable_gland
from caster import caster
from chamber_frame import chamber_frame
from chamber_panel import chamber_panel
from control_board import control_board
from door import door
from door_gasket import door_gasket
from door_handle import door_handle
from door_hinge import AXIS_X, AXIS_Y, door_hinge
from electronics_box import electronics_box
from exhaust_port import exhaust_port
from extender_board import extender_board
from inlet_port import inlet_port
from pack import pack
from pack_rail import pack_rail
from params import clamp_N, hinge_N, sen_N
from sen55_bracket import sen55_bracket, sen55_location
from toggle_clamp import BASE_X1, BODY_Y0, toggle_clamp

DOOR_ANGLE = 0.0  # 도어 열림 각도(도). 0은 닫힌 상태, 양수는 바깥(−y)으로 연다. 0 … DOOR_ANGLE_MAX
DOOR_ANGLE_MAX = 90.0  # 도는 동안의 간섭을 확인한 범위의 끝(도)

CLAMP_PIVOT_DX = 2.0  # 작업 가정 — 사용자 확인 필요. 누름 암 회전축이 몸체 오른쪽 면(x BASE_X1 = 18)에서 왼쪽(−x)으로 들어온 거리
CLAMP_PIVOT_DY = 1.0  # 작업 가정 — 사용자 확인 필요. 누름 암 회전축이 몸체 앞면(y BODY_Y0 = −77)에서 바깥(−y)으로 나온 거리
CLAMP_RELEASE = 150.0  # 작업 가정 — 사용자 확인 필요. 풀린 자세에서 누름 암·스핀들·패드를 젖히는 각도(도), 위에서 보아 시계 방향(암 끝이 −y로)
CLAMP_PIVOT_X = BASE_X1 - CLAMP_PIVOT_DX  # 누름 암 회전축 x (16)
CLAMP_PIVOT_Y = BODY_Y0 - CLAMP_PIVOT_DY  # 누름 암 회전축 y (−78)

SEN55_STEP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step", "imported", "Sensirion_STEP_SEN5x.STEP")

# (label, 모델). 순서는 cad/parts.md의 표 순서(챔버 본체 → 센서부 → 전장부)를 따른다.
MODELS = (
    ("pack", pack),
    ("pack_rail", pack_rail),
    ("chamber_frame", chamber_frame),
    ("chamber_panel", chamber_panel),
    ("door", door),
    ("door_gasket", door_gasket),
    ("door_hinge", door_hinge),
    ("toggle_clamp", toggle_clamp),
    ("door_handle", door_handle),
    ("caster", caster),
    ("inlet_port", inlet_port),
    ("exhaust_port", exhaust_port),
    ("cable_gland", cable_gland),
    ("sen55_bracket", sen55_bracket),
    ("extender_board", extender_board),
    ("control_board", control_board),
    ("electronics_box", electronics_box),
)

# 도어와 함께 도는 leaf의 label.
DOOR_LEAVES = ("door", "door_handle") + tuple(f"hinge_{i}_leaf_door" for i in range(1, hinge_N + 1))
# 풀린 자세에서 젖히는 클램프 leaf의 label.
CLAMP_LEAVES = tuple(f"clamp_{i}_{name}" for i in range(1, clamp_N + 1) for name in ("arm", "spindle", "pad"))


def z_rotation(x: float, y: float, angle: float) -> bd.Location:
    """(x, y)를 지나는 +z 축을 중심으로 angle(도)만큼 도는 강체 이동. 양수는 위에서 보아 반시계 방향."""
    return bd.Location((x, y, 0)) * bd.Location((0, 0, 0), (0, 0, 1), angle) * bd.Location((-x, -y, 0))


def door_location(door_angle: float) -> bd.Location:
    """도어가 door_angle만큼 열린 자리로 옮기는 이동. 경첩 너클 축 기준, 양수에서 도어 왼쪽 끝이 −y로 나간다."""
    return z_rotation(AXIS_X, AXIS_Y, door_angle)


def clamp_release_location() -> bd.Location:
    """누름 암·스핀들·패드를 풀린 자세로 젖히는 이동."""
    return z_rotation(CLAMP_PIVOT_X, CLAMP_PIVOT_Y, -CLAMP_RELEASE)


def _with_moved(shape: bd.Shape, moves: dict[str, bd.Location], found: set[str]) -> bd.Shape:
    """트리를 그대로 두고 label이 moves에 있는 leaf만 그 이동으로 옮긴 사본. 옮길 leaf가 없는 가지는 원래 객체를 그대로 쓴다."""
    children = list(shape.children)
    if not children:
        if shape.label not in moves:
            return shape
        moved = shape.moved(moves[shape.label])
        moved.label = shape.label
        found.add(shape.label)
        return moved
    new_children = [_with_moved(c, moves, found) for c in children]
    if all(n is c for n, c in zip(new_children, children)):
        return shape
    return bd.Compound(children=new_children, label=shape.label)


def build_assembly(door_angle: float) -> bd.Compound:
    """도어가 door_angle(도)만큼 열린 조립품. 0이면 닫힌 상태이고 부품 모델의 출력을 손대지 않는다."""
    if not 0.0 <= door_angle <= DOOR_ANGLE_MAX:
        raise ValueError(f"door_angle {door_angle}은 0 … {DOOR_ANGLE_MAX}° 밖이다")
    moves: dict[str, bd.Location] = {}
    if door_angle > 0.0:
        loc = door_location(door_angle)
        moves.update({label: loc for label in DOOR_LEAVES})
        release = clamp_release_location()
        moves.update({label: release for label in CLAMP_LEAVES})
    found: set[str] = set()
    children = []
    for label, model in MODELS:
        part = model()
        part.label = label
        if moves:
            part = _with_moved(part, moves, found)
        children.append(part)
    if found != set(moves):
        raise ValueError(f"옮길 leaf를 찾지 못했다: {sorted(set(moves) - found)}")
    sen55 = read_step(SEN55_STEP)
    for i in range(1, sen_N + 1):
        module = sen55.moved(sen55_location(i))
        module.label = f"sen55_{i}"
        children.append(module)
    return bd.Compound(children=children, label="assembly")


@step(out="../step/assembly.step")
def assembly():
    return build_assembly(DOOR_ANGLE)


if __name__ == "__main__":
    assembly()
