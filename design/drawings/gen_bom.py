#!/usr/bin/env python3
"""지표 3 모의장치 BOM(J3-BM-001) 생성기.

`chamber_params.json`·`sen55_params.json`을 단일 치수 출처로 삼아
`design/지표3-모의장치-설계서.md` 13장 구매·제작 요구사항과 합쳐
`bom.xlsx`(3시트: BOM / 판재 절단표 / 치수 근거)를 만든다.

xlsx 는 zipfile + inlineStr 로 직접 쓴다. 표준 라이브러리만 사용한다.
"""

import json
import math
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
REV = "C"
DRAWING_NO = "J3-BM-001"

# ── 상태 어휘는 chamber_params.json 과 같다 ──────────────────────────────
FIXED = "fixed"
DEPENDENT = "dependent"
UNKNOWN = "unknown"


# ── xlsx 최소 구현 ──────────────────────────────────────────────────────

def _col(i):
    """0-기반 열 번호를 A, B, ... AA 로."""
    s = ""
    while True:
        s = chr(ord("A") + i % 26) + s
        i = i // 26 - 1
        if i < 0:
            return s


def _cell(ref, value, style):
    if value is None or value == "":
        return f'<c r="{ref}" s="{style}"/>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    t = escape(str(value))
    return (f'<c r="{ref}" s="{style}" t="inlineStr">'
            f'<is><t xml:space="preserve">{t}</t></is></c>')


def _sheet_xml(rows, widths, freeze_header=True):
    """(xml, [(셀참조, URL)]) 를 돌려준다. http 로 시작하는 문자열 셀은
    파랑 밑줄 스타일과 실제 하이퍼링크를 함께 받는다."""
    cols = "".join(
        f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(widths)
    )
    body, links = [], []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, v in enumerate(row):
            ref = f"{_col(c)}{r}"
            if r == 1:
                style = 1
            elif isinstance(v, str) and v.startswith("http"):
                style = 3
                links.append((ref, v))
            else:
                style = 2
            cells.append(_cell(ref, v, style))
        body.append(f'<row r="{r}">{"".join(cells)}</row>')
    pane = ('<sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
            'activePane="bottomLeft" state="frozen"/></sheetView>'
            if freeze_header else '<sheetView workbookViewId="0"/>')
    hl = ""
    if links:
        hl = "<hyperlinks>" + "".join(
            f'<hyperlink ref="{ref}" r:id="rId{i}"/>'
            for i, (ref, _) in enumerate(links, start=1)
        ) + "</hyperlinks>"
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheetViews>{pane}</sheetViews>'
        f'<cols>{cols}</cols>'
        f'<sheetData>{"".join(body)}</sheetData>'
        f'{hl}'
        '</worksheet>'
    )
    return xml, links


STYLES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="3">'
    '<font><sz val="10"/><name val="맑은 고딕"/></font>'
    '<font><b/><sz val="10"/><name val="맑은 고딕"/></font>'
    '<font><u/><sz val="10"/><color rgb="FF0563C1"/><name val="맑은 고딕"/></font>'
    '</fonts>'
    '<fills count="3">'
    '<fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFE8E8E8"/>'
    '<bgColor indexed="64"/></patternFill></fill>'
    '</fills>'
    '<borders count="2"><border/>'
    '<border><left style="thin"/><right style="thin"/>'
    '<top style="thin"/><bottom style="thin"/></border></borders>'
    '<cellStyleXfs count="1">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="4">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0"'
    ' applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
    '<alignment vertical="center" horizontal="center" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0"'
    ' applyBorder="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0"'
    ' applyFont="1" applyBorder="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '</cellXfs>'
    '<cellStyles count="1">'
    '<cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    '</styleSheet>'
)


