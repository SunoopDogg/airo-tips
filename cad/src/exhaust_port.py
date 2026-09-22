"""배기 포트.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 주입 포트와 마주 보는 왼쪽 옆면에 같은 형상으로 단다(`cad/chamber.md` 포트 평면 위치·포트 세부 행, 사용자 결정 2026-10-06, 2026-10-07). 형상은 `inlet_port.py`의 port_parts()를 그대로 쓰고 위치와 바깥 방향(−x)만 바꾼다.

관은 내경 exhaust_dia(50), 외경 exhaust_tube_OD(56)이고, 안쪽 끝은 왼쪽 패널 안쪽 면 exhaust_tube_x1(−30), 바깥 끝은 패널 바깥면(−33)에서 port_protrude 나간 exhaust_tube_x0(−83)이다. 플랜지는 −38–−33, 마개 끼움부는 −83–−63, 끝판은 −86–−83이다.

label: exhaust_pipe — 관과 플랜지를 합친 솔리드 하나. exhaust_cap — 마개 솔리드 하나.
"""

from __future__ import annotations

from cadgen import step

from inlet_port import port_parts
from params import (
    exhaust_dia,
    exhaust_tube_OD,
    exhaust_tube_x0,
    exhaust_tube_x1,
    panel_left_x0,
    panel_left_x1,
    port_protrude,
)


@step(out="../step/exhaust_port.step")
def exhaust_port():
    assert abs(exhaust_tube_x1 - panel_left_x1) < 1e-9 and abs(exhaust_tube_x0 - (panel_left_x0 - port_protrude)) < 1e-9
    return port_parts(exhaust_dia, exhaust_tube_OD, exhaust_tube_x1, exhaust_tube_x0, panel_left_x0, "exhaust")


if __name__ == "__main__":
    exhaust_port()
