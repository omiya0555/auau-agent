import os
from typing import List, Dict, Any
from tavily import TavilyClient
from strands import tool

ALLOWED_TIME_RANGES = {"d", "w", "m", "y"}

# グローバルに 1 度だけ初期化（agent 起動前に呼び出される想定）
_api_key = os.getenv("TAVILY_API_KEY")
_client: TavilyClient | None = None
if _api_key:
    _client = TavilyClient(api_key=_api_key)

def _ensure_client() -> TavilyClient:
    print("ensure client")
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("環境変数 TAVILY_API_KEY が設定されていません")
        _client = TavilyClient(api_key=api_key)
    return _client


def _format_results(resp: Dict[str, Any]) -> str:
    results = resp.get("results", [])
    if not results:
        return "検索結果はありません。"
    lines: List[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "(no title)"
        url = r.get("url") or ""
        content = (r.get("content") or "").strip()
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"[{i}] {title}\nURL: {url}\n{content}\n")
    return "\n".join(lines).rstrip()


# include_domains: list[str] = []

@tool
def web_search(
    query: str,
    time_range: str | None = None,
    include_domains: list[str] | None = None,
):
    """Tavily を用いたウェブ検索ツール。

    Args:
        query: 検索クエリ
        time_range: 'd','w','m','y' のいずれかで期間フィルタ
        include_domains: 絞り込みたいドメインのリスト
    Returns:
        Strands Agent 互換の辞書 (status/content)
    """
    print("run tool")
    if not query or not query.strip():
        return {"status": "error", "content": [{"text": "query は必須です"}]}
    if time_range and time_range not in ALLOWED_TIME_RANGES:
        return {"status": "error", "content": [{"text": f"time_range は {ALLOWED_TIME_RANGES} のいずれか"}]}

    try:
        client = _ensure_client()
        resp = client.search(
            query=query,
            max_results=10,
            time_range=time_range,
            include_domains=include_domains,
        )
        formatted = _format_results(resp)
        return {"status": "success", "content": [{"text": formatted}, {"json": resp}]}
    except Exception as e:
        return {"status": "error", "content": [{"text": f"検索失敗: {type(e).__name__}: {e}"}]}
    