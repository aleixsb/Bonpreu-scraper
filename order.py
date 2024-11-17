from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
import os


def get_product_links():
    # Connect to the SQLite database
    conn = sqlite3.connect('/app/db/bonpreu.db')
    cursor = conn.cursor()
    
    # Query all product links from the table
    cursor.execute("SELECT link FROM proximacompra")
    links = cursor.fetchall()
    print(f"Items from DB: {links}")
    
    # Close the connection
    conn.close()
    
    # Return the list of links
    return links


def login(driver):
    # Open the login page
    driver.get("https://app.bonpreu.cat/openid-connect-server-webapp/login?lang=ca-ES&channel=osp")
    # Wait for the username field to be present and fill it
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "j_username"))
    )
    username_field.send_keys("aleixsb@gmail.com")  # Replace with your username/email
    # Wait for the password field to be present and fill it
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "j_password"))
    )
    bonpreu_password = os.getenv('Bonpreu_PASSWORD')
    password_field.send_keys(bonpreu_password)  # Replace with your password
    # Wait for the login button to be clickable and click it
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "loginButton"))
    )
    login_button.click()
    # Wait for a few seconds to ensure the login is processed (you can wait for a specific element on the next page)
    time.sleep(5)  # Adjust time if necessary
    # Now you can interact with the logged-in page or print out information
    # Example: Print the current URL after logging in (you can replace this with further steps)
    print("Successfully logged in! Current URL:", driver.current_url)

def scroll_to_element(driver, element):
    """
    Scroll the page to the given element to make it visible.
    """
    driver.execute_script("arguments[0].scrollIntoView();", element)

def close_cookie_banner(driver):
    """
    Close the cookie consent banner by clicking the 'Acceptar' button and ensure the overlay disappears.
    """
    try:
        # Find and click the 'Acceptar' button to close the cookie banner
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        close_button.click()
        print("Cookie consent banner closed.")
        
        # Wait for the overlay to disappear completely
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "onetrust-pc-dark-filter"))
        )
        print("Cookie banner overlay disappeared.")
        
    except Exception as e:
        print("No cookie banner found or couldn't close it.")
        print(str(e))

def click_add_button(driver):
    """
    This function waits for and clicks the 'Afegeix' button once it's clickable.
    :param driver: Selenium WebDriver instance.
    """
    try:
        # Wait until the 'Afegeix' button is clickable
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Afegeix')]"))
        )
        
        # Scroll to the button if it's not in view
        scroll_to_element(driver, button)
        
        # Click the 'Afegeix' button
        button.click()
        print("Button 'Afegeix' clicked.")
    except Exception as e:
        print("Error: Button 'Afegeix' not found or not clickable.")
        print(str(e))


def main():
    # Set up Selenium with Chrome WebDriver
    # Create a new instance of the Chrome driver 
    option = webdriver.ChromeOptions() 
    
    option.add_argument("--disable-gpu") 
    option.add_argument("--disable-extensions") 
    option.add_argument("--disable-infobars") 
    option.add_argument("--start-maximized") 
    option.add_argument("--disable-notifications") 
    option.add_argument('--headless') 
    option.add_argument('--no-sandbox') 
    option.add_argument('--disable-dev-shm-usage') 

    service = Service()
    driver = webdriver.Chrome(service=service, options=option) 

    # Log in to Bonpreu
    login(driver)
    
    # Get the products from SQLite
    products = get_product_links()
    
    # Loop through each product and add it to the cart
    for product in products:
        url = product[0]
        print(f"Trying to add {url} to shopping cart")
        driver.get(url)
        print(driver)
        close_cookie_banner(driver)
        click_add_button(driver)
    
    driver.quit()  # Close the browser after all actions

if __name__ == "__main__":
    main()
