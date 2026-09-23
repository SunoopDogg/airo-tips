"""조립품.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)를 그대로 쓴다. 부품 모델은 모두 이 좌표계에서 조립 위치에 놓인 채로 모델링되어 있으므로, 조립품은 각 모델을 불러 옮기지 않고 한 문서로 묶는다. 벤더 STEP으로 더하는 것은 SEN55 3대뿐이고, `sen55_bracket.sen55_location(i)`로 브래킷 i에 놓는다. ESP32 모듈은 `control_board`가 이미 갖고 있고, 캐스터 4개와 글랜드 3개는 `caster` · `cable_gland` 모델이 이미 조립 위치에 놓아 두었다(`cad/parts.md` 조립품 절).

label: 부품 모델마다 모델 이름(pack, chamber_frame, pack_rail, chamber_panel, door, door_gasket, door_hinge, toggle_clamp, door_handle, inlet_port, exhaust_port, sen55_bracket, extender_board, cable_gland, control_board, electronics_box, caster)이고 그 아래는 각 모델의 트리 그대로다. SEN55는 sen55_1(앞, bracket_1), sen55_2(뒤 왼쪽, bracket_2), sen55_3(뒤 오른쪽, bracket_3).
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
from door_hinge import door_hinge
from electronics_box import electronics_box
from exhaust_port import exhaust_port
from extender_board import extender_board
from inlet_port import inlet_port
from pack import pack
from pack_rail import pack_rail
from params import sen_N
from sen55_bracket import sen55_bracket, sen55_location
from toggle_clamp import toggle_clamp

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


@step(out="../step/assembly.step")
def assembly():
    children = []
    for label, model in MODELS:
        part = model()
        part.label = label
        children.append(part)
    sen55 = read_step(SEN55_STEP)
    for i in range(1, sen_N + 1):
        module = sen55.moved(sen55_location(i))
        module.label = f"sen55_{i}"
        children.append(module)
    return bd.Compound(children=children, label="assembly")


if __name__ == "__main__":
    assembly()