def write_xlsx(path, sheets):
    """sheets: [(이름, rows, widths), ...]"""
    n = len(sheets)
    ct = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, n + 1)
        )
        + '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets>'
        + "".join(
            f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, (name, _, _) in enumerate(sheets, start=1)
        )
        + '</sheets></workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, n + 1)
        )
        + f'<Relationship Id="rId{n+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", STYLES_XML)
        for i, (_, rows, widths) in enumerate(sheets, start=1):
            xml, links = _sheet_xml(rows, widths)
            z.writestr(f"xl/worksheets/sheet{i}.xml", xml)
            if links:
                z.writestr(
                    f"xl/worksheets/_rels/sheet{i}.xml.rels",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    + "".join(
                        f'<Relationship Id="rId{j}" Type="http://schemas.openxmlformats.org/'
                        f'officeDocument/2006/relationships/hyperlink" '
                        f'Target="{escape(url, {chr(34): "&quot;"})}" TargetMode="External"/>'
                        for j, (_, url) in enumerate(links, start=1)
                    )
                    + '</Relationships>',
                )


# ── 파라미터에서 치수 유도 ──────────────────────────────────────────────

def derive(chamber, sen55):
    v = lambda *keys: _dig(chamber, keys)["value"]
    pack_w, pack_d, pack_h = v("pack", "width"), v("pack", "depth"), v("pack", "height")
    c = {k: v("clearance", k) for k in
         ("side_left", "side_right", "front", "rear", "top", "bottom")}
    t = v("enclosure", "wall_thickness")

    inner_w = pack_w + c["side_left"] + c["side_right"]
    inner_d = pack_d + c["front"] + c["rear"]
    inner_h = pack_h + c["top"] + c["bottom"]
    outer_w, outer_d, outer_h = inner_w + 2 * t, inner_d + 2 * t, inner_h + 2 * t

    r = v("sensor_layout", "circumradius")
    return {
        "pack": (pack_w, pack_d, pack_h),
        "clearance": c,
        "t": t,
        "inner": (inner_w, inner_d, inner_h),
        "outer": (outer_w, outer_d, outer_h),
        "door": (v("enclosure", "door_opening_width"),
                 v("enclosure", "door_opening_height")),
        "window": (v("enclosure", "observation_window_width"),
                   v("enclosure", "observation_window_height")),
        "handle_len": v("enclosure", "door_handle_length"),
        "frame_h": v("floor_frame", "height"),
        "elec": (v("electrical_envelope", "width"),
                 v("electrical_envelope", "depth"),
                 v("electrical_envelope", "height")),
        "circumradius": r,
        "triangle_side": r * math.sqrt(3),
        "material": v("enclosure", "material"),
        "sealing": v("enclosure", "sealing_grade"),
        "revision": chamber["meta"]["revision"],
        "sen55_part": _dig(sen55, ("module", "part_number"))["value"],
        "sen55_article": _dig(sen55, ("module", "article_number"))["value"],
        "sen55_conn": _dig(sen55, ("module", "connector"))["value"],
        "sen55_dims": tuple(_dig(sen55, ("module", k))["value"]
                            for k in ("length", "width", "height")),
        "sen55_weight": _dig(sen55, ("module", "weight"))["value"],
        "sen55_rev": sen55["meta"]["revision"],
    }


def _dig(d, keys):
    for k in keys:
        d = d[k]
    return d


def panels(d):
    """판재 절단표. 바닥·천장이 측벽 상하를 덮고 정면·후면판이 측벽 사이에
    끼는 맞대기 구성을 가정한다. 실제 접합 방식은 미정이므로 상태는 dependent."""
    (iw, _id_, ih), (ow, od, _oh) = d["inner"], d["outer"]
    dw, dh = d["door"]
    return [
        ("바닥판", 1, ow, od, FIXED, "외형 바닥면 전체를 덮는다"),
        ("천장판", 1, ow, od, FIXED,
         f"SEN55 3점 취부면. 외접원 R{d['circumradius']:g} 정삼각형"),
        ("측벽판(좌·우)", 2, od, ih, FIXED, "깊이 전장 × 내부 유효 높이"),
        ("후면판", 1, iw, ih, FIXED, "공용 주입 포트 관통(구경 종속값)"),
        ("정면판(도어 프레임)", 1, iw, ih, FIXED,
         f"도어 개구 {dw:g} × {dh:g} 를 도려낸다. 배기 포트 관통(구경 종속값)"),
        ("도어판", 1, dw, dh, DEPENDENT,
         f"개구 {dw:g} × {dh:g} 기준값. 씰 겹침 여유는 접합·개스킷 방식에 종속. "
         f"관찰창 {d['window'][0]:g} × {d['window'][1]:g} 를 도려낸다"),
    ]


