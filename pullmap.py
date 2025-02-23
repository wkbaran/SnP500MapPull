from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time

# Set up the Chrome WebDriver
service = Service('d:\chromedriver-win64\chromedriver.exe')  # Update with your ChromeDriver path
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Run in headles mode
options.add_argument('--window-size=1920,1080')  # Set window size
driver = webdriver.Chrome(service=service, options=options)

try:
    print("Getting...")
    # Navigate to the FINVIZ S&P 500 heat map
    #driver.get('https://finviz.com/map.ashx')
    driver.set_window_size(1920,1080)
    driver.get('https://www.tradingview.com/heatmap/stock/#%7B%22dataSource%22%3A%22SPX500%22%2C%22blockColor%22%3A%22change%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22grouping%22%3A%22sector%22%7D')

    # Wait for the heat map to load
    WebDriverWait(driver, 10, poll_frequency=2).until(
        #EC.presence_of_element_located((By.ID, 'js-market-heatmap'))
        #EC.visibility_of_element_located((By.ID, 'js-market-heatmap'))
        EC.element_to_be_clickable((By.ID, 'js-market-heatmap'))
    )

    # Allow additional time for dynamic content to load
    time.sleep(5)

    # Execute JavaScript to force dark mode
    driver.execute_script("""
        document.cookie = "theme=dark; path=/";
        document.documentElement.classList.add("theme-dark");
        document.documentElement.classList.remove("theme-light");
        window.initData = window.initData || {};
        window.initData.theme = "dark";
    """)

    # Reload the page to apply the theme setting
    driver.refresh()

    # Wait to ensure dark mode is applied
    time.sleep(3)

    # Capture the screenshot of the entire page
    screenshot = driver.get_screenshot_as_png()

    # Load the screenshot into PIL
    image = Image.open(BytesIO(screenshot))

    # Define the bounding box (left, upper, right, lower) for the heat map
    # These values may need adjustment based on the actual page layout
#    left = 100
#    upper = 200
#    right = 1820
#    lower = 880

    # Find the heatmap element
    heatmap = driver.find_element(By.ID, 'js-market-heatmap')

    # Get location and size
    location = heatmap.location
    size = heatmap.size

    # Crop to heatmap region
    left = location["x"]
    top = location["y"]
    right = left + size["width"]
    bottom = top + size["height"]

    # Crop the image to the bounding box
    heatmap_image = image.crop((left, top, right, bottom))

    # Scale the image by 50%
    new_size = (size["width"] // 2, size["height"] // 2)
    scaled_heatmap = heatmap_image.resize(new_size)

    # Save the cropped image
    heatmap_image.save('sp500_heatmap.png')

finally:
    # Close the WebDriver
    driver.quit()
