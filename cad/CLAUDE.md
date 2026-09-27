# cad — 부품 형상 규약

이 문서는 `cad/`의 파일 배치와 좌표계, 그리고 text-to-cad 플러그인(`text-to-cad@earthtojake`)의 스킬을 쓸 때 명령을 어떻게 실행하는지를 정한다. 장치가 무엇이고 왜 그렇게 구성되는지는 `wiki/topics/모의장치.md`가, 치수의 근거 규칙과 위키와의 경계는 루트 `CLAUDE.md`가 정한다.

## 파일 배치

```
cad/
  CLAUDE.md        이 문서
  parts.md         모의장치 구성 부품과 그 CAD 파일 목록
  chamber.md       치수 근거 대장
  cadgen           cadgen 실행 스크립트
  src/             모델 소스. 부품 하나에 .py 하나. 가공 도면·치수 도면 스크립트도 여기 둔다
  step/            src/가 생성한 STEP
    imported/      벤더에게서 받은 STEP. 원본 파일명 그대로
  dxf/             src/의 도면 스크립트가 생성한 가공용 DXF
  pdf/             src/의 도면 스크립트가 생성한 치수 도면 PDF
  tmp/             스냅샷과 실험 스크립트. git이 무시한다
```

- 부품 하나는 `src/<이름>.py` 하나이고, 출력은 `@step(out="../step/<이름>.step")`처럼 같은 이름을 쓴다. 이름은 Python 식별자로 쓸 수 있는 영문 소문자와 밑줄만 쓴다.
- 폴더 이름은 소문자로 통일한다. 스킬 예시의 `STEP/` · `STL/` · `DXF/` · `PDF/`는 여기서 `step/` · `stl/` · `dxf/` · `pdf/`이다. 이 밖의 폴더는 만들기 전에 사용자에게 묻는다.
- 생성된 STEP·DXF·PDF도 커밋한다. SolidWorks나 cadgen이 없는 사람도 받아 보고 가공업체에 보낼 수 있어야 한다. 소스를 고치면 다시 빌드한 STEP을 같은 커밋에 담고, 그 부품을 부르는 도면도 다시 빌드해 함께 담는다.
- STEP·DXF·PDF는 `.gitattributes`에서 `-text`로 둔다. 체크아웃이 줄바꿈을 CRLF로 바꾸면 cadgen이 출력과 입력이 바뀐 것으로 보고 다시 빌드하며, 벤더 STEP의 sha256도 원본과 어긋난다.
- 여러 부품이 공유하는 치수는 `src/params.py` 한 곳에 상수로 둔다. 부품 소스마다 따로 박아 넣지 않는다. 값마다의 상태와 근거는 `chamber.md`가 담고, 근거 없는 값은 상수로 만들지 않는다.
- 부품 색은 `src/style.py` 한 곳에 재질별 hex 상수로 두고, 상수마다 근거를 주석으로 단다. 각 부품 소스가 leaf 개체마다 `srgb()`로 입힌다. 색은 STEP에 실려 SolidWorks에서 보인다. `materials=` 사이드카는 SolidWorks가 읽지 않으므로 쓰지 않는다.
- 조립이 필요해지면 하위 부품 모델을 호출하는 `src/assembly.py`를 둔다. 루트 조립품을 실행하면 전체가 빌드된다. 도어를 연 조립품 `src/assembly_door_open.py`는 `assembly.py`를 불러 쓰므로 조립품을 다시 빌드할 때 함께 실행한다.

## 좌표계와 단위

- 단위는 mm, 각도는 도(°)다.
- 원점은 챔버 **내부 바닥의 도어측 좌측 모서리**이며 Z-up이다. `x`는 폭, `y`는 깊이, `z`는 높이다.
- 모든 부품은 이 좌표계에서 조립 위치에 놓인 채로 모델링하거나, 자기 원점을 쓰고 조립품에서 옮긴다. 어느 쪽인지는 소스 맨 위 주석에 적는다.

## 가공 도면 (DXF)

판재를 잘라 만드는 부품(외함 패널, 도어, 도어 밀폐재, 기판 외곽)은 text-to-cad의 `dxf` 스킬로 가공용 2D 도면을 낸다.