# ── 구매 링크 ──────────────────────────────────────────────────────────
#
# 전부 2026-09-08 에 HTTP 200 과 상품명을 직접 확인했다. 검색 결과 제목만 보고
# 넣은 링크는 없다 — 확인 과정에서 판매 보류·삭제로 드러난 후보(디바이스마트
# 1361837·13235312, 엘레파츠 14675992)는 뺐다. 값은 확인 시점의 표시가이며
# VAT 처리는 사이트마다 다르므로 발주 전에 다시 본다.

CHECKED = "2026-09-08"

# 품목키: (구매처, URL, 참고가)
VENDORS = {
    "sen55": ("엘레파츠", "https://www.eleparts.co.kr/goods/view?no=14468287",
              "59,300원 · 재고 1,435 (해외재고 주문수입)"),
    "esp32": ("디바이스마트", "https://www.devicemart.co.kr/goods/view?no=15163693",
              "10,329원 · 재고 22,060 (제조사 ESPRESSIF)"),
    "pca9548a": ("가치창조기술",
                 "https://vctec.co.kr/product/qwiic-mux-pca9548a-i2c-%EB%A9%80%ED%8B%B0%ED%94%8C%EB%A0%89%EC%84%9C-qwiic-mux-pca9548a/11588/",
                 "23,500원 · SparkFun Qwiic Mux 브레이크아웃(베어 칩 아님)"),
    "harness": ("디바이스마트", "https://www.devicemart.co.kr/goods/view?no=15440726",
                "1,980원 · Adafruit ada-5754 JST GH 1.25 6P 100 mm"),
    "usb": ("디바이스마트", "https://www.devicemart.co.kr/goods/view?no=15060748",
            "21,890원 · C-to-C 2 m. 재고 1"),
    "door_sw": ("디바이스마트", "https://www.devicemart.co.kr/goods/view?no=14913058",
                "151,800원 · 큐라이트 SW2TS-LRL 방수형 리미트스위치(IP66) 참고 형번"),
    "smps": ("아이씨뱅큐", "https://www.icbanq.com/P004783185", "20,200원 · 민웰 RS-50-5 (5 V 10 A 50 W) 참고 형번"),
    "mccb": ("디바이스마트", "https://www.devicemart.co.kr/goods/view?no=10893844",
             "3,850원 · 30AF 2P MCCB JSB-1522 (15 A) 참고 형번. 접지바 별도"),
    "gland": ("한국미스미", "https://kr.misumi-ec.com/vona2/detail/110500127270/",
              "형번별 단가 — 케이블 그랜드(금속제) MS-M 시리즈, 외경 확정 후 선정"),
    "gasket": ("한국미스미", "https://kr.misumi-ec.com/vona2/detail/110302683740/",
               "형번별 단가 — 고무·스펀지 패킹 가공품 각형, 씰라인 확정 후 선정"),
    "encl": ("한국미스미",
             "https://kr.misumi-ec.com/vona2/el_control/E1500000000/E1501000000/E1501040000/",
             "형번별 단가 — 스테인리스 제어 박스 카테고리, W120–300×H60–150×D150–400 에서 선정"),
    "made": ("제작 발주", "", ""),
    "none": ("", "", ""),
}


# ── BOM 본문 ────────────────────────────────────────────────────────────

DOC = "설계서 13장"
PARAMS = "chamber_params.json"


