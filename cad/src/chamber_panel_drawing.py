"""외함 패널 6장의 치수 도면.

`chamber_panel()`을 한 번 불러 label마다 패널 하나를 꺼내고, 쪽마다 그 패널의 바깥면을 본 주 뷰 하나를 그린다. 쪽 순서는 앞 · 뒤 · 왼쪽 · 오른쪽 · 천장 · 바닥이다. 주 뷰는 같은 판의 가공 도면(`chamber_panel_dxf.py`)과 같은 면 · 같은 방향이고, 위치 치수는 DXF 원점과 같은 판의 왼쪽 아래 모서리에서 잰다. cadgen의 `bottom` 뷰는 위쪽이 챔버 −y라 DXF와 180° 다르므로, 바닥 패널은 자기 외곽 가운데를 지나는 z축으로 180° 돌려 그리고 치수 점도 같은 Location으로 옮긴다(cad/CLAUDE.md).

뷰의 오른쪽 · 위쪽 방향은 cadgen의 `VIEW_DIRECTIONS`에서 계산하고, 판의 네 모서리와 구멍의 도면 좌표 (u, v)를 그 방향으로 잰다. 그래서 어느 구멍이 줄의 첫 구멍인지, 어느 모서리가 기준점인지도 형상에서 정해진다. 볼트 구멍은 `bolt_holes()`에서, 포트 · 글랜드 구멍과 지름은 `round_cutouts()`에서, 도어 개구와 바닥 보강재 줄은 params.py에서 가져오고, 치수 값은 cadgen이 형상에서 잰다. 같은 간격 줄에만 `(n× EQ SP)`를 붙이고 n은 그 줄의 구멍 수에서 센다.

치수 줄의 배치는 cadgen의 세 가지 동작에 맞춘다. 첫째, 위쪽 · 왼쪽에 자리를 준 치수는 offset을 줄 수로 세어 `overall()`을 그 바깥에 놓으므로, 그 두 쪽에는 판 변에서 잰 치수(변 거리 15, 첫 구멍 30, 같은 간격 줄)만 두고 판 안쪽 형상(도어 개구, 포트, 글랜드, 보강재 줄)은 아래쪽 · 오른쪽에 둔다. 둘째, 겹침 검사가 세로 치수의 글자를 돌리지 않은 가로 상자로 재므로, 판 높이의 가운데에 글자가 오는 세로 같은 간격 줄은 `overall()`의 세로 치수와 두 줄 넘게 떨어뜨린다. 셋째, 구멍 표기는 뷰 밖으로 수평 지시선을 내므로, 판 안쪽 구멍(포트 · 글랜드)이 있는 쪽은 세로 같은 간격 줄을 왼쪽에 두어 지시선이 오른쪽 치수선을 넘지 않게 하고, 그 밖의 쪽은 오른쪽에 둔다. 볼트 구멍 표기는 오른쪽 치수보다 먼저 넣어 지시선이 판 오른쪽 위 모서리만 넘게 한다(앞 패널은 A3 폭이 모자라 이 순서가 아니면 표기가 틀 밖으로 나간다). 1:5에서 3 mm인 변 거리 15는 글자가 보조선 사이에 들어가지 않으므로, 보조선이 글자 밑만 스치는 위쪽 · 왼쪽에 둔다.

천장 · 바닥 패널(1440 × 1030)은 A3 1:5에서 뷰와 치수 줄이 틀 높이를 넘으므로 A2 1:5로 그린다. 1:10은 Ø6.5가 0.65 mm로 찍혀 쓰지 않는다.
"""

from __future__ import annotations

from cadgen import build123d as bd
from cadgen.eng_drawing import VIEW_DIRECTIONS, Sheet, eng_drawing

from chamber_panel import bolt_holes, chamber_panel, panel_specs, round_cutouts
from params import door_x0, door_x1, door_z0, door_z1, stiff_cx, t_panel

