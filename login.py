def login_cookies():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    import time
    import os

    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode if you don't need the GUI
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    driver.get('https://boardgamegeek.com/login')

    # consent_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="I\'m OK with that"]'))
    # )
    # consent_button.click()
    # print('Clicked consent button.')

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'inputUsername'))
    )
    username = driver.find_element(By.ID, 'inputUsername')
    password = driver.find_element(By.ID, 'inputPassword')

    username.click()
    username.send_keys(os.getenv('BGG_USERNAME'))
    password.send_keys(os.getenv('BGG_PASSWORD'))
    password.send_keys(Keys.RETURN)

    time.sleep(5)

    cookies = driver.get_cookies()
    driver.quit()
    
    return cookies