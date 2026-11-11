"""Browser-level geometry regression for the animated solar landing page.

Run with a local Streamlit server started on http://127.0.0.1:8501.
Saves desktop/mobile screenshots as CI artifacts for visual inspection.
"""
from pathlib import Path
import time
import urllib.request

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8501"
ARTIFACTS = Path("layout-screenshots")
ARTIFACTS.mkdir(exist_ok=True)


def box(page, selector: str) -> dict:
    locator = page.locator(selector)
    locator.wait_for(timeout=45000)
    bounds = locator.bounding_box()
    assert bounds, f"Missing layout rectangle for {selector}"
    return bounds


def overlaps(a: dict, b: dict, slack: float = 3.0) -> bool:
    return (a["x"] < b["x"] + b["width"] - slack
            and b["x"] < a["x"] + a["width"] - slack
            and a["y"] < b["y"] + b["height"] - slack
            and b["y"] < a["y"] + a["height"] - slack)


def verify(page, label: str) -> None:
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.get_by_role("button", name="01 · Portfolio").wait_for(timeout=60000)
    page.locator(".wr-sun").wait_for(timeout=60000)
    page.wait_for_timeout(1400)

    heading = box(page, ".wr-space-head")
    sun = box(page, ".wr-sun")
    names = {
        "portfolio": "01 · Portfolio", "analytics": "02 · Analytics",
        "discover": "03 · Discover", "fire": "04 · FIRE",
        "lab": "05 · Model Lab",
    }
    planets = {
        slug: page.get_by_role("button", name=name).bounding_box()
        for slug, name in names.items()
    }
    assert all(planets.values()), f"Planet not rendered: {planets}"
    assert heading["y"] + heading["height"] + 10 < sun["y"], (
        f"Hero overlaps sun: {heading} vs {sun}"
    )
    for name, rectangle in planets.items():
        assert not overlaps(heading, rectangle), f"{name} overlaps title"
        assert not overlaps(sun, rectangle), f"{name} overlaps sun"
        assert rectangle["x"] >= -2 and rectangle["x"] + rectangle["width"] <= page.viewport_size["width"] + 2, (
            f"{name} overflows horizontally: {rectangle}"
        )
    for first in planets:
        for second in planets:
            if first < second:
                assert not overlaps(planets[first], planets[second]), (
                    f"{first} overlaps {second}"
                )
    center_x = lambda value: value["x"] + value["width"] / 2
    assert center_x(planets["portfolio"]) < center_x(sun) < center_x(planets["analytics"])
    assert center_x(planets["lab"]) < center_x(sun) < center_x(planets["discover"])
    assert abs(center_x(planets["fire"]) - center_x(sun)) < max(40, sun["width"] * .35)
    page.screenshot(path=str(ARTIFACTS / f"{label}.png"), full_page=True)
    print(f"{label}: planets aligned; heading separated; screenshot captured.")


def wait_for_streamlit() -> None:
    for _ in range(90):
        try:
            with urllib.request.urlopen(URL + "/_stcore/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(.5)
    raise RuntimeError("The local Streamlit server did not become ready.")


def main() -> None:
    wait_for_streamlit()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            verify(desktop, "desktop")
            desktop.get_by_role("button", name="04 · FIRE").click()
            desktop.get_by_text("YOUR EXPECTED EXPENSES AT RETIREMENT").wait_for(timeout=30000)
            desktop.get_by_label("Monthly expenses today (₹)").fill("1,00,000")
            desktop.get_by_label("Monthly expenses today (₹)").press("Tab")
            desktop.wait_for_timeout(800)
            assert desktop.get_by_text("MONTHLY AT RETIREMENT").count() > 0
            desktop.screenshot(path=str(ARTIFACTS / "fire.png"), full_page=True)
            mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
            verify(mobile, "mobile")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