SCALE = 0.2  # 1:5
ROW = 12.0  # 치수 줄 하나의 폭(도면 mm). cadgen이 자리를 정하지 않은 치수를 쌓는 간격과 같다
MATERIAL = f"ALUMINIUM COMPOSITE PANEL {t_panel:g} mm"
NOTES = ["HARDWARE MOUNTING HOLES NOT INCLUDED.", "OUTSIDE FACE SHOWN. DATUM: LOWER LEFT CORNER (= DXF ORIGIN)."]

# 쪽 순서대로 (label, cadgen 뷰 이름, 제목 끝, 180° 돌려 그리는가, 용지, 뷰 왼쪽 아래 모서리의 도면 위치 mm)
PAGES = [
    ("panel_front", "front", "FRONT", False, "A3", (58.0, 92.0)),
    ("panel_back", "back", "BACK", False, "A3", (58.0, 92.0)),
    ("panel_left", "left", "LEFT", False, "A3", (98.0, 92.0)),
    ("panel_right", "right", "RIGHT", False, "A3", (98.0, 92.0)),
    ("panel_top", "top", "TOP", False, "A2", (145.0, 106.0)),
    ("panel_bottom", "bottom", "BOTTOM", True, "A2", (145.0, 106.0)),
]

AXIS = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}


class Page:
    """한 쪽에 그릴 패널. 형상과 치수 점을 같은 Location으로 옮기고, 도면 좌표 (u, v)를 뷰의 오른쪽 · 위쪽 방향으로 잰다."""

    def __init__(self, part, label: str, view_name: str, rotate: bool) -> None:
        if rotate:  # 자기 외곽 가운데를 지나는 z축으로 180°
            c = part.bounding_box().center()
            self.loc = bd.Pos(c.X, c.Y, c.Z) * bd.Rot(0, 0, 180) * bd.Pos(-c.X, -c.Y, -c.Z)
        else:
            self.loc = bd.Location()
        self.shape = part.moved(self.loc)
        self.axes = panel_specs()[label][:2]  # 면 안의 두 축
        direction, up = VIEW_DIRECTIONS[view_name]
        self.toward = bd.Vector(*direction)  # 보는 사람이 선 쪽 = 패널 바깥면 쪽
        self.up = bd.Vector(*up)
        self.right = self.up.cross(self.toward)
        bb = self.shape.bounding_box()
        corners = [bd.Vector(x, y, z) for x in (bb.min.X, bb.max.X) for y in (bb.min.Y, bb.max.Y) for z in (bb.min.Z, bb.max.Z)]
        self.face = max(c.dot(self.toward) for c in corners)  # 바깥면
        self.u0 = min(c.dot(self.right) for c in corners)
        self.v0 = min(c.dot(self.up) for c in corners)
        self.U = max(c.dot(self.right) for c in corners) - self.u0  # 도면 폭
        self.V = max(c.dot(self.up) for c in corners) - self.v0  # 도면 높이

    def point(self, a: float, b: float) -> bd.Vector:
        """패널 면 안 좌표 (a, b)(panel_specs의 두 축, 챔버 좌표)의 바깥면 위 점. 돌린 쪽은 돌린 자리."""
        u, v = self.axes
        p = (self.loc * bd.Pos(*(bd.Vector(*AXIS[u]) * a + bd.Vector(*AXIS[v]) * b))).position
        return p + self.toward * (self.face - p.dot(self.toward))

    def corner(self, su: int, sv: int) -> bd.Vector:
        """판 외곽의 모서리. (0, 0)이 기준점(왼쪽 아래), (1, 1)이 오른쪽 위."""
        return self.right * (self.u0 + su * self.U) + self.up * (self.v0 + sv * self.V) + self.toward * self.face

    def uv(self, p: bd.Vector) -> tuple[float, float]:
        """도면 좌표. 1e-6 mm로 반올림해, 같은 줄의 점이 부동소수 오차로 갈리지 않고 (u, v) 순 정렬이 u의 오차에 휘둘리지 않게 한다."""
        return (round(p.dot(self.right) - self.u0, 6), round(p.dot(self.up) - self.v0, 6))

    def lines(self, pts: list) -> tuple[list, list, list, list]:
        """구멍 점들의 아래 줄 · 위 줄(u 순) · 왼쪽 열 · 오른쪽 열(v 순)."""
        us = [self.uv(p)[0] for p in pts]
        vs = [self.uv(p)[1] for p in pts]
        by_u = lambda ps: sorted(ps, key=lambda p: self.uv(p)[0])
        by_v = lambda ps: sorted(ps, key=lambda p: self.uv(p)[1])
        return (by_u([p for p, v in zip(pts, vs) if v == min(vs)]), by_u([p for p, v in zip(pts, vs) if v == max(vs)]),
                by_v([p for p, u in zip(pts, us) if u == min(us)]), by_v([p for p, u in zip(pts, us) if u == max(us)]))

    def dim(self, view, side: str, row: int, p1: bd.Vector, p2: bd.Vector, text: str | None = None) -> None:
        """p1–p2 치수를 뷰의 side 쪽 row번째 줄에 둔다. cadgen의 offset은 두 점 가운데 바깥쪽 점에서 잰 도면 mm다."""
        (u1, v1), (u2, v2) = self.uv(p1), self.uv(p2)
        offset = {
            "top": ROW * row + (self.V - max(v1, v2)) * SCALE,
            "bottom": -(ROW * row + min(v1, v2) * SCALE),
            "right": ROW * row + (self.U - max(u1, u2)) * SCALE,
            "left": -(ROW * row + min(u1, u2) * SCALE),
        }[side]
        # 모서리에서 잰 offset이 정확히 ROW의 배수가 되게 반올림한다. 1e-14만 모자라도 cadgen이 줄 수를 하나 적게 세어 overall()을 그 줄에 겹친다.
        view.dim(tuple(p1), tuple(p2), offset=round(offset, 6), text=text, orientation="h" if side in ("top", "bottom") else "v")


