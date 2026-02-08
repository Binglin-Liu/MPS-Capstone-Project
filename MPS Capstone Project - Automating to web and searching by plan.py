#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import time
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


# ---------- helpers ----------
def sanitize_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"\s+", " ", str(name)).strip()
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:max_len]


def build_search_query(plan_name: str, max_words: int = 8) -> str:
    s = " ".join(str(plan_name).strip().replace("\xa0", " ").split())
    s = s.replace("&", " ").replace("(", " ").replace(")", " ").replace(",", " ")
    s = re.sub(r"\s+", " ", s).strip()

    drop = {
        "INC", "INC.", "LLC", "L.L.C.", "CO", "CO.", "CORP", "CORPORATION",
        "LTD", "LIMITED", "TRUST", "PLAN", "PROFIT", "SHARING", "SAVINGS",
        "RETIREMENT", "EMPLOYEE", "BENEFIT"
    }
    words = [w for w in s.split() if w.upper() not in drop]
    return " ".join(words[:max_words]) if words else s


def list_pdfs(folder: Path) -> set[str]:
    return {p.name for p in folder.glob("*.pdf")}


def move_new_pdf(download_dir: Path, before: set[str], target_path: Path) -> bool:
    """
    Wait for a new PDF to appear in download_dir, then rename/move to target_path.
    """
    for _ in range(80):  # ~40s
        # Chrome uses .crdownload while downloading
        if any(p.suffix == ".crdownload" for p in download_dir.glob("*.crdownload")):
            time.sleep(0.5)
            continue

        after = list_pdfs(download_dir)
        new_files = list(after - before)
        if new_files:
            newest = download_dir / new_files[0]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                target_path.unlink()
            newest.rename(target_path)
            return True

        time.sleep(0.5)

    return False


def clear_plan_name_only(driver, wait, retries=3) -> bool:
    for attempt in range(retries):
        try:
            btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "(//button[contains(@class,'breadcrumb-delete-btn')])[2]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            driver.execute_script("arguments[0].click();", btn)
            print("🧹 Cleared plan name (breadcrumb X).")
            return True
        except TimeoutException:
            print(f"⚠️ Attempt {attempt+1}: Plan name breadcrumb X not clickable yet.")
            time.sleep(0.4)
    print("❌ Could not clear plan name after retries.")
    return False


def close_try_later_modal(driver, timeout=3) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Please try back later')]"))
        )
        close_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class,'usa-modal__close')] | //button[.//span[text()='Close']]"
            ))
        )
        driver.execute_script("arguments[0].click();", close_button)
        print("Modal closed automatically.")
        return True
    except TimeoutException:
        return False


def apply_year_filter(driver, wait, year: str):
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[.//span[normalize-space(text())='Show Filters']]")
    )).click()

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'filter-category-button') and normalize-space(text())='Plan Years']")
    )).click()

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//div[@id='planYearList']//a[starts-with(normalize-space(text()), '{year}')]")
    )).click()


def click_download_for_year(driver, wait, year: str) -> bool:
    """
    Robustly find a row with year and click the download svg.
    Handles stale element by retrying.
    """
    for attempt in range(3):
        try:
            # re-fetch rows each attempt (important!)
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 3:
                    continue
                year_text = cols[2].text.strip()
                if year in year_text:
                    download_btn = cols[0].find_element(By.TAG_NAME, "svg")
                    driver.execute_script("arguments[0].scrollIntoView();", download_btn)
                    time.sleep(0.3)
                    driver.execute_script(
                        "arguments[0].dispatchEvent(new Event('click', {bubbles: true}));",
                        download_btn
                    )
                    return True
            return False
        except StaleElementReferenceException:
            print(f"⚠️ stale element while locating download row (retry {attempt+1}/3)")
            time.sleep(0.8)
    return False


# ---------- CONFIG ----------
TARGET_URL = "https://www.efast.dol.gov/5500Search/"
TARGET_YEAR = "2024"

csv_file = "filtered_401k_403b_plans.csv"

# 临时下载落地（为了识别“新下载的那个文件”）
TEMP_DOWNLOAD_DIR = Path("outputs_tmp_downloads").resolve()
TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ✅ 你要的：最终都放在 outputs/ 下面
OUTPUT_DIR = Path("outputs").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LIMIT = 10


def main():
    df = pd.read_csv(csv_file)
    if "Full_Plan_Name" not in df.columns:
        raise ValueError(f"Column 'Full_Plan_Name' not found in {csv_file}. Found: {df.columns.tolist()}")

    plan_names = df["Full_Plan_Name"].dropna().astype(str).tolist()[:LIMIT]

    # Selenium setup
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    prefs = {"download.default_directory": str(TEMP_DOWNLOAD_DIR)}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(TARGET_URL)
        close_try_later_modal(driver)
        apply_year_filter(driver, wait, TARGET_YEAR)

        for raw_plan in plan_names:
            query = build_search_query(raw_plan)
            plan_slug = sanitize_filename(raw_plan)

            print(f"\n🔍 Searching for: {query}")

            # search
            search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-field")))
            search_input.clear()
            search_input.send_keys(query)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                search_input
            )
            time.sleep(0.4)

            try:
                go_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Go!']]")))
                driver.execute_script("arguments[0].click();", go_button)
            except TimeoutException:
                pass

            # check results exist
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) > 0
                )
                print(f"✅ Results exist for query: {query}")
            except TimeoutException:
                print(f"❌ No results returned for query: {query}")
                cleared = clear_plan_name_only(driver, wait)
                if not cleared:
                    print("🔄 Refresh fallback...")
                    driver.refresh()
                    close_try_later_modal(driver)
                    apply_year_filter(driver, wait, TARGET_YEAR)
                continue

            # download
            before = list_pdfs(TEMP_DOWNLOAD_DIR)
            clicked = click_download_for_year(driver, wait, TARGET_YEAR)

            if clicked:
                print(f"⬇️ Download clicked ({TARGET_YEAR})")

                # ✅ final file goes directly under outputs/
                target_pdf = OUTPUT_DIR / f"{plan_slug}__{TARGET_YEAR}.pdf"
                moved = move_new_pdf(TEMP_DOWNLOAD_DIR, before, target_pdf)
                if moved:
                    print(f"✅ Saved -> {target_pdf}")
                else:
                    print("⚠️ Download not detected (maybe blocked / slow).")
            else:
                print(f"⚠️ No {TARGET_YEAR} row found to download for this query.")

            # clear for next
            cleared = clear_plan_name_only(driver, wait)
            if not cleared:
                print("🔄 Refresh fallback...")
                driver.refresh()
                close_try_later_modal(driver)
                apply_year_filter(driver, wait, TARGET_YEAR)

            time.sleep(0.4)

    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    main()