- 도면 스크립트는 그 부품 모델 옆에 `src/<부품>_dxf.py`로 두고, 출력은 `@dxf(out="../dxf/<도면>.dxf")`다. 부품 모델을 import해 호출하고, 돌려받은 형상에서 면을 골라 `cadgen.flatten`으로 펼친다. 생성된 `step/*.step`을 `read_step`으로 읽지 않는다.
- 한 부품에서 여러 장이 나오면 한 스크립트에 `@dxf` 함수를 여러 개 둔다(외함 패널 6장). 같은 형상이 여러 개면 도면은 하나다(P82B715 기판 3장).
- 도면은 모델에 있는 형상만 옮기고 새 치수를 만들지 않는다. 모델에 없는 구멍은 도면에도 없다. 철물 장착 구멍은 철물이 대표 형상인 동안 모델에도 도면에도 내지 않고, 구매품이 정해지면 모델에 먼저 더한다.
- 챔버 바깥에서 본 면을 그린다. 패널은 바깥면이 보이는 면이다. 기판은 소자를 싣는 면이고, 소자를 그리지 않는 P82B715 기판은 브래킷에서 먼 면이다. 펼친 면은 돌리기만 하고 뒤집지 않는다.
- 세로 판(앞·뒤·옆 패널, 도어, 밀폐재)은 챔버의 +z가, 천장·바닥 패널은 챔버의 +y(뒤쪽)가 도면의 위쪽이다. 기판은 긴 변을 도면의 x축에 둔다.
- 도면 좌표의 원점은 판 외곽의 왼쪽 아래 모서리이고, 판 전체가 +x·+y 쪽에 놓인다. 펼친 결과를 옮겨서 맞춘다.
- 레이어는 `CUT` 하나다. 각인과 참고선은 넣지 않는다. kerf는 0으로 두고, 절단 폭은 가공업체가 보정한다.

## 치수 도면 (PDF)

가공 도면을 낸 판재 부품은 text-to-cad의 `engineering-drawing` 스킬로 사람이 읽는 치수 도면을 함께 낸다. DXF는 자를 선이고 PDF는 그 선의 치수를 확인하는 문서다.

- 도면 스크립트는 그 부품 모델 옆에 `src/<부품>_drawing.py`로 두고, 출력은 `@eng_drawing(out="../pdf/<부품>.pdf")`다. 부품 모델을 import해 호출하고 돌려받은 형상을 그린다. 한 부품에서 여러 장이 나오면 한 PDF의 여러 쪽이다(외함 패널 6쪽).
- 주 뷰는 그 판의 DXF와 같은 면, 같은 방향이다. cadgen의 뷰 이름(`front` · `back` · `left` · `right` · `top`)은 그대로 DXF 방향과 같지만 `bottom`은 위쪽이 챔버의 −y라 180° 다르므로, 바닥 패널은 형상을 자기 외곽 가운데를 지나는 z축으로 180° 돌려 그린다.
- 위치 치수는 DXF 원점과 같은 판의 왼쪽 아래 모서리에서 잰다. 같은 간격의 구멍 줄은 첫·끝 구멍 사이를 한 번 재고 `(n× EQ SP)`를 붙인다. 구멍은 `view.hole`로 `n× ⌀d THRU`처럼 표기한다. 치수 값은 형상에서 재고 직접 쓰지 않으며, 점과 개수는 모델의 상수와 함수에서 가져온다. 두께는 도곽의 재질 칸이 담고 치수로 재지 않는다.
- 일반 공차는 ISO 2768-m이다. 글자는 영문이다(컨테이너에 한글 글꼴이 없다). 도곽에는 제목, 정해진 재질, 개정 A를 적고 도면 번호와 작성자는 비운다. 도어와 패널에는 `HARDWARE MOUNTING HOLES NOT INCLUDED.` 노트를 넣는다.

## 호스트에서 cadgen을 실행하지 않는다

