from __future__ import annotations

from urllib.parse import quote

from playwright.async_api import Page

from . import config


async def login(page: Page) -> str:
    """케이스노트에 이메일/비밀번호로 로그인한다."""
    if not config.CASENOTE_EMAIL or not config.CASENOTE_PASSWORD:
        return "환경변수 CASENOTE_EMAIL, CASENOTE_PASSWORD가 설정되지 않았습니다."

    await page.goto(f"{config.CASENOTE_BASE_URL}/login", wait_until="networkidle")

    # 이메일 입력
    email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="이메일"]').first
    await email_input.fill(config.CASENOTE_EMAIL)

    # 비밀번호 입력
    pw_input = page.locator('input[type="password"], input[name="password"]').first
    await pw_input.fill(config.CASENOTE_PASSWORD)

    # 로그인 버튼 클릭
    login_btn = page.locator('button:has-text("로그인"), button[type="submit"]').first
    await login_btn.click()

    # 로그인 완료 대기 (URL 변경 또는 특정 요소 표시)
    try:
        await page.wait_for_url(f"{config.CASENOTE_BASE_URL}/**", timeout=10000)
        # 로그인 실패 시 여전히 /login 페이지에 있을 수 있음
        if "/login" in page.url:
            return "로그인 실패: 이메일 또는 비밀번호를 확인해주세요."
        return "로그인 성공"
    except Exception:
        return "로그인 실패: 타임아웃 또는 페이지 로딩 오류"


async def search_cases(page: Page, query: str, page_num: int = 1) -> dict:
    """키워드로 판례를 검색한다."""
    encoded_query = quote(query)
    url = f"{config.CASENOTE_BASE_URL}/search?q={encoded_query}"
    if page_num > 1:
        url += f"&page={page_num}"

    await page.goto(url, wait_until="networkidle")

    # 검색 결과 파싱 — 실제 HTML 구조에 맞게 셀렉터 조정 필요
    # 일반적인 판례 검색 결과 목록 구조를 가정
    results = []

    # 검색 결과 항목들을 찾는다 (여러 셀렉터 시도)
    items = await page.locator(
        '[class*="search-result"], [class*="case-item"], '
        '[class*="SearchResult"], [class*="CaseItem"], '
        'article, .result-item'
    ).all()

    if not items:
        # 대안: 링크 기반으로 판례 항목 추출
        items = await page.locator('a[href*="/대법원/"], a[href*="/서울"], a[href*="/헌법재판소/"]').all()

    for item in items[:20]:  # 최대 20개
        try:
            text = await item.inner_text()
            href = await item.get_attribute("href") if await item.count() else None

            # 링크가 있는 경우 href에서 정보 추출
            if href is None:
                link_el = item.locator("a").first
                href = await link_el.get_attribute("href") if await link_el.count() else None

            result = {
                "text": text.strip()[:500],  # 텍스트 길이 제한
                "url": f"{config.CASENOTE_BASE_URL}{href}" if href and href.startswith("/") else href,
            }
            results.append(result)
        except Exception:
            continue

    # 페이지 전체 텍스트에서 결과가 없는 경우 대비
    if not results:
        content = await page.content()
        body_text = await page.locator("body").inner_text()
        return {
            "query": query,
            "page": page_num,
            "results": [],
            "raw_text": body_text[:3000],
            "note": "검색 결과를 파싱할 수 없었습니다. raw_text에서 결과를 확인해주세요.",
        }

    return {
        "query": query,
        "page": page_num,
        "count": len(results),
        "results": results,
    }


async def get_case_detail(page: Page, court: str, case_number: str) -> dict:
    """특정 판례의 상세 내용을 조회한다."""
    encoded_court = quote(court)
    encoded_case = quote(case_number)
    url = f"{config.CASENOTE_BASE_URL}/{encoded_court}/{encoded_case}"

    await page.goto(url, wait_until="networkidle")

    result: dict = {
        "court": court,
        "case_number": case_number,
        "url": url,
    }

    # 페이지 제목
    title = await page.title()
    result["title"] = title

    # 판례 본문 영역 파싱 시도
    # 케이스노트의 정확한 HTML 구조에 따라 셀렉터 조정 필요
    sections = {
        "판시사항": '[class*="opinion"], [data-section="opinion"], h3:has-text("판시사항")',
        "판결요지": '[class*="summary"], [data-section="summary"], h3:has-text("판결요지")',
        "참조조문": '[class*="reference"], [data-section="reference"], h3:has-text("참조조문")',
        "참조판례": 'h3:has-text("참조판례")',
        "본문": '[class*="content"], [class*="body"], [class*="full-text"], main, article',
    }

    for section_name, selector in sections.items():
        try:
            el = page.locator(selector).first
            if await el.count() > 0:
                text = await el.inner_text()
                result[section_name] = text.strip()[:5000]
        except Exception:
            continue

    # 섹션별 파싱이 실패한 경우 전체 본문 텍스트를 가져온다
    if len(result) <= 4:  # url, court, case_number, title만 있는 경우
        try:
            body_text = await page.locator("main, #__next, body").first.inner_text()
            result["full_text"] = body_text.strip()[:8000]
        except Exception:
            result["error"] = "판례 내용을 파싱할 수 없었습니다."

    return result
