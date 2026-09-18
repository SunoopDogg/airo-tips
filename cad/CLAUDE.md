# cad — text-to-cad 실행 규칙

이 문서는 `cad/`에서 text-to-cad 플러그인(`text-to-cad@earthtojake`)의 스킬을 쓸 때 명령을 어떻게 실행하는지를 정한다. 도면 계층이 무엇을 담고 어떤 근거로 치수를 정하는지는 `cad/README.md`와 루트 `CLAUDE.md`가 정하고, 여기서는 다루지 않는다.

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
- cadgen이 출력하는 `/work/…` 경로는 워크트리 루트 기준 경로다. 예: `/work/cad/export/a.png` → `cad/export/a.png`.

## 결과 확인

- 형상 확인은 `cad/cadgen step snapshot <a.step> <a.png>`로 PNG를 렌더링해 읽는다. 스킬이 요구하는 시각 검토도 이 방법으로 한다.
- CAD Viewer(`cadgen viewer`, `cad_show`)는 쓰지 않는다. 임시 컨테이너 안의 서버는 명령이 끝나면 사라진다.

## 파일 위치

모델 소스(`.py`)와 산출물을 어디에 둘지는 `cad/README.md`의 디렉터리 규약을 따른다. 스킬 예시에 나오는 `STEP/` · `STL/` · `src/` 폴더를 새로 만들지 않는다. 규약에 맞는 자리가 없으면 만들기 전에 사용자에게 묻는다.

## 이미지

- 이미지는 저장소 루트의 `Dockerfile`로 만든 `trixie-slim:uv-nvm`이다. cadgen에 필요한 Node.js와 Chromium 시스템 라이브러리가 들어 있다.
- `Dockerfile`이 바뀌면 `docker compose build`로 다시 만든다.
- 다른 이미지나 버전을 써야 할 때는 환경변수 `CADGEN_IMAGE`와 `CADGEN_VERSION`으로 바꾼다.
- 컨테이너에 `DISPLAY`를 넘기지 않는다. 넘기면 Chromium이 X11에 붙으려다 WebGL 생성에 실패해 스냅샷이 깨진다.
