# javascriptinfo-ko-translation-validator

[모던 JavaScript 튜토리얼](https://javascript.info/) 한국어 번역 프로젝트 [ko.javascript.info](https://github.com/javascript-tutorial/ko.javascript.info)의 번역 품질을 검증하는 Claude Code 스킬입니다.

번역 파일(`.md`)을 지정하면 4개의 에이전트가 병렬로 규칙을 검사하고, 마크다운 보고서와 JSON 파일을 생성합니다.

---

## 설치

### 사전 요구사항

- [Claude Code](https://claude.ai/code) CLI 설치
- Python 3 (맞춤법 검사 에이전트에 필요)
- Node.js + [hanspell](https://www.npmjs.com/package/hanspell) (`npm install -g hanspell`)
- macOS / Linux / WSL

### 방법 1 — git clone (권장)

```bash
# 1. 스킬 디렉터리로 이동 (없으면 생성)
mkdir -p ~/.claude/skills
cd ~/.claude/skills

# 2. 저장소 클론
git clone https://github.com/BHyeonKim/javascriptinfo-ko-translation-validator translation-validator
```

### 방법 2 — 수동 복사

저장소를 ZIP으로 다운로드한 뒤 압축을 풀고, 폴더 이름을 `translation-validator`로 변경해 `~/.claude/skills/`에 넣습니다.

```
~/.claude/skills/
└── translation-validator/
    ├── SKILL.md
    ├── references/
    └── scripts/
```

### 설치 확인

Claude Code를 재시작한 뒤 아래 명령으로 스킬 목록에 `translation-validator`가 표시되는지 확인합니다.

```
/skills
```

### 업데이트

```bash
cd ~/.claude/skills/translation-validator
git pull
```

---

## 사용법

```
/translation-validator <번역 파일 경로>
```

**예시**

```
/translation-validator 1-js/02-first-steps/03-strict-mode/article.md
```

---

## 에이전트 구성

4개의 에이전트가 동시에 실행됩니다.

### Agent 1 — WIKI 규칙 검사

출처: [ko.javascript.info 위키 번역 모범 사례](https://github.com/javascript-tutorial/ko.javascript.info/wiki/번역-모범-사례)

| 규칙 ID | 내용 |
|---------|------|
| WIKI-1 | 문장 끝 쌍점(콜론) 사용 금지 |
| WIKI-2 | 과도한 `-시-` 존칭 사용 제한 |
| WIKI-3 | 영어 쉼표의 기계적 직역 금지 |
| WIKI-4 | 외래어 동사 → `명사형 + 하다` 형태로 번역 |
| WIKI-5 | 불필요한 인칭대명사 생략 |
| WIKI-6 | 피동형 최소화, 능동형으로 전환 |
| WIKI-7 | 동일 단어 반복 사용 지양 |
| WIKI-8 | 복수형 `-들` 최소화 |
| WIKI-9 | 조건 어미 앞 불필요한 `만약` 생략 |
| WIKI-10 | 괄호 삽입 문장 형식 (구 vs 완전한 문장) |
| WIKI-11 | IT 약어 표기 순서 (`약어(한글 번역)`) |
| WIKI-12 | 함수 이름 뒤 `함수` 명칭 붙이기 |
| WIKI-13 | 강조 표현에 작은따옴표(`'`) 사용 |
| WIKI-14 | 모호한 대명사 구체적 명사로 풀어쓰기 |
| WIKI-15 | 헤딩에 마침표·물음표 금지 |
| WIKI-16 | 짝 단어에 슬래시(`/`) 대신 가운뎃점(`·`) 사용 |
| WIKI-17 | 명사형 문장 끝 마침표 생략 |

### Agent 2 — KIGO 규칙 검사

출처: KIGO 표준 스타일 가이드 v2017 (한국 IT 산업세계화학회) 발췌

| 규칙 ID | 내용 |
|---------|------|
| KIGO-시제 | 미래 시제(`~할 것입니다`) → 현재형으로 대체 |
| KIGO-콜론 | 세미콜론 → 쉼표 또는 마침표로 대체 |
| KIGO-괄호 | 괄호 삽입 형식 (구·문장 구분) |
| KIGO-조사 | 괄호 앞 단어 기준으로 조사 결정 |
| KIGO-약어 | 약어 대문자 표기, 복수 `s` 금지 |
| KIGO-외래어 | IT 외래어 표기 규칙 준수 |
| KIGO-경어 | 경어체 일관 사용, 맨 끝 동사에만 높임말 |
| KIGO-주체생략 | 분명한 주체 생략 |
| KIGO-조사남용 | 격조사 `~의` 연속 사용 금지 |
| KIGO-수동형 | 수동형 → 능동형 전환 |
| KIGO-복수형 | 복수형 → 단수형으로 표현 |
| KIGO-맞춤법 | 자주 틀리는 단어 교정 |
| KIGO-제목 | 헤딩은 간결한 명사형 사용 |
| KIGO-제품명 | 회사·제품·소프트웨어 이름 번역 금지 |

### Agent 3 — CUSTOM 규칙 검사

ko.javascript.info 프로젝트 자체 규칙

| 규칙 ID | 내용 |
|---------|------|
| CUSTOM-병기 | 새 키워드 첫 등장 시 한-영 병기 (`한국어(영어)`) |
| CUSTOM-옮긴이 | 번역자 부가설명은 `(설명 - 옮긴이)` 형식으로만 삽입 |
| CUSTOM-금지표현 | `-적인`, `-적으로` 형 한자 조어 지양 |

### Agent 4 — 맞춤법 검사

[hanspell](https://www.npmjs.com/package/hanspell) 라이브러리를 사용하는 Python 스크립트(`scripts/check_spelling.py`)로 맞춤법을 검사합니다.

- 띄어쓰기 오류
- 맞춤법 오류
- 표준어 교정

> **사전 요구사항**: `hanspell` npm 패키지가 설치되어 있어야 합니다.
> ```bash
> npm install -g hanspell
> ```

> 코드 블록(` ``` `), 인라인 코드(`` ` ``) 내부는 모든 에이전트 검사에서 제외됩니다.

---

## 결과 예시

### 마크다운 보고서

```markdown
## 번역 검토 결과: `1-js/02-first-steps/03-strict-mode/article.md`

### 위반 사항 (19개)

| 줄  | 규칙 ID       | 심각도   | 위반 내용                              | 수정 제안               |
|-----|--------------|---------|---------------------------------------|------------------------|
| 3   | SPELL        | 🔴 필수  | `발전해왔습니다` — 보조 용언 붙여쓰기      | `발전해 왔습니다`        |
| 7   | KIGO-시제     | 🔴 필수  | `생길 수 있겠죠?` — 미래 추측 시제       | `생길 수 있습니다.`      |
| 22  | KIGO-경어     | 🟡 권고  | `알아두시기 바랍니다` — 이중 높임 표현    | `알아두기 바랍니다`      |
| 49  | WIKI-2       | 🟡 권고  | `주의하셔야 합니다` — 과도한 `-시-`      | `주의해야 합니다`        |
| 81  | CUSTOM-병기   | 🟡 권고  | `클래스`와 `모듈` 첫 등장 시 병기 누락   | `클래스(class)`, `모듈(module)` |

### 통과 항목
- WIKI: 헤딩 콜론 없음, 인칭대명사 삽입 없음, ...
- KIGO: 외래어 표기 준수, 제품명 번역 않음, ...
- CUSTOM: `엄격 모드(strict mode)` 첫 등장 병기 적용, ...
- SPELL: 그 외 맞춤법 오류 없음

### 총평
🔴 필수 9건 · 🟡 권고 10건. KIGO-시제 위반(5건)이 가장 빈번 —
`~하겠습니다`를 현재형으로 일괄 교체하면 해소됩니다.
```

### JSON 결과 파일

검증 대상 파일과 같은 디렉터리에 `<파일명>_validation.json`으로 저장됩니다.

```
article.md → article_validation.json
```

```json
{
  "meta": {
    "validated_file": "/path/to/article.md",
    "validated_at": "2026-05-09T10:22:55Z",
    "summary": {
      "total": 19,
      "required": 9,
      "recommended": 10,
      "info": 0
    }
  },
  "violations": [
    {
      "line": 3,
      "rule_id": "SPELL",
      "source": "spell",
      "problem": "발전해왔습니다 — 보조 용언 붙여쓰기",
      "suggestion": "발전해 왔습니다",
      "severity": "required"
    }
  ],
  "passed": {
    "wiki": ["WIKI-1: 헤딩 콜론 사용 없음", "..."],
    "kigo": ["KIGO-약어: 대문자 표기 준수", "..."],
    "custom": ["엄격 모드(strict mode) 첫 등장 시 병기 적용", "..."],
    "spell": ["그 외 맞춤법 오류 없음"]
  }
}
```

---

## 자동 수정

검증이 끝나고 JSON 파일이 생성되면 다음 선택지가 표시됩니다:

```
검증 결과를 바탕으로 번역 파일을 자동 수정할까요?

  A. 🔴 필수 항목만 수정   — 맞춤법·명백한 규칙 위반만 적용
  B. 🔴 필수 + 🟡 권고 수정 — 스타일 개선까지 포함
  C. 건너뛰기              — 파일 변경 없이 종료
```

수정 후 결과 요약:

```markdown
### 자동 수정 결과

✅ 적용됨 (6건)
| 줄 | 규칙 ID | 변경 내용 |
|---|---|---|
| 3  | SPELL    | `발전해왔습니다` → `발전해 왔습니다` |
| 7  | SPELL    | `활성화 했을` → `활성화했을` |
| 65 | SPELL    | `오래 되어서` → `오래되어서` |

⚠️ 수동 수정 필요 (3건)
| 줄 | 규칙 ID  | 제안 내용 |
|---|---|---|
| 22 | KIGO-시제 | `학습하도록 하겠습니다` → `학습합니다` |
| 83 | KIGO-시제 | `모시도록 하겠습니다` → `모십니다` |
```

> 코드 블록(` ``` `) 내부는 자동 수정에서 제외됩니다.
> 문장 전체 재작성이 필요한 항목은 제안만 표시하고 직접 수정을 안내합니다.

---

## 심각도 기준

| 심각도 | 의미 |
|--------|------|
| 🔴 필수 | 규칙 위반이 명확 — 반드시 수정 |
| 🟡 권고 | 더 자연스러운 표현 존재 — 수정 권장 |
| ⚪ 참고 | 맥락에 따라 허용 가능 — 의견 제시만 |

---

## 파일 구조

```
.
├── SKILL.md                      # Claude Code 스킬 정의
├── references/
│   ├── wiki-guidelines.md        # WIKI-1~17 규칙
│   ├── kigo-guidelines.md        # KIGO 스타일 가이드
│   └── custom-rules.md           # 프로젝트 커스텀 규칙
└── scripts/
    └── check_spelling.py         # 맞춤법 검사 스크립트
```

---

## 관련 링크

- [ko.javascript.info 저장소](https://github.com/javascript-tutorial/ko.javascript.info)
- [번역 모범 사례 위키](https://github.com/javascript-tutorial/ko.javascript.info/wiki/번역-모범-사례)
- [모던 JavaScript 튜토리얼](https://javascript.info/)
