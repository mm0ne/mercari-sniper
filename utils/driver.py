from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import utils.constant as uc


def init_web_driver(executable_path: str) -> webdriver.Chrome.__class__:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options, executable_path=executable_path)

    return driver


def scrape(url_payload: str, executable_path: str) -> webdriver.Chrome.__class__:
    while True:
        driver = init_web_driver()
        try:
            driver.get(url_payload)
            # Wait until the specific <li> elements with the given class are present
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, uc.IMAGE_CLASS)))
            break
        except Exception:
            driver.close()
            driver.quit()
    return driver
