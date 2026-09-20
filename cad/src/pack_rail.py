"""팩 받침 레일.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 3030 B형 슬롯 8 프로파일(step.parts `profile_3030_b_slot8`)의 끝면 단면을 `chamber_frame.py`와 같은 방법으로 늘여, 깊이 방향 레일 2줄과 레일 양 끝 밑의 세로 다리 4개를 만든다. 레일 윗면이 더미 팩 밑면(z rail_H)이고, 다리 밑면이 바닥 보강재 윗면(z 0)이다.

레일과 다리의 이음 브래킷은 그리지 않는다(사용자 결정 2026-10-07).
"""

from __future__ import annotations

from cadgen import build123d as bd
from cadgen import step

from chamber_frame import member, profile_section
from params import leg_H, leg_y, leg_z0, prof_W, rail_cx, rail_H, rail_L, rail_y0, rail_y1, rail_z0


@step(out="../step/pack_rail.step")
def pack_rail():
    section = profile_section()
    parts = []
    for cx, lr in zip(rail_cx, ("L", "R")):
        x0 = cx - prof_W / 2  # 레일·다리 x 시작 — 185, 1115
        # 레일, 깊이 방향 y 80–890, z 70–100
        parts.append(member(section, "y", x0, rail_y0, rail_z0, rail_L, f"rail_{lr}"))
        # 다리 2개, 레일 양 끝 밑 z 0–70
        for (y0, _), fb in zip(leg_y, ("F", "B")):
            parts.append(member(section, "z", x0, y0, leg_z0, leg_H, f"leg_{lr}{fb}"))

    rails = bd.Compound(children=parts)
    bb = rails.bounding_box()
    want = (rail_cx[0] - prof_W / 2, rail_y0, leg_z0, rail_cx[1] + prof_W / 2, rail_y1, rail_H)
    got = (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)
    if max(abs(g - w) for g, w in zip(got, want)) > 1e-6:
        raise ValueError(f"받침 레일 외곽 {got}이 {want}와 다르다")
    return rails


if __name__ == "__main__":
    pack_rail()