def bom_rows(d):
    """모의장치 본체만 담는다.

    챔버 구조물, 챔버 내부의 SEN55 3대, 상판 외부의 수집·전장이 대상이다.
    자극 장비 5종과 매니폴드, 시료 팩, 기록 PC, 카메라, 안전 계통은 이 장치에
    연결되는 별도 품목이므로 제외한다 (사용자 지시 2026-09-08).
    """
    dw, dh = d["door"]
    ww, wh = d["window"]
    ew, ed, eh = d["elec"]
    gasket = 2 * (dw + dh)
    R = [
        # 계층, 품목, 수량, 단위, 요구 사양, 상태, 근거
        ("챔버", "구조 프레임", 1, "식",
         "시료 120 kg 이하 및 부착물 지지, 도어 개폐 시 밀폐면 비틀림 없음, 접지 가능",
         DEPENDENT, "설계서 6.1·13"),
        ("챔버", "받침 프레임", 1, "식",
         f"상면 높이 {d['frame_h']:g} mm. 상면이 팩 저면과 일치", FIXED,
         f"{PARAMS} floor_frame.height"),
        ("챔버", f"벽·천장·바닥 판재 {d['material']} {d['t']:g}t", 1, "식",
         "60 ℃·습기·먼지·DEC·세정 적합성 공급자 자료. 절단 매수·치수는 「판재 절단표」 시트",
         FIXED, f"{PARAMS} enclosure.material·wall_thickness"),
        ("챔버", "도어 + 레버형 다점 래치 핸들", 1, "식",
         f"개구 {dw:g} × {dh:g} mm, 핸들 레버 길이 {d['handle_len']:g} mm, "
         "다점 래치로 둘레 압착 균일화", FIXED, f"{PARAMS} enclosure.door_*"),
        ("챔버", "도어 닫힘 스위치", 1, "ea",
         "안전 계통 하드와이어. 개방 시 DEC 분무·열풍 차단, 고장 안전",
         DEPENDENT, "설계서 6.2·12.2"),
        ("챔버", "관찰창", 1, "ea",
         f"{ww:g} × {wh:g} mm. 내열·내화학·기계강도 자료. 도어판에 설치", FIXED,
         f"{PARAMS} enclosure.observation_window_*"),
        ("챔버", "연속 폐쇄형 개스킷", 1, "식",
         f"도어 둘레 연속. 개구 둘레 {gasket:g} mm 이상이며 실제 길이는 씰라인 오프셋에 종속. "
         "DEC·습기·60 ℃ 적합성", DEPENDENT, "설계서 6.2"),
        ("챔버", "공용 주입 포트", 1, "ea",
         "후면 중·하부. 5개 자극이 외부 매니폴드에서 합류해 들어오는 단일 관통구. "
         "DEC 노즐은 이 포트의 챔버 내측 끝에 둔다. "
         "구경은 장비 토출구·요구 유량·압력손실·누설 시험 결과에 종속",
         DEPENDENT, f"{PARAMS} ports.common_inlet*"),
        ("챔버", "배기 포트", 1, "ea",
         "주입 반대편 정면 상부(대각 관류). 포집 계통 연결. 구경은 위와 같은 종속값",
         DEPENDENT, f"{PARAMS} ports.exhaust*"),
        ("챔버", "케이블 관통판 + 글랜드", 1, "식",
         "측면 하부, 자극 호스와 분리. 최저점은 받침 프레임 상면 이상. "
         "글랜드 구경은 선정 케이블 외경에 종속, 예비구는 막음",
         DEPENDENT, f"{PARAMS} ports.cable_entry*"),
        ("챔버", "블라인드 캡", "확인 항목", "-",
         "미사용 포트를 동일 밀폐 수준으로 폐쇄", DEPENDENT, "설계서 6.3"),
        ("챔버", "잔류액 회수 용기", 1, "식",
         "배수 포트 없음. 퍼지·안전 확인 후 도어 개방 수동 회수. DEC 폐액 호환",
         DEPENDENT, "설계서 6.4·13"),

        ("센싱", f"SEN55 ({d['sen55_part']}, Art. {d['sen55_article']})", 3, "ea",
         "PM1.0/2.5/4.0/10·RH·T·VOC Index·NOx Index 통합 출력으로 완료 정의의 "
         "온도·습도·먼지·오프가스 4종을 대신한다. 설계서 8.1의 교정 가능성·먼지 반복성 및 "
         "회복·오프가스 교차감응 자료 요구가 이 품목에 걸린다. "
         f"외형 {d['sen55_dims'][0]:g} × {d['sen55_dims'][1]:g} × {d['sen55_dims'][2]:g} mm, "
         f"{d['sen55_weight']:g} g. 구매 완료",
         FIXED, "사용자 확인 2026-09-07; wiki/topics/모의장치.md"),
        ("센싱", "SEN55 천장 브래킷", 3, "식",
         f"천장면 z={d['inner'][2]:g}, 내부 평면 중심 기준 외접원 R{d['circumradius']:g} mm "
         f"정삼각형(한 변 약 {d['triangle_side']:.0f} mm), 꼭짓점 하나는 후방. "
         "천장면에서 띄우는 거리와 브래킷 형상은 미정",
         DEPENDENT, f"{PARAMS} sensor_layout·sensor_points"),

        ("수집", "ESP32-S3-WROOM-1 N16R8", 1, "ea",
         "I2C 1버스를 PCA9548A에 물리는 브리지. USB Serial/JTAG(CDC-ACM)로 PC 중계",
         FIXED, "사용자 확인 2026-09-07; wiki/topics/ESP32-S3-WROOM-1.md"),
        ("수집", "PCA9548A", 1, "ea",
         "8채널 I2C 멀티플렉서. A0=A1=A2=GND 로 주소 0x70 고정, RESET 은 VCC 풀업. "
         "채널 0~2에 SEN55 3대(주소 0x69 고정)를 분리 수용",
         FIXED, "사용자 확인 2026-09-07; wiki/topics/PCA9548A.md"),
        ("수집", "P82B715", 6, "ea",
         "I2C 버스 익스텐더. 채널당 케이블 양 끝 1쌍(3채널 = 6개), VCC 5 V. "
         "배선 10 cm 권고 초과 대책의 후보이며 채택 미확정",
         UNKNOWN, "사용자 확인 2026-09-07; wiki/topics/P82B715.md"),
        ("수집", "SEN55 커넥터 하네스", 3, "식",
         f"{d['sen55_conn']} 대응 6핀", FIXED,
         "sen55_params.json module.connector"),
        ("수집", "I2C 차폐 케이블", 3, "식",
         "PCA9548A~SEN55 구간. 챔버 벽을 가로지르므로 데이터시트 10 cm 권고를 넘긴다. "
         "길이·차폐 방식 미정이며 P82B715 채택 여부와 함께 결정",
         UNKNOWN, "wiki/topics/모의장치.md Contradictions"),
        ("수집", "USB 케이블", 1, "ea",
         "전원·통신 통합. SEN55 3대의 5 V를 VBUS에서 분기", FIXED,
         "사용자 확인 2026-09-07; wiki/topics/모의장치.md"),

        ("전장", "전장함", 1, "ea",
         f"챔버 상판 중앙 외부. 확보 공간 {ew:g} × {ed:g} × {eh:g} mm. "
         "실제 함체 미선정, 상판 부착 방식·배선 경로 미정",
         DEPENDENT, f"{PARAMS} electrical_envelope"),
        ("전장", "전원공급기(SMPS)", 1, "ea",
         "계측·제어 전원. 자극 장비 전원과 분리. 정격은 부하표·위험성 평가로 산정하며 "
         "링크는 5 V 10 A 50 W 참고 형번",
         DEPENDENT, "설계서 9.3·13"),
        ("전장", "차단기·접지바", 1, "식",
         "차단기 정격·누전보호는 부하표 확정 후 선정. 링크는 2P 15 A 참고 형번",
         DEPENDENT, "설계서 9.3·13"),
        ("전장", "센서·전력 케이블·실드", 1, "식",
         "전력/신호 분리, 60 ℃·습기·DEC 환경 적합", DEPENDENT, DOC),
        ("전장", "접지 본딩 점퍼(도어용)", 1, "식",
         "외함·도어·판넬·케이블 실드를 지정 접지점에 본딩. 도어는 유연 점퍼",
         DEPENDENT, "설계서 9.3"),
    ]
    keys = [
        "made", "made", "made", "made", "door_sw", "made", "gasket", "made",
        "made", "gland", "made", "none",           # 챔버 12
        "sen55", "made",                            # 센싱 2
        "esp32", "pca9548a", "none", "harness", "none", "usb",   # 수집 6
        "encl", "smps", "mccb", "none", "none",     # 전장 5
    ]
    assert len(keys) == len(R), f"구매처 키 {len(keys)}개 != 행 {len(R)}개"
    out = []
    for i, (row, k) in enumerate(zip(R, keys), start=1):
        out.append((i, *row, *VENDORS[k]))
    return out


