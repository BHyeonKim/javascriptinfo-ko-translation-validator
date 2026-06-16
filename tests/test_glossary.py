"""Tests for scripts/check_glossary.py.

실행:
    python3 -m unittest discover tests -v
또는:
    python3 -m unittest tests.test_glossary -v
"""

import json
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_glossary import (  # noqa: E402
    PAIR_RE,
    check_file,
    load_glossary,
    resolve_korean,
)


def has_network() -> bool:
    try:
        socket.create_connection(("docs.google.com", 443), timeout=3).close()
        return True
    except OSError:
        return False


def write_md(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".md", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class ResolveKoreanTest(unittest.TestCase):
    """resolve_korean(): 본문 한국어와 표준 후보 매칭."""

    def test_exact_single(self):
        self.assertEqual(resolve_korean("작은따옴표", ["작은따옴표"]), ("작은따옴표", True))

    def test_exact_multi_token(self):
        self.assertEqual(resolve_korean("동일 출처", ["동일 출처"]), ("동일 출처", True))

    def test_suffix_match_with_prefix(self):
        # 정규식이 욕심부려 앞 단어까지 잡은 경우, suffix 매칭으로 통과 처리
        self.assertEqual(
            resolve_korean("본문에 작은따옴표", ["작은따옴표"]), ("작은따옴표", True)
        )

    def test_no_match_single_token(self):
        self.assertEqual(resolve_korean("다른표기", ["작은따옴표"]), ("다른표기", False))

    def test_no_match_extract_last_token(self):
        # 매칭 실패 시 마지막 어절을 실제 사용된 표현으로 보고
        self.assertEqual(
            resolve_korean("여기 잘못표기", ["작은따옴표"]), ("잘못표기", False)
        )

    def test_comma_separated_candidates_first(self):
        # "문, 구문" → candidates=["문", "구문"], "문" 사용 시 통과
        self.assertEqual(resolve_korean("문", ["문", "구문"]), ("문", True))

    def test_comma_separated_candidates_second(self):
        self.assertEqual(resolve_korean("구문", ["문", "구문"]), ("구문", True))

    def test_longest_candidate_preferred(self):
        # 후보 중 더 긴 매칭이 가능하면 더 긴 것을 사용된 표기로 간주
        self.assertEqual(
            resolve_korean("동일 출처", ["출처", "동일 출처"]), ("동일 출처", True)
        )


class PairRegexTest(unittest.TestCase):
    """PAIR_RE: 한국어(영어) 병기 검출."""

    def test_simple_pair(self):
        m = PAIR_RE.search("프로퍼티(property)는")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(2), "property")

    def test_multi_word_english(self):
        m = PAIR_RE.search("이벤트 루프(event loop)에서")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(2), "event loop")

    def test_english_with_comma(self):
        m = PAIR_RE.search("브라우저 객체 모델(Browser Object Model, BOM)을")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(2), "Browser Object Model, BOM")

    def test_no_match_korean_only(self):
        self.assertIsNone(PAIR_RE.search("프로퍼티는"))

    def test_no_match_english_only(self):
        # 영어로 시작하는 한국어 그룹은 불가
        self.assertIsNone(PAIR_RE.search("property는"))


class LoadGlossaryTest(unittest.TestCase):
    """load_glossary(): 캐시 CSV에서 용어 맵 빌드."""

    @classmethod
    def setUpClass(cls):
        cls.glossary = load_glossary()

    def test_has_single_quoted(self):
        self.assertIn("single-quoted", self.glossary)
        self.assertEqual(self.glossary["single-quoted"], ["작은따옴표"])

    def test_has_command(self):
        self.assertIn("command", self.glossary)
        self.assertIn("명령어", self.glossary["command"])

    def test_statement_comma_split(self):
        # 시트의 "문, 구문" 표기는 두 후보 모두 인정
        self.assertIn("statement", self.glossary)
        self.assertIn("문", self.glossary["statement"])
        self.assertIn("구문", self.glossary["statement"])

    def test_case_insensitive_key(self):
        # 모든 키는 lowercase
        for key in self.glossary:
            self.assertEqual(key, key.lower())

    def test_no_symbol_keys(self):
        # 시트2의 기호 entry는 PAIR_RE에서 매칭 불가하므로 맵에서도 제외
        for key in self.glossary:
            self.assertRegex(key, r"^[a-z]")


