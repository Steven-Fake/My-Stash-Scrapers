from typing import Literal
from typing import Optional, Dict, Any
from pathlib import Path
import json
import time

from bs4 import BeautifulSoup as Soup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth
from py_common import log


class StealthPlaywright:
    """
    Async Playwright wrapper that integrates playwright_stealth.
    Supports usage as an async context manager: `async with StealthPlaywright() as sp:`
    or explicit start()/close() calls.
    """

    def __init__(
            self,
            browser: Literal["chromium", "firefox", "webkit"] = "chromium",
            headless: bool = True,
            persist_cookies: bool = False,
            cookies_path: Optional[str] = None,
            request_headers: Optional[Dict[str, str]] = None,
            browser_args: Optional[list[str]] = None,
            context_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self._browser_type: Literal["chromium", "firefox", "webkit"] = browser
        self._headless = headless
        self._request_headers = request_headers or {}  # default request headers
        self._browser_args = browser_args or ["--lang=zh-CN"]  # browser launch arguments
        self._context_kwargs = context_kwargs or {"locale": "zh-CN"}  # page context arguments
        self._playwright_ctx = None
        self._p = None

        self._persist_cookies = persist_cookies
        # store cookies path as Path for convenience
        self._cookies_path = Path(cookies_path) if cookies_path else Path("cookies.json")

        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self):
        # Enter the Stealth async context to get the modified playwright instance
        self._playwright_ctx = Stealth().use_async(async_playwright())
        self._p = await self._playwright_ctx.__aenter__()  # returns async_playwright instance

        browser = getattr(self._p, self._browser_type)
        if not browser:
            raise ValueError(f"Unsupported browser type: {self._browser_type}")

        self.browser = await browser.launch(headless=self._headless, args=self._browser_args)

        # prepare context parameters and optionally load storage_state if cookies persistence enabled
        context_params = dict(self._context_kwargs)
        context_params["extra_http_headers"] = self._request_headers

        if self._persist_cookies and self._cookies_path.exists():
            # load existing storage_state (cookies + localStorage) by path
            try:
                # quick validation: check file contains valid JSON to avoid Playwright errors
                with self._cookies_path.open("r", encoding="utf-8") as f:
                    json.load(f)
                context_params["storage_state"] = str(self._cookies_path)
                log.info(f"Loaded storage_state from {self._cookies_path}")
            except Exception as e:
                # backup corrupt file and continue with fresh context
                try:
                    bad_path = self._cookies_path.with_name(self._cookies_path.name + f".corrupt.{int(time.time())}")
                    self._cookies_path.rename(bad_path)
                    log.warning(f"Corrupt storage_state at {self._cookies_path} renamed to {bad_path}: {e}")
                except Exception as e2:
                    log.error(
                        f"Failed to backup corrupt storage_state {self._cookies_path}: {e2} (original error: {e})")
                # do not set storage_state so a fresh context will be created

        self.context = await self.browser.new_context(**context_params)
        self.page = await self.context.new_page()
        return self

    async def close(self):
        """
        Close the page, context, and browser in the correct order, then exit the stealth context.
        :return:
        """
        try:
            # if persistence enabled, save current storage state (cookies + localStorage)
            if self._persist_cookies and self.context:
                try:
                    # ensure parent dir exists
                    self._cookies_path.parent.mkdir(parents=True, exist_ok=True)
                    await self.context.storage_state(path=str(self._cookies_path))
                    log.info(f"Saved storage_state to {self._cookies_path}")
                except Exception as e:
                    log.error(f"Failed to save storage_state to {self._cookies_path}: {e}")

            if self.context:
                await self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass
        if self._playwright_ctx:
            await self._playwright_ctx.__aexit__(None, None, None)
        self._playwright_ctx = None
        self._p = None
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def new_page(self) -> Page:
        if not self.context:
            raise RuntimeError("Context not started. Call start() first.")
        self.page = await self.context.new_page()
        return self.page

    async def goto(self, url: str, **kwargs) -> None:
        if not self.page:
            await self.new_page()
        await self.page.goto(url, **kwargs)

    async def wait_for_selector(self, selector: str, **kwargs) -> None:
        if not self.page:
            raise RuntimeError("No page available.")
        await self.page.wait_for_selector(selector, **kwargs)

    async def query_selector_all(self, selector: str):
        if not self.page:
            raise RuntimeError("No page available.")
        return await self.page.query_selector_all(selector)

    async def evaluate(self, expression: str):
        if not self.page:
            raise RuntimeError("No page available.")
        return await self.page.evaluate(expression)

    @property
    async def navigator_webdriver(self) -> Any:
        # 返回 navigator.webdriver 的值（通常用于检测）
        return await self.evaluate("navigator.webdriver")

    async def fetch_soup(self, url: str, **kwargs) -> Soup:
        await self.goto(url, **kwargs)
        await self.page.wait_for_load_state("domcontentloaded")

        if close_button := await self.page.query_selector("div.modal-card a.button.is-success"):
            await close_button.click()

        content = await self.page.content()
        return Soup(content, "html.parser")
