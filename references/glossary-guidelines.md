# 용어집 기반 번역 검증 규칙

ko.javascript.info 한국어 번역 팀이 운영하는 공식 용어집(Google Sheets)을 기준으로
표준 번역어 일관성을 검사한다.

- 시트1(일반 기술 용어): https://docs.google.com/spreadsheets/d/1fYaEI8vz26N3R2VaxrlNnk9fMQ8zIy4RpvjRp4jZd0Q/edit?gid=1401860741
- 시트2(기호/구두점 표기): https://docs.google.com/spreadsheets/d/1fYaEI8vz26N3R2VaxrlNnk9fMQ8zIy4RpvjRp4jZd0Q/edit?gid=843106813

두 시트는 `glossary/sheet1.csv`, `glossary/sheet2.csv`로 캐시되며, 매 실행 시 원본 시트를
조회하고 해시가 변경된 경우에만 캐시를 갱신한다. 네트워크 실패 시 기존 캐시로 계속 동작한다.

## GLOSSARY-mismatch 표준 번역어 불일치

본문에 `한국어(영어)` 병기 패턴이 등장할 때, 영어 키가 용어집에 있는데 한국어 부분이
표준 표기와 다르면 권고한다.

예시:
- ❌ `객체(property)` → ✅ `프로퍼티(property)`
- ❌ `다른표기(single-quoted)` → ✅ `작은따옴표(single-quoted)`
- ✅ `세미콜론(;)` (시트2의 슬래시 표기 `세미콜론/쌍반점` 중 하나라 통과)

**적용 범위**: `한국어(영어)` 병기 패턴에 한정. 한국어 단독 등장, 영어 단독 등장은
검사하지 않는다(오탐 방지).

**예외**: 코드 블록(`` ``` ``), 인라인 코드(`` ` ``) 내부는 검사 제외.

**심각도**: 권고(🟡) — 문맥상 표준과 다르게 번역하는 게 옳은 경우도 있어 강제하지 않는다.

**자동 수정 대상 아님**: 5단계 자동 수정에서 GLOSSARY-mismatch는 사용자가 권고
포함을 선택하더라도 적용하지 않고 수동 검토로만 안내한다.

## 동작 메모

- 시트2의 슬래시 분리 표기(예: `세미콜론/쌍반점`)는 두 표기 모두 정답 후보로 인정한다.
- `Browser Object Model, BOM`처럼 콤마 포함 영문은 첫 항(`Browser Object Model`)을
  lookup 키로 사용한다.
- 한국어 부분이 길게 매칭되는 경우(예: `본문에 작은따옴표(single-quoted)`)에도
  표준 후보가 suffix로 들어있으면 통과로 본다.
