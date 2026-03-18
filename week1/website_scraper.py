"""
website_scraper.py — JS-capable website scraper using undetected Chrome.

Uses undetected-chromedriver to bypass bot-detection on JavaScript-heavy sites,
then extracts the visible text from the fully rendered page.

Dependencies (install via uv from the project root):
    uv add undetected-chromedriver selenium rich

Usage:
    python week1/website_scraper.py https://example.com
    python week1/website_scraper.py https://openai.com https://anthropic.com
"""

import sys
import subprocess
import time

REQUIRED_PACKAGES = {
    "undetected_chromedriver": "undetected-chromedriver",
    "selenium": "selenium",
    "rich": "rich",
}


def _ensure_dependencies():
    """Check that all required packages are importable; install any that are missing via uv."""
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        from rich.console import Console

        console = Console()
        console.print(
            f"\n📦 [bold yellow]Missing packages:[/] {', '.join(missing)}. Installing with uv…\n"
        )
        subprocess.check_call(["uv", "add"] + missing)
        console.print("[bold green]✅ All dependencies installed![/]\n")


_ensure_dependencies()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()


def fetch_js_website(url: str, *, headless: bool = True, timeout: int = 30) -> str:
    """
    Scrape the visible text of a JavaScript-rendered webpage.

    Launches a headless Chrome instance via undetected-chromedriver so that
    sites protected by Cloudflare, Akamai, or similar bot-detection don't
    block the request.  The browser fully renders the page (including JS),
    waits for the <body> element, and returns its inner text.

    Args:
        url:      The webpage URL to scrape.
        headless: Run Chrome without a visible window (default True).
        timeout:  Max seconds to wait for the page to load.

    Returns:
        The visible text content of the page body.
    """
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        # --- Phase 1: Launch browser ---
        task = progress.add_task("🚀 Launching stealth browser…", total=4)

        options = uc.ChromeOptions()
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        driver = uc.Chrome(options=options, use_subprocess=False, version_main=144)
        driver.set_page_load_timeout(timeout)
        progress.update(task, advance=1, description="🟢 Browser launched")

        try:
            # --- Phase 2: Navigate to URL ---
            progress.update(task, description=f"🌐 Navigating to {url}")
            start = time.perf_counter()
            try:
                driver.get(url)
            except Exception:
                # Timeout on page load is expected for heavy sites; the body
                # may still be available thanks to the 'eager' load strategy.
                pass
            elapsed = time.perf_counter() - start
            progress.update(task, advance=1, description=f"📡 Page response received ({elapsed:.1f}s)")

            # --- Phase 3: Wait for DOM ---
            progress.update(task, description="⏳ Waiting for page body to render…")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            progress.update(task, advance=1, description="✅ DOM ready")

            # --- Phase 4: Extract text ---
            progress.update(task, description="📝 Extracting text content…")
            content = driver.find_element(By.TAG_NAME, "body").text
            progress.update(task, advance=1, description="🏁 Done!")
        finally:
            driver.quit()

    char_count = len(content)
    word_count = len(content.split())
    console.print(
        Panel(
            f"[green]Words:[/] {word_count:,}  ·  [green]Characters:[/] {char_count:,}",
            title=f"📄 Scraped [bold]{url}[/bold]",
            border_style="bright_cyan",
        )
    )

    return content


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print(
            Panel(
                "[bold]Usage:[/]  python website_scraper.py <url> [url …]",
                title="🕷️  Website Scraper",
                border_style="red",
            )
        )
        sys.exit(1)

    for url in sys.argv[1:]:
        console.rule(f"[bold magenta]🔎 Scraping: {url}")
        text = fetch_js_website(url)
        console.print(f"\n[dim]{text[:500]}{'…' if len(text) > 500 else ''}[/dim]\n")