def eq_sp(line: list) -> str:
    return f"<> ({len(line) - 1}× EQ SP)"


@eng_drawing(out="../pdf/chamber_panel.pdf")
def chamber_panel_drawing():
    parts = {p.label: p for p in chamber_panel().children}
    holes = bolt_holes()
    cutouts = round_cutouts()
    sheets = []
    for label, view_name, side_name, rotate, size, origin in PAGES:
        pg = Page(parts[label], label, view_name, rotate)
        sheet = Sheet(size, scale=SCALE, title=f"CHAMBER PANEL - {side_name}", material=MATERIAL, revision="A",
                      general_tolerance="ISO 2768-m", notes=NOTES)
        view = sheet.view(pg.shape, view_name, at=(origin[0] + pg.U * SCALE / 2, origin[1] + pg.V * SCALE / 2))
        view.overall()

        (bolt_dia, _), *others = cutouts[label]
        bolts = [pg.point(a, b) for a, b in holes[label]]
        bottom_row, top_row, left_col, right_col = pg.lines(bolts)
        bl, br, tl = pg.corner(0, 0), pg.corner(1, 0), pg.corner(0, 1)

        # 볼트 구멍 표기 — 위 줄 맨 오른쪽 구멍에서 수평으로, 판 오른쪽 위 모서리 밖으로
        view.hole(tuple(top_row[-1]), bolt_dia, thru=True, count=len(bolts), angle=0)

        # 왼쪽(안쪽부터): 판 안쪽 구멍이 있으면 세로 같은 간격 줄, 변 거리 15(아래 줄), 첫 구멍 30(왼쪽 열)
        left = [(bl, bottom_row[0], None), (bl, left_col[0], None)]
        if others:
            left.insert(0, (left_col[0], left_col[-1], eq_sp(left_col)))
        for row, (p1, p2, text) in enumerate(left, start=1):
            pg.dim(view, "left", row, p1, p2, text)

        # 위쪽(안쪽부터): 변 거리 15(왼쪽 열), 첫 구멍 30과 위 줄 같은 간격. 천장은 글랜드 줄을 맨 안에 두므로 따로 놓는다
        if label != "panel_top":
            pg.dim(view, "top", 1, tl, left_col[-1])
            pg.dim(view, "top", 2, tl, top_row[0])
            pg.dim(view, "top", 2, top_row[0], top_row[-1], eq_sp(top_row))

        right_row = 1  # 오른쪽에 다음으로 놓을 줄
        callouts = []  # 판 안쪽 구멍 표기 — 오른쪽 치수를 다 놓은 뒤 그 바깥으로 낸다
        if label == "panel_front":
            door_bl, door_tl, door_br, door_tr = sorted(
                (pg.point(a, b) for a in (door_x0, door_x1) for b in (door_z0, door_z1)), key=pg.uv)  # u 다음 v 순
            pg.dim(view, "bottom", 1, bl, door_bl)  # 개구 위치 u
            pg.dim(view, "bottom", 1, door_bl, door_br)  # 개구 폭
            pg.dim(view, "right", right_row, br, door_br)  # 개구 위치 v
            pg.dim(view, "right", right_row, door_br, door_tr)  # 개구 높이
            right_row += 1
        elif label in ("panel_left", "panel_right"):
            (port_dia, port_ab), = others
            port = pg.point(*port_ab[0])
            pg.dim(view, "bottom", 1, bl, port)  # 포트 중심 u
            pg.dim(view, "right", right_row, br, port)  # 포트 중심 v
            right_row += 1
            callouts.append((port, port_dia, None, 45.0))
        elif label == "panel_top":
            # 글랜드 줄의 같은 간격은 글자가 간격보다 넓어 보조선이 글자를 지나므로, 보조선이 글자 밑만 스치는 위쪽 맨 안 줄에 둔다. 위쪽에 자리를 준 치수는 offset이 줄 수로 세어지므로(판 가운데의 글랜드는 열 줄 가까이) 위쪽 둘은 자리를 정하지 않고 쌓는다. 같은 까닭에 첫 구멍 30과 볼트 줄 같은 간격은 아래쪽에 둔다
            (gland_dia, gland_ab), = others
            glands = sorted((pg.point(a, b) for a, b in gland_ab), key=pg.uv)
            view.dim(tuple(glands[0]), tuple(glands[-1]), text=eq_sp(glands), orientation="h")
            view.dim(tuple(tl), tuple(left_col[-1]), orientation="h")  # 변 거리 15(왼쪽 열)
            pg.dim(view, "bottom", 1, bl, glands[0])  # 첫 글랜드 구멍 u
            pg.dim(view, "bottom", 2, bl, bottom_row[0])  # 첫 구멍 30
            pg.dim(view, "bottom", 2, bottom_row[0], bottom_row[-1], eq_sp(bottom_row))
            pg.dim(view, "right", right_row, br, glands[-1])  # 글랜드 줄 v
            right_row += 1
            # 지시선은 끝 구멍의 위에서 나가 글랜드 줄 v의 보조선과 떨어진다
            callouts.append((glands[-1], gland_dia, len(glands), 90.0))
        elif label == "panel_bottom":
            cols = {}  # 보강재 줄마다 구멍
            for a, b in holes[label]:
                if a in stiff_cx:
                    p = pg.point(a, b)
                    cols.setdefault(pg.uv(p)[0], []).append(p)
            for row, u in enumerate(sorted(cols), start=1):
                pg.dim(view, "bottom", row, bl, min(cols[u], key=pg.uv))  # 보강재 줄 u
        if not others:
            pg.dim(view, "right", right_row, right_col[0], right_col[-1], eq_sp(right_col))  # 세로 같은 간격 줄
        for centre, dia, count, angle in callouts:
            view.hole(tuple(centre), dia, thru=True, count=count, angle=angle)
        sheets.append(sheet)
    return sheets


if __name__ == "__main__":
    chamber_panel_drawing()
