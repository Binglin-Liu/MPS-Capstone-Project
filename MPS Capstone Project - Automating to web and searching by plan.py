#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# In[3]:


# Helper function

def close_try_later_modal(driver, timeout=5):
    """
    Detects the 'Please try back later...' modal and closes it if present.
    Returns True if modal was found and closed, False otherwise.
    """
    try:
        # Wait to see if modal heading appears
        modal_heading = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(),'Please try back later')]")
            )
        )

        # Find the modal close button (either 'X' or 'Close')
        close_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class,'usa-modal__close')] | //button[.//span[text()='Close']]"
            ))
        )

        # Click the close button using JavaScript
        driver.execute_script("arguments[0].click();", close_button)
        print("Modal closed automatically.")
        return True

    except TimeoutException:
        # Modal not present
        return False


# In[6]:


# Setup Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# Explicit wait
wait = WebDriverWait(driver, 20)  # Wait up to 20 seconds for elements

# Open the search page
driver.get("https://www.efast.dol.gov/5500Search/")

# Step 1: Close modal if it appears
close_try_later_modal(driver)

# Step 2: Click 'Show Filters'
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[.//span[normalize-space(text())='Show Filters']]")
    )
).click()


# Step 3: Open 'Plan Years' accordion
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class,'filter-category-button') and normalize-space(text())='Plan Years']")
    )
).click()
#

# Step 4: Select 2024
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='planYearList']//a[starts-with(normalize-space(text()), '2024')]")
    )
).click()


# In[18]:


# HELPER FUNCTION TO CLEAR SEARCH BAR BEFORE SEARCHING FOR NEXT PLAN

def clear_plan_name_only(driver, wait, retries=2):
    """
    Clears the second breadcrumb X button (Plan Name) robustly.
    """
    for attempt in range(retries):
        try:
            # Wait for the second X button to be visible and clickable
            plan_name_clear_btn = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "(//button[contains(@class,'breadcrumb-delete-btn')])[2]"
                ))
            )

            # Scroll into view in case it's hidden
            driver.execute_script("arguments[0].scrollIntoView(true);", plan_name_clear_btn)
            
            # Click via JS to avoid overlay issues
            driver.execute_script("arguments[0].click();", plan_name_clear_btn)
            print("🧹 Cleared plan name (second X button).")
            return True

        except TimeoutException:
            print(f"⚠️ Attempt {attempt+1}: Plan name breadcrumb X button not clickable yet.")
            time.sleep(0.3)  # small delay before retry

    print("❌ Could not clear plan name after retries.")
    return False


# In[ ]:


# wait.until(
#     EC.element_to_be_clickable(
#         (By.XPATH, "(//button[contains(@class,'breadcrumb-delete-btn')])[2]")
#     )
# ).click()


# In[19]:


import pandas as pd
import time
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


# Read Excel
excel_file = "/Users/sharonzou/f_5500_2024_all.xlsx"
df = pd.read_excel(excel_file, nrows=10)
plan_names = df['PLAN_NAME'].dropna().tolist()

for plan in plan_names:
    clean_plan = plan.strip().replace("\xa0", " ")
    print(f"\n🔍 Searching for: {clean_plan}")

    # Remove modal if it appears
    driver.execute_script("""
        const modal = document.querySelector('.mmodal');
        if (modal) modal.remove();
    """)

    # Type plan name
    search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-field")))
    search_input.clear()
    search_input.send_keys(clean_plan)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true }))",
        search_input
    )
    time.sleep(0.5)  # debounce

    # Click Go
    go_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Go!']]"))
    )
    driver.execute_script("arguments[0].click();", go_button)

    # Wait and check for the plan robustly
    found = False
    try:
        WebDriverWait(driver, 10).until(
            lambda d: any(
                clean_plan.lower() in row.text.lower()
                for row in d.find_elements(By.CSS_SELECTOR, "table tbody tr")
            )
        )
        found = True
    except TimeoutException:
        found = False
    except StaleElementReferenceException:
        # Retry once if stale
        try:
            WebDriverWait(driver, 5).until(
                lambda d: any(
                    clean_plan.lower() in row.text.lower()
                    for row in d.find_elements(By.CSS_SELECTOR, "table tbody tr")
                )
            )
            found = True
        except:
            found = False

    print(f"✅ Plan exists: {clean_plan}" if found else f"❌ Plan NOT found: {clean_plan}")

    # Clear plan name for next iteration
    try:
        x_buttons = driver.find_elements(By.CSS_SELECTOR, "button.breadcrumb-delete-btn")
        if len(x_buttons) >= 2:
            driver.execute_script("arguments[0].click();", x_buttons[1])
            print("🧹 Cleared plan name (second X button).")
    except:
        pass
    time.sleep(0.5)


# In[ ]:




