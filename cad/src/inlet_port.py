"""공용 주입 포트.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 내경 inlet_dia(50) 알루미늄 관을 오른쪽 옆면 깊이 가운데에 플랜지로 달고 끼움형 마개로 닫는다(`cad/chamber.md` 포트 평면 위치·포트 세부 행, 사용자 결정 2026-10-07). 관 축은 x 방향이고 (port_y, port_z) = (485, 510)을 지난다.

관과 플랜지는 한 몸이다. 관은 외경 inlet_tube_OD(56), 안쪽 끝은 오른쪽 패널 안쪽 면 inlet_tube_x0(1410), 바깥 끝은 패널 바깥면에서 port_protrude 나간 inlet_tube_x1(1463)이다. 관이 패널 포트 구멍(관 외경과 같은 Ø56)을 지난다. 플랜지는 외경 port_flange_OD(100) × 두께 port_flange_T(5)이고 패널 바깥면(1413)에 붙어 바깥으로 1418까지 온다. 플랜지에 M5 구멍 port_bolt_N(4)개를 피치원 port_bolt_PCD(80) 위에 낸다.

마개는 관 바깥 끝에 끼운 닫힌 상태로 그린다. 끼움부는 안지름이 관 외경, 벽 port_cap_wall(3), 끼움 깊이 port_cap_depth(20)이고, 끝판 두께도 port_cap_wall이다(포트 세부 행의 "마개 벽 3"). 끼움부 안쪽 면이 관 바깥면에, 끝판 안쪽 면이 관 끝면에 닿는다.

port_parts()가 형상 함수이고, 배기 포트(`exhaust_port.py`)가 같은 함수를 위치와 방향만 바꿔 쓴다.

label: inlet_pipe — 관과 플랜지를 합친 솔리드 하나. inlet_cap — 마개 솔리드 하나.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step

from params import (
    inlet_dia,
    inlet_tube_OD,
    inlet_tube_x0,
    inlet_tube_x1,
    panel_right_x0,
    panel_right_x1,
    port_bolt_N,
    port_bolt_PCD,
    port_cap_depth,
    port_cap_wall,
    port_flange_OD,
    port_flange_T,
    port_protrude,
    port_y,
    port_z,
)

PORT_BOLT_HOLE_DIA = 5.5  # 포트 세부 — 플랜지 M5 볼트 통과 구멍 지름. chamber.md 포트 세부 행은 "M5 구멍 4개 PCD 80 mm"로 지름을 적지 않았다. 코디네이터가 준 값이고 chamber.md · params.py에 자리 잡기를 기다린다
PORT_BOLT_ANGLE0 = 45.0  # 작업 가정 — 사용자 확인 필요. 첫 플랜지 구멍의 각도(°), +y에서 +z 쪽으로 잰다. 구멍을 y·z 축에서 45° 돌린 자리에 둔다


def x_cylinder(radius: float, xa: float, xb: float) -> bd.Solid:
    """축이 x 방향이고 (port_y, port_z)를 지나는 원기둥, x min(xa, xb)–max(xa, xb)."""
    return x_cylinder_at(radius, xa, xb, port_y, port_z)


def x_cylinder_at(radius: float, xa: float, xb: float, yc: float, zc: float) -> bd.Solid:
    """축이 x 방향이고 (yc, zc)를 지나는 원기둥, x min(xa, xb)–max(xa, xb)."""
    x0, x1 = min(xa, xb), max(xa, xb)
    return bd.Solid.make_cylinder(radius, x1 - x0, plane=bd.Plane(origin=(x0, yc, zc), x_dir=(0, 1, 0), z_dir=(1, 0, 0)))


def bolt_hole_centers() -> list[tuple[float, float]]:
    """플랜지 구멍 중심 (y, z). 피치원 port_bolt_PCD 위에 PORT_BOLT_ANGLE0부터 같은 간격."""
    r = port_bolt_PCD / 2
    return [
        (port_y + r * math.cos(math.radians(PORT_BOLT_ANGLE0 + i * 360.0 / port_bolt_N)), port_z + r * math.sin(math.radians(PORT_BOLT_ANGLE0 + i * 360.0 / port_bolt_N)))
        for i in range(port_bolt_N)
    ]


def port_parts(bore: float, tube_OD: float, x_in: float, x_end: float, x_panel_out: float, prefix: str) -> bd.Compound:
    """포트 하나: 관+플랜지 솔리드 `<prefix>_pipe`와 마개 솔리드 `<prefix>_cap`.

    x_in은 관 안쪽 끝(패널 안쪽 면), x_end는 관 바깥 끝, x_panel_out은 패널 바깥면이다. 바깥 방향은 x_in에서 x_end로 가는 쪽이다.
    """
    sign = 1.0 if x_end > x_in else -1.0
    flange_x1 = x_panel_out + sign * port_flange_T  # 플랜지 바깥면
    cap_OD = tube_OD + 2 * port_cap_wall  # 마개 끼움부 바깥지름 (62)
    cap_x0 = x_end - sign * port_cap_depth  # 마개 끼움부 시작 (관 끝에서 안쪽으로 끼움 깊이)
    cap_x1 = x_end + sign * port_cap_wall  # 마개 끝판 바깥면
    assert sign * (x_panel_out - x_in) > 0 and sign * (x_end - flange_x1) > 0, "관이 패널과 플랜지를 지나 바깥으로 나오지 않는다"
    assert sign * (cap_x0 - flange_x1) > 0, "마개가 플랜지에 닿는다"
    assert port_bolt_PCD / 2 - PORT_BOLT_HOLE_DIA / 2 > tube_OD / 2, "플랜지 구멍이 관에 걸린다"
    assert port_bolt_PCD / 2 + PORT_BOLT_HOLE_DIA / 2 < port_flange_OD / 2, "플랜지 구멍이 플랜지 밖으로 나간다"

    # 관+플랜지: 속이 찬 관 외경 원기둥과 플랜지 원판을 합친 뒤 관 내경과 구멍을 뺀다(같은 면끼리 합치는 경우를 피한다).
    pipe = x_cylinder(tube_OD / 2, x_in, x_end) + x_cylinder(port_flange_OD / 2, x_panel_out, flange_x1)
    pipe = pipe - x_cylinder(bore / 2, x_in, x_end)
    for yc, zc in bolt_hole_centers():
        pipe = pipe - x_cylinder_at(PORT_BOLT_HOLE_DIA / 2, x_panel_out - sign, flange_x1 + sign, yc, zc)
    # 마개: 속이 찬 바깥지름 원기둥에서 관이 들어갈 자리(관 외경, 끼움 깊이)를 뺀다.
    cap = x_cylinder(cap_OD / 2, cap_x0, cap_x1) - x_cylinder(tube_OD / 2, cap_x0, x_end)

    parts = []
    for name, body in ((f"{prefix}_pipe", pipe), (f"{prefix}_cap", cap)):
        solids = body.solids()
        if not body.is_valid or len(solids) != 1 or len(solids[0].shells()) != 1:
            raise ValueError(f"{name} 솔리드가 올바르지 않다 (solids {len(solids)})")
        part = solids[0]
        part.label = name
        parts.append(part)
    return bd.Compound(children=parts)


@step(out="../step/inlet_port.step")
def inlet_port():
    assert abs(inlet_tube_x0 - panel_right_x0) < 1e-9 and abs(inlet_tube_x1 - (panel_right_x1 + port_protrude)) < 1e-9
    return port_parts(inlet_dia, inlet_tube_OD, inlet_tube_x0, inlet_tube_x1, panel_right_x1, "inlet")


if __name__ == "__main__":
    inlet_port()
