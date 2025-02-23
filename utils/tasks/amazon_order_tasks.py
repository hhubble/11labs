import asyncio
import json
import os
from multiprocessing import Process
from typing import Dict, Optional

import openai
from litellm import acompletion
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


async def extract_search_details(query: str) -> Dict[str, str]:
    """Use LLM to extract search parameters from the query."""
    system_prompt = """
    Convert the shopping query into a simple search term.
    - If a price limit is mentioned, ignore it
    - If a quantity is mentioned, ignore it
    - Just return the core product description
    
    Example:
    Input: "Find me 2 blue water bottles under $20"
    Output: blue water bottle
    
    Return only the search term, with no additional text or formatting.
    """

    response = await acompletion(
        model="groq/mixtral-8x7b-32768",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        api_key=os.getenv("GROQ_API_KEY"),
    )

    search_term = response.choices[0].message.content.strip()
    return {"search_term": search_term, "quantity": 1, "max_price": None}


def setup_chrome():
    """Configure and return ChromeDriver with appropriate options"""
    options = webdriver.ChromeOptions()

    # Add headless mode
    options.add_argument("--headless=new")  # Using the new headless mode

    # Rest of the existing Chrome options
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")

    # Set preferences to avoid detection
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Chrome(options=options)


async def click_with_retry(driver, element, max_retries=3):
    """Attempt to click an element with multiple retry strategies"""
    for attempt in range(max_retries):
        try:
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(0.5)

            # Try regular click first
            element.click()
            return True
        except ElementClickInterceptedException:
            try:
                # Try JavaScript click if regular click fails
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                if attempt == max_retries - 1:
                    raise
                asyncio.sleep(1)
        except StaleElementReferenceException:
            if attempt == max_retries - 1:
                raise
            asyncio.sleep(1)
    return False


async def add_to_amazon_cart(query: str, max_retries: int = 3) -> Dict[str, str]:
    """
    Opens a browser using Selenium, searches Amazon, and adds item to cart.
    Returns status, any error messages, the product title, and product URL.
    """
    driver = None
    try:
        # Extract search details using LLM
        search_details = await extract_search_details(query)
        print(f"Search details extracted: {search_details}")

        # Setup Chrome with anti-detection measures
        driver = setup_chrome()
        wait = WebDriverWait(driver, 10)

        # Go to Amazon
        print("Navigating to Amazon...")
        driver.get("https://www.amazon.com")
        print(f"Current URL: {driver.current_url}")
        await asyncio.sleep(3)  # Wait for page to fully load

        # Search for the item
        print("Searching for item...")
        search_box = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        await asyncio.sleep(1)
        search_box.send_keys(search_details["search_term"])
        await asyncio.sleep(0.5)
        search_box.send_keys(Keys.RETURN)
        print(f"Search results URL: {driver.current_url}")
        await asyncio.sleep(3)

        # Find any product link that wraps an s-image
        product_selectors = [
            ".s-result-item .s-image",  # Find the image first
        ]

        product_found = False
        for selector in product_selectors:
            try:
                print(f"Trying selector: {selector}")
                # Find all product images
                images = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )

                # Try clicking each product until one works
                for image in images[:5]:  # Try first 5 products
                    try:
                        # Get the parent link of the image
                        parent_link = image.find_element(By.XPATH, "./ancestor::a[1]")

                        # Ensure element is in viewport
                        driver.execute_script("arguments[0].scrollIntoView(true);", parent_link)
                        await asyncio.sleep(1)

                        # Check if link is visible and clickable
                        if parent_link.is_displayed() and parent_link.is_enabled():
                            await click_with_retry(driver, parent_link)
                            product_found = True
                            break
                    except (StaleElementReferenceException, ElementClickInterceptedException):
                        continue

                if product_found:
                    break

            except TimeoutException:
                continue

        if not product_found:
            raise Exception("Could not find any clickable product")

        # After clicking product, get the product URL
        product_url = driver.current_url
        print(f"Product page URL: {product_url}")
        await asyncio.sleep(3)

        # Try different selectors for product title
        title_selectors = [
            (By.ID, "productTitle"),
            (By.CSS_SELECTOR, "h1.product-title-word-break"),
        ]

        product_title = None
        for selector_type, selector_value in title_selectors:
            try:
                title_element = wait.until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                product_title = title_element.text.strip()
                break
            except TimeoutException:
                continue

        if not product_title:
            product_title = "Unknown Product"

        # Try different selectors for Add to Cart button
        cart_button_selectors = [
            (By.ID, "add-to-cart-button"),
            (By.NAME, "submit.add-to-cart"),
            (By.CSS_SELECTOR, "#add-to-cart-button-ubb"),
        ]

        cart_button = None
        for selector_type, selector_value in cart_button_selectors:
            try:
                cart_button = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                break
            except TimeoutException:
                continue

        if not cart_button:
            raise Exception("Could not find Add to Cart button")

        # Click Add to Cart
        await click_with_retry(driver, cart_button)
        await asyncio.sleep(2)

        # Wait for cart confirmation
        wait.until(EC.presence_of_element_located((By.ID, "nav-cart-count")))
        print("Successfully added to cart!")
        await asyncio.sleep(2)

        result = {
            "status": "success",
            "message": f"Successfully added {search_details['search_term']} to cart",
            "product_title": product_title,
            "product_url": product_url,
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        result = {"status": "error", "message": str(e), "product_title": None, "product_url": None}

    finally:
        if driver:
            print("Closing browser...")
            await asyncio.sleep(1)
            driver.quit()

        return result


# Move the process_wrapper function outside of run_amazon_cart_process
def process_wrapper(query: str):
    async def wrapper():
        return await add_to_amazon_cart(query)

    return asyncio.run(wrapper())


async def run_amazon_cart_process(query: str) -> bool:
    """
    Runs the Amazon cart addition in a separate background process.
    Returns the Process object for tracking.
    """
    process = Process(target=process_wrapper, args=(query,))
    process.start()
    print(f"Amazon cart process started: {process}")
    return True


if __name__ == "__main__":
    result = asyncio.run(add_to_amazon_cart("Find me a blue water bottle under $20"))
    print(result.get("message"))
