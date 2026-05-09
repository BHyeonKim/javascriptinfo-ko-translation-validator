---
name: translation-validator
description: >
  ko.javascript.info 한국어 번역 검증기. javascript.info 한국어 번역 작업물이
  프로젝트 번역 모범 사례를 준수하는지 검토할 때 사용. 다음 요청 시 트리거:
  "번역 검토해줘", "번역 확인해줘", "번역 검증해줘", "번역 피드백", "번역 규칙
  맞는지 봐줘", "translation validate", PR 리뷰 시 .md 번역 파일 포함된 경우.
  세 가지 규칙 소스를 병렬 에이전트로 동시 검토: (1) ko.javascript.info 위키
  번역 모범 사례, (2) KIGO 번역 스타일 가이드, (3) 프로젝트 커스텀 규칙.
---

# ko.javascript.info 번역 검증

## 검증 절차

### 1단계 — 파일 준비 및 스크립트 경로 확인

검토할 번역 파일을 읽고, 다음 명령으로 맞춤법 검사 스크립트의 절대 경로를 확인한다:

```bash
find "$HOME/.claude" "$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude" \
  -name "check_spelling.py" -path "*/translation-validator/*" 2>/dev/null | head -1
```

결과를 `SPELL_SCRIPT`로 기억한다. 경로를 찾지 못하면 에이전트 4를 건너뛴다.

### 2단계 — 병렬 에이전트 실행

네 검증 작업이 서로 독립적이므로 Agent 도구로 **동시에 4개 에이전트를 하나의 메시지에** 실행한다.
각 에이전트에게 전달할 것:
- 번역 파일 전체 내용 (프롬프트에 직접 포함)
- 담당 규칙 파일 경로 (각자 Read로 읽게 함)
- 아래 출력 형식

**에이전트 1 프롬프트 템플릿:**
```
다음은 ko.javascript.info 번역 파일 내용입니다:

<translation>
[번역 파일 전체 내용]
</translation>

/Users/kimbohyeon/.claude/skills/translation-validator/references/wiki-guidelines.md 를 읽고,
해당 파일에 정의된 WIKI-1~WIKI-17 규칙을 번역 파일에 적용해 위반 사항을 검토하라.

결과를 아래 JSON으로만 반환하라 (다른 텍스트 없음):
{
  "source": "wiki",
  "violations": [
    {"line": 줄번호, "rule_id": "WIKI-N", "problem": "위반 내용", "suggestion": "수정 제안", "severity": "required|recommended|info"}
  ],
  "passed": ["통과한 규칙 항목 간략 설명", ...]
}

주의: 코드 블록(```), 인라인 코드(``) 내부는 검사 제외.
```

**에이전트 2** — 동일하되 `kigo-guidelines.md`, 규칙 ID는 `KIGO-*`

**에이전트 3** — 동일하되 `custom-rules.md`, 규칙 ID는 `CUSTOM-*`

**에이전트 4 프롬프트 템플릿:**
```
다음 명령을 실행하고 결과를 그대로 반환하라:

  python3 "<SPELL_SCRIPT 경로>" "<파일 절대경로>"

명령 실행 후 JSON 출력을 파싱하여 아래 형식으로만 반환하라 (다른 텍스트 없음):
{
  "source": "spell",
  "violations": [
    {"rule_id": "SPELL", "problem": "원문 텍스트", "suggestion": "수정 제안", "explanation": "설명", "severity": "required"}
  ],
  "passed": ["맞춤법 오류 없음"] // violations가 비어 있을 때만
}
```

### 3단계 — 결과 병합 및 보고서 출력

네 에이전트 결과를 합쳐 아래 형식으로 출력한다.

### 4단계 — JSON 결과 저장 및 경로 출력

보고서 출력 직후, 병합된 결과를 JSON 파일로 저장하고 경로를 표시한다.

**저장 경로**: 검증 대상 파일과 같은 디렉터리에 `<원본파일명>_validation.json` 으로 저장.
- 예) `/path/to/article.md` → `/path/to/article_validation.json`

**저장 형식**:
```json
{
  "meta": {
    "validated_file": "<검증 대상 파일 절대경로>",
    "validated_at": "<ISO 8601 타임스탬프>",
    "summary": {
      "total": N,
      "required": N,
      "recommended": N,
      "info": N
    }
  },
  "violations": [
    {
      "line": 줄번호,
      "rule_id": "WIKI-N",
      "source": "wiki",
      "problem": "위반 내용",
      "suggestion": "수정 제안",
      "severity": "required"
    }
  ],
  "passed": {
    "wiki": ["통과 항목 1", "..."],
    "kigo": ["통과 항목 1", "..."],
    "custom": ["통과 항목 1", "..."],
    "spell": ["통과 항목 1", "..."]
  }
}
```

타임스탬프는 Bash로 생성: `date -u +"%Y-%m-%dT%H:%M:%SZ"`

Write 도구로 JSON 파일을 저장한 뒤, 다음 형식으로 경로를 출력한다:

```
📄 검증 결과 저장됨: /path/to/article_validation.json
```

## 보고서 형식

```markdown
## 번역 검토 결과: `파일경로`

### 위반 사항 (N개)

| 줄 | 규칙 ID | 심각도 | 위반 내용 | 수정 제안 |
|---|---|---|---|---|
| 23 | WIKI-1 | 🔴 필수 | "다음 예제를 보세요:" → 문장 끝 콜론 | "다음 예제를 보세요." |
| 45 | KIGO-시제 | 🟡 권고 | "찾을 수 있을 것입니다" | "찾을 수 있습니다" |
| 67 | CUSTOM-병기 | 🔴 필수 | `property` 첫 등장, 한-영 병기 누락 | "프로퍼티(property)" |
| - | SPELL | 🔴 필수 | "테스트 입니다." | "테스트입니다." |

### 통과 항목
- WIKI: 제목 문장부호 이상 없음, 경어 일관됨, ...
- KIGO: 외래어 표기 이상 없음, ...
- CUSTOM: 옮긴이 주 형식 올바름
- SPELL: 추가 맞춤법 오류 없음

### 총평
(심각도별 통계 및 전체 품질 의견)
```

## 심각도

- **🔴 필수(required)**: 규칙 위반이 명확 — 반드시 수정
- **🟡 권고(recommended)**: 더 자연스러운 표현 존재 — 수정 권장
- **⚪ 참고(info)**: 맥락에 따라 허용 가능 — 의견 제시만

## 주의사항

- 코드 블록(`` ``` ``), 인라인 코드(`` ` ``), 원문 인용 내부는 규칙 적용 제외
- 마크다운 헤딩은 WIKI-15 적용 (마침표/물음표 금지)
- CUSTOM-병기는 **해당 파일 내 첫 등장**에만 적용