# ── 시트 조립 ───────────────────────────────────────────────────────────

def build_sheets(d):
    bom = [("번호", "계층", "품목", "수량", "단위", "요구 사양", "상태", "근거",
            "구매처", "링크", f"참고가 ({CHECKED} 확인)")]
    bom += bom_rows(d)

    cut = [("부재", "매수", "폭 (mm)", "길이 (mm)",
            "매당 면적 (m²)", "합계 면적 (m²)", "상태", "비고")]
    total = 0.0
    for name, qty, w, h, status, note in panels(d):
        each = w * h / 1e6
        sub = each * qty
        total += sub
        cut.append((name, qty, w, h, round(each, 4), round(sub, 4), status, note))
    cut.append(("합계", "", "", "", "", round(total, 4), "",
                f"{d['material']} {d['t']:g}t 총 소요 면적(개구 공제 전). "
                "바닥·천장이 측벽 상하를 덮고 정면·후면판이 측벽 사이에 끼는 "
                "맞대기 구성 가정. 접합 방식·용접 여유는 미정"))

    iw, id_, ih = d["inner"]
    ow, od, oh = d["outer"]
    c = d["clearance"]
    free = (iw * id_ * ih - d["pack"][0] * d["pack"][1] * d["pack"][2]) / 1e9
    basis = [("항목", "값", "단위", "상태", "근거")]
    basis += [
        ("문서 번호", f"{DRAWING_NO} REV {REV}", "-", FIXED,
         "품번과 가격은 전 품목 미정"),
        ("기준 도면", f"J3-CH-001 REV {d['revision']} / J3-SN-001 REV {d['sen55_rev']}",
         "-", FIXED, "chamber_params.json·sen55_params.json"),
        ("팩 치수 (W×D×H)", f"{d['pack'][0]:g} × {d['pack'][1]:g} × {d['pack'][2]:g}",
         "mm", FIXED, "2026-09-01 사람 결정; 설계서 5.1"),
        ("여유 — 좌/우", f"{c['side_left']:g} / {c['side_right']:g}", "mm", FIXED,
         "기류 회전 공간; 2026-09-02 사람 결정"),
        ("여유 — 전/후", f"{c['front']:g} / {c['rear']:g}", "mm", FIXED,
         "전후 기류 공간; 2026-09-02 사람 결정"),
        ("여유 — 상", f"{c['top']:g}", "mm", FIXED,
         "상부 감지기 설치 공간; 2026-09-02 사람 결정"),
        ("여유 — 하", f"{c['bottom']:g}", "mm", FIXED,
         "받침 프레임 높이; 2026-09-02 사람 결정"),
        ("내부 유효 치수", f"{iw:g} × {id_:g} × {ih:g}", "mm", FIXED,
         "팩 + 여유 합"),
        ("판 두께", f"{d['t']:g}", "mm", FIXED, "2026-09-02 사람 결정"),
        ("외형 치수", f"{ow:g} × {od:g} × {oh:g}", "mm", FIXED,
         "내부 유효 + 양면 판 두께"),
        ("재질", d["material"], "-", FIXED, "DEC 내약품성·열풍 내열성; 2026-09-02 사람 결정"),
        ("밀폐 등급", d["sealing"], "-", FIXED, "2026-09-02 사람 결정"),
        ("내부 자유 체적", round(free, 6), "m³", FIXED,
         "내부 체적 − 팩 체적. 지그·장비 체적은 미반영"),
        ("도어 개구", f"{d['door'][0]:g} × {d['door'][1]:g}", "mm", FIXED,
         "팩 폭 + 반입 지그 여유"),
        ("관찰창", f"{d['window'][0]:g} × {d['window'][1]:g}", "mm", FIXED, "설계서 6.2"),
        ("전장 공간 (챔버 상판 외부 중앙)",
         f"{d['elec'][0]:g} × {d['elec'][1]:g} × {d['elec'][2]:g}", "mm", FIXED,
         "사용자 승인 2026-09-07"),
        ("SEN55 배치 외접원", f"R{d['circumradius']:g}", "mm", FIXED,
         "천장면 정삼각형, 꼭짓점 후방; 사용자 지시 2026-09-07"),
        ("SEN55 삼각형 한 변", round(d["triangle_side"], 1), "mm", FIXED,
         "외접원 R × √3"),
        ("SEN55 모듈 외형",
         f"{d['sen55_dims'][0]:g} × {d['sen55_dims'][1]:g} × {d['sen55_dims'][2]:g}",
         "mm", FIXED, "sen55_params.json; 브래킷 설계 입력"),
        ("포트 구경 3종", "미정", "mm", DEPENDENT,
         "장비 토출구·요구 유량·압력손실·누설 시험 결과 및 선정 케이블 외경"),
    ]

    return [
        ("BOM", bom, [6, 8, 34, 10, 6, 66, 11, 30, 14, 46, 32]),
        ("판재 절단표", cut, [22, 7, 11, 12, 15, 15, 11, 60]),
        ("치수 근거", basis, [28, 24, 7, 11, 46]),
    ]