class CheckFileTest(unittest.TestCase):
    """check_file(): 파일 단위 통합 동작."""

    @classmethod
    def setUpClass(cls):
        # 한 번만 캐시 갱신해 테스트 속도 확보 (네트워크 안 되면 캐시 fallback)
        cls.warmup = check_file(write_md("워밍업"))

    def _run(self, content: str) -> dict:
        path = write_md(content)
        try:
            return check_file(path)
        finally:
            os.unlink(path)

    def test_all_passing(self):
        result = self._run(
            "프로퍼티(property)와 명령어(command), 그리고 문(statement)."
        )
        self.assertEqual(result["violations"], [])
        self.assertGreaterEqual(len(result["passed"]), 2)  # property는 시트 외일 수 있음

    def test_violation_single(self):
        result = self._run("다른표기(single-quoted)를 사용했습니다.")
        self.assertEqual(len(result["violations"]), 1)
        v = result["violations"][0]
        self.assertEqual(v["rule_id"], "GLOSSARY-mismatch")
        self.assertEqual(v["severity"], "recommended")
        self.assertEqual(v["problem"], "다른표기(single-quoted)")
        self.assertEqual(v["suggestion"], "작은따옴표(single-quoted)")

    def test_code_block_excluded(self):
        result = self._run(
            "```js\n잘못표기(single-quoted)\n```\n외부에서는 작은따옴표(single-quoted)."
        )
        self.assertEqual(result["violations"], [])

    def test_inline_code_excluded(self):
        result = self._run("`잘못표기(single-quoted)` 인라인 코드는 검사 제외.")
        self.assertEqual(result["violations"], [])

    def test_unknown_term_ignored(self):
        # 시트에 없는 영어 키는 위반/통과 어디에도 분류되지 않음
        result = self._run("문법 구조(syntax structure)는 어쩌고.")
        self.assertEqual(result["violations"], [])
        self.assertNotIn(
            "문법 구조(syntax structure)",
            " ".join(result["passed"]),
        )

    def test_greedy_match_recovers(self):
        # 정규식이 욕심부려도 suffix 매칭으로 정상 통과 처리
        result = self._run("본문에 작은따옴표(single-quoted)가 보입니다.")
        self.assertEqual(result["violations"], [])
        self.assertTrue(
            any("작은따옴표(single-quoted)" in p for p in result["passed"])
        )

    def test_line_number_reported(self):
        result = self._run("줄1\n줄2\n다른표기(single-quoted)\n줄4")
        self.assertEqual(len(result["violations"]), 1)
        self.assertEqual(result["violations"][0]["line"], 3)

    def test_user_approved_sample(self):
        """사용자가 '승인된 번역본'으로 검토 요청한 케이스 — 위반 0건이어야 함."""
        content = (
            "# 코드 구조\n\n"
            "처음으로 배울 것은 코드 블록을 만드는 방법입니다.\n\n"
            "## 문\n\n"
            "문(statement)은 어떤 작업을 수행하는 문법 구조(syntax structure)와 "
            "명령어(command)를 의미합니다.\n"
        )
        result = self._run(content)
        self.assertEqual(
            result["violations"],
            [],
            f"승인된 번역본에서 위반 발생: {result['violations']}",
        )


@unittest.skipUnless(has_network(), "docs.google.com 접근 불가 — 네트워크 테스트 건너뜀")
class CacheRefreshTest(unittest.TestCase):
    """캐시 갱신 동작 — 네트워크 가능할 때만 실행."""

    def setUp(self):
        self.meta_path = REPO_ROOT / "glossary" / "meta.json"
        self.original = self.meta_path.read_text(encoding="utf-8")

    def tearDown(self):
        self.meta_path.write_text(self.original, encoding="utf-8")

    def test_no_refresh_when_hash_same(self):
        # 정상 상태에서는 해시가 같아 refreshed=False
        path = write_md("내용 없음")
        try:
            result = check_file(path)
        finally:
            os.unlink(path)
        self.assertFalse(result["cache"]["refreshed"])
        self.assertIsNone(result["cache"]["network_warning"])

    def test_refresh_when_hash_differs(self):
        meta = json.loads(self.original)
        meta["sheets"]["sheet1"]["sha256"] = "0" * 64  # 가짜 해시로 변경 트리거
        self.meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        path = write_md("내용 없음")
        try:
            result = check_file(path)
        finally:
            os.unlink(path)

        self.assertTrue(
            result["cache"]["refreshed"], "fake hash 주입 후 갱신되지 않음"
        )
        # 갱신 후 meta.json의 sheet1 해시가 원상 복구되었는지
        new_meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        self.assertNotEqual(new_meta["sheets"]["sheet1"]["sha256"], "0" * 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