이 PC는 Windows Smart App Control이 켜져 있어 uv가 받은 Python(`python313.dll`)과 CAD 커널(`OCP`)의 DLL을 차단한다. 그래서 스킬 문서가 안내하는 `uvx --no-config --managed-python --python 3.13 --from cadgen==… cadgen` 명령은 호스트에서 실패한다. 플러그인이 등록하는 MCP 서버 `cad`도 같은 이유로 연결되지 않으며, 고치려 하지 않는다.

모든 cadgen 실행은 도커 컨테이너 안에서 하는 `cad/cadgen` 스크립트로 대신한다.

| 스킬 문서의 표기 | 대신 실행할 것 |
|---|---|
| `cadgen <args>` | `cad/cadgen <args>` |
| `python <model>.py` | `cad/cadgen python <model>.py` |
| `python -c "…"` | `cad/cadgen python -c "…"` |

경로는 실행하는 위치에 맞게 상대경로로 바꾼다. 예를 들어 `cad/` 안에서는 `./cadgen step snapshot …`이다.

## 스크립트가 하는 일

- 명령마다 `docker run --rm`으로 임시 컨테이너를 띄우고, 끝나면 지운다. 상시 실행 중인 `airo-tips` 컨테이너는 쓰지 않는다.
- 현재 git 워크트리의 루트를 컨테이너의 `/work`에 붙이고, 현재 디렉터리를 그대로 유지한다. 어느 워크트리에서 실행해도 그 워크트리가 붙는다.
- 패키지·브라우저·Python과 matplotlib 글꼴 캐시(`MPLCONFIGDIR`)는 도커 볼륨 `cadgen-cache`에 남는다. 첫 실행만 다운로드로 수십 초가 걸리고, 이후는 몇 초다.
- cadgen 버전은 설치된 플러그인의 `claude.mcp.json`에 고정된 `cadgen==` 값을 따른다. 플러그인을 업데이트하면 따라 바뀐다.

## 경로 규칙

- 파일은 반드시 현재 워크트리 안에 있어야 한다. 워크트리 밖의 경로와 호스트 절대경로(`C:\…`)는 컨테이너에서 보이지 않는다. 상대경로를 쓴다.
- cadgen이 출력하는 `/work/…` 경로는 워크트리 루트 기준 경로다. 예: `/work/cad/step/chamber.step` → `cad/step/chamber.step`.

## 결과 확인

- 형상 확인은 `cad/cadgen step snapshot step/<이름>.step tmp/<이름>.png`처럼 PNG를 `tmp/`에 렌더링해 읽는다. 스킬이 요구하는 시각 검토도 이 방법으로 한다.
- 도면은 `cad/cadgen dxf snapshot dxf/<도면>.dxf tmp/<도면>.png`로 렌더링해 읽고, `cadgen.drawing_checks.validate_dxf_file`과 `ezdxf`로 레이어·개체 수·외곽·구멍을 잰다. 도면이 부품보다 오래됐는지는 `cad/cadgen store why src/<부품>_dxf.py`가 알려 준다.
- 치수 도면은 `cad/cadgen python src/<부품>_drawing.py`가 출력하는 알림(`measures blank paper`, `annotation overlaps`)을 먼저 읽고, PDF를 직접 읽어 겹침과 빠진 표기를 본다. 같은 내용이면 PDF가 같은 바이트로 다시 나오므로, 스크립트를 `tmp/`에 복사해 출력 경로만 바꿔 그린 PDF의 sha256이 커밋된 PDF와 같으면 그 PDF가 지금 모델과 맞다.
- CAD Viewer(`cadgen viewer`, `cad_show`)는 쓰지 않는다. 임시 컨테이너 안의 서버는 명령이 끝나면 사라진다.

## 이미지

- 이미지는 저장소 루트의 `Dockerfile`로 만든 `trixie-slim:uv-nvm`이다. cadgen에 필요한 Node.js와 Chromium 시스템 라이브러리가 들어 있다.
- `Dockerfile`이 바뀌면 `docker compose build`로 다시 만든다.
- 다른 이미지나 버전을 써야 할 때는 환경변수 `CADGEN_IMAGE`와 `CADGEN_VERSION`으로 바꾼다.
- 컨테이너에 `DISPLAY`를 넘기지 않는다. 넘기면 Chromium이 X11에 붙으려다 WebGL 생성에 실패해 스냅샷이 깨진다.
