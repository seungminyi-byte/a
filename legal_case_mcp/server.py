"""케이스노트 판례 검색 MCP 서버."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import browser, casenote

mcp = FastMCP(
    "legal-case-search",
    instructions=(
        "케이스노트(casenote.kr)에서 대한민국 판례를 검색하고 조회하는 도구입니다. "
        "먼저 casenote_login으로 로그인한 뒤, search_legal_cases로 검색하거나 "
        "get_case_detail로 특정 판례를 조회하세요."
    ),
)

# 페이지를 재사용하기 위한 모듈-레벨 변수
_page = None


async def _get_page():
    global _page
    if _page is None or _page.is_closed():
        _page = await browser.get_page()
    return _page


@mcp.tool()
async def casenote_login() -> str:
    """케이스노트(casenote.kr)에 로그인합니다.

    환경변수 CASENOTE_EMAIL과 CASENOTE_PASSWORD가 설정되어 있어야 합니다.
    로그인 후 세션이 유지되어 이후 검색/조회에 활용됩니다.
    """
    page = await _get_page()
    result = await casenote.login(page)
    return result


@mcp.tool()
async def search_legal_cases(query: str, page_num: int = 1) -> str:
    """키워드로 판례를 검색합니다.

    Args:
        query: 검색할 키워드 (예: "손해배상", "부당해고", "명예훼손")
        page_num: 페이지 번호 (기본값: 1)

    Returns:
        검색된 판례 목록 (사건명, 법원명, 선고일자, URL 등)
    """
    page = await _get_page()
    result = await casenote.search_cases(page, query, page_num)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_case_detail(court: str, case_number: str) -> str:
    """특정 판례의 상세 내용을 조회합니다.

    Args:
        court: 법원명 (예: "대법원", "서울고등법원", "헌법재판소")
        case_number: 사건번호 (예: "2017도19025", "2016다271608")

    Returns:
        판례 상세 내용 (판시사항, 판결요지, 참조조문, 본문 등)
    """
    page = await _get_page()
    result = await casenote.get_case_detail(page, court, case_number)
    return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
