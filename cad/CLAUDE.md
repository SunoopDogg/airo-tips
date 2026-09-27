# cad — 부품 형상 규약

이 문서는 `cad/`의 파일 배치와 좌표계, 그리고 text-to-cad 플러그인(`text-to-cad@earthtojake`)의 스킬을 쓸 때 명령을 어떻게 실행하는지를 정한다. 장치가 무엇이고 왜 그렇게 구성되는지는 `wiki/topics/모의장치.md`가, 치수의 근거 규칙과 위키와의 경계는 루트 `CLAUDE.md`가 정한다.

## 파일 배치

```
cad/
  CLAUDE.md        이 문서
  parts.md         모의장치 구성 부품과 그 CAD 파일 목록
  chamber.md       치수 근거 대장
  cadgen           cadgen 실행 스크립트
  src/             모델 소스. 부품 하나에 .py 하나
  step/            src/가 생성한 STEP
    imported/      벤더에게서 받은 STEP. 원본 파일명 그대로
  tmp/             스냅샷과 실험 스크립트. git이 무시한다
```

- 부품 하나는 `src/<이름>.py` 하나이고, 출력은 `@step(out="../step/<이름>.step")`처럼 같은 이름을 쓴다. 이름은 Python 식별자로 쓸 수 있는 영문 소문자와 밑줄만 쓴다.
- 폴더 이름은 소문자로 통일한다. 스킬 예시의 `STEP/` · `STL/`은 여기서 `step/` · `stl/`이다. 이 밖의 폴더는 만들기 전에 사용자에게 묻는다.
- 생성된 STEP도 커밋한다. SolidWorks나 cadgen이 없는 사람도 받아 볼 수 있어야 한다. 소스를 고치면 다시 빌드한 STEP을 같은 커밋에 담는다.
- 여러 부품이 공유하는 치수는 `src/params.py` 한 곳에 상수로 둔다. 부품 소스마다 따로 박아 넣지 않는다. 값마다의 상태와 근거는 `chamber.md`가 담고, 근거 없는 값은 상수로 만들지 않는다.
- 부품 색은 `src/style.py` 한 곳에 재질별 hex 상수로 두고, 상수마다 근거를 주석으로 단다. 각 부품 소스가 leaf 개체마다 `srgb()`로 입힌다. 색은 STEP에 실려 SolidWorks에서 보인다. `materials=` 사이드카는 SolidWorks가 읽지 않으므로 쓰지 않는다.
- 조립이 필요해지면 하위 부품 모델을 호출하는 `src/assembly.py`를 둔다. 루트 조립품을 실행하면 전체가 빌드된다. 도어를 연 조립품 `src/assembly_door_open.py`는 `assembly.py`를 불러 쓰므로 조립품을 다시 빌드할 때 함께 실행한다.

## 좌표계와 단위

- 단위는 mm, 각도는 도(°)다.
- 원점은 챔버 **내부 바닥의 도어측 좌측 모서리**이며 Z-up이다. `x`는 폭, `y`는 깊이, `z`는 높이다.
- 모든 부품은 이 좌표계에서 조립 위치에 놓인 채로 모델링하거나, 자기 원점을 쓰고 조립품에서 옮긴다. 어느 쪽인지는 소스 맨 위 주석에 적는다.

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
- 패키지·브라우저·Python은 도커 볼륨 `cadgen-cache`에 남는다. 첫 실행만 다운로드로 수십 초가 걸리고, 이후는 몇 초다.
- cadgen 버전은 설치된 플러그인의 `claude.mcp.json`에 고정된 `cadgen==` 값을 따른다. 플러그인을 업데이트하면 따라 바뀐다.

## 경로 규칙

- 파일은 반드시 현재 워크트리 안에 있어야 한다. 워크트리 밖의 경로와 호스트 절대경로(`C:\…`)는 컨테이너에서 보이지 않는다. 상대경로를 쓴다.
- cadgen이 출력하는 `/work/…` 경로는 워크트리 루트 기준 경로다. 예: `/work/cad/step/chamber.step` → `cad/step/chamber.step`.

## 결과 확인

- 형상 확인은 `cad/cadgen step snapshot step/<이름>.step tmp/<이름>.png`처럼 PNG를 `tmp/`에 렌더링해 읽는다. 스킬이 요구하는 시각 검토도 이 방법으로 한다.
- CAD Viewer(`cadgen viewer`, `cad_show`)는 쓰지 않는다. 임시 컨테이너 안의 서버는 명령이 끝나면 사라진다.

## 이미지

- 이미지는 저장소 루트의 `Dockerfile`로 만든 `trixie-slim:uv-nvm`이다. cadgen에 필요한 Node.js와 Chromium 시스템 라이브러리가 들어 있다.
- `Dockerfile`이 바뀌면 `docker compose build`로 다시 만든다.
- 다른 이미지나 버전을 써야 할 때는 환경변수 `CADGEN_IMAGE`와 `CADGEN_VERSION`으로 바꾼다.
- 컨테이너에 `DISPLAY`를 넘기지 않는다. 넘기면 Chromium이 X11에 붙으려다 WebGL 생성에 실패해 스냅샷이 깨진다.