# ── 회귀 검사 ───────────────────────────────────────────────────────────

def check(d, sheets):
    pw, pd_, ph = d["pack"]
    c, t = d["clearance"], d["t"]
    iw, id_, ih = d["inner"]
    ow, od, oh = d["outer"]

    assert (iw, id_, ih) == (pw + c["side_left"] + c["side_right"],
                             pd_ + c["front"] + c["rear"],
                             ph + c["top"] + c["bottom"]), "내부 치수 = 팩 + 여유"
    assert (ow, od, oh) == (iw + 2 * t, id_ + 2 * t, ih + 2 * t), "외형 = 내부 + 2t"
    dw, dh = d["door"]
    assert dw <= iw and dh <= ih, "도어 개구가 정면 내부 면을 벗어난다"
    assert d["window"][0] <= dw and d["window"][1] <= dh, "관찰창이 도어 개구를 벗어난다"
    assert abs(d["triangle_side"] - d["circumradius"] * math.sqrt(3)) < 1e-9
    assert d["circumradius"] * math.sqrt(3) / 2 < iw / 2, "정삼각형이 좌우 벽을 넘는다"

    ps = panels(d)
    area = sum(q * w * h for _, q, w, h, _, _ in ps) / 1e6
    assert area > 0, "판재 면적이 0"
    # 절단표 합계 셀이 실제 합과 일치
    total_cell = sheets[1][1][-1][5]
    assert abs(total_cell - area) < 1e-3, f"합계 면적 불일치: {total_cell} != {area}"

    # 시트마다 모든 행의 열 수가 머리글과 같아야 한다
    for name, rows, widths in sheets:
        n = len(rows[0])
        assert n == len(widths), f"{name}: 머리글 {n}열 != 폭 {len(widths)}개"
        for r in rows:
            assert len(r) == n, f"{name}: 열 수 불일치 {r[:2]}"

    # 상태 어휘와 구매 링크 정합성
    linked = 0
    for row in sheets[0][1][1:]:
        assert row[6] in (FIXED, DEPENDENT, UNKNOWN), f"알 수 없는 상태: {row[6]}"
        vendor, url, price = row[8], row[9], row[10]
        if url:
            linked += 1
            assert url.startswith("https://"), f"{row[2]}: 링크가 https 가 아니다"
            assert vendor and price, f"{row[2]}: 링크가 있는데 구매처 또는 참고가가 비었다"
        else:
            assert not price, f"{row[2]}: 링크 없이 참고가만 있다"
    assert linked, "구매 링크가 하나도 없다"

    print(f"검사 통과 — BOM {len(sheets[0][1]) - 1}행(구매 링크 {linked}), "
          f"판재 {len(ps)}종 합계 {area:.4f} m²")


def main():
    chamber = json.loads((HERE / "chamber_params.json").read_text(encoding="utf-8"))
    sen55 = json.loads((HERE / "sen55_params.json").read_text(encoding="utf-8"))
    d = derive(chamber, sen55)
    sheets = build_sheets(d)
    check(d, sheets)
    out = HERE / "bom.xlsx"
    write_xlsx(out, sheets)
    print(f"생성: {out}")


if __name__ == "__main__":
    main()
