from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
import os


def create_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("/app/db/bonpreu.db")
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            link TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_item(name, link, price):
    conn = sqlite3.connect("/app/db/bonpreu.db")
    cursor = conn.cursor()
    try:
        # Insert the item or update if the link already exists
        cursor.execute("""
            INSERT INTO items (link, name, price) VALUES (?, ?, ?)
            ON CONFLICT(link) DO UPDATE SET
                name=excluded.name,
                price=excluded.price
        """, (link, name, price))  # Pass actual values, not the strings 'link', 'name', 'price'
        
        # Commit the transaction
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Item with link {link} already exists in the database.")
    finally:
        # Close the connection
        conn.close()

def fetch_items():
    conn = sqlite3.connect("/app/db/bonpreu.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    conn.close()
    return cursor.fetchall()


def get_order_details(driver):
    # Navigate to the orders page (modify the URL or navigation step as needed)
    driver.get('https://www.compraonline.bonpreuesclat.cat/orders')  # Replace with actual orders URL
    # Wait for the orders page to load
    time.sleep(5)
    # Find all order containers
    orders = driver.find_elements(By.CSS_SELECTOR, 'a[data-test="order-card-past"]')
    # Loop through each order to extract date and price
    order_details = []
    for order in orders:
        # Extract the order date
        date = order.find_element(By.CSS_SELECTOR, 'h3').text.split(' - ')[0]  # Get the date part
        # Extract the order price
        price = order.find_element(By.CSS_SELECTOR, 'span._text_16wi0_1._text--m_16wi0_23').text
        # Open the order details page
        order_link = order.get_attribute('href')
        # Append order details with items
        order_details.append({
            'date': date,
            'price': price,
            'link': order_link,
            'items': []
        })
    return order_details


def get_order_items_by_names_and_links_and_price(driver, order_details):
    for order in order_details:
        # Navigate to the order details page
        driver.get(order['link'])
        time.sleep(10)
        # Wait for the items container to be present on the page
        try:
            print(f"Looking for items in: {order['link']}")
            # Wait for the items container to load fully
            items_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test="received-items"]'))  # Correct selector for items container
            )
            # Extract all item names and their links
            items_info = []
            # Locate all <a> tags inside <h3> tags (which contain the item names and links)
            item_elements = items_container.find_elements(By.CSS_SELECTOR, 'h3 a[data-test="fop-product-link"]')
            price_elements = items_container.find_elements(By.CSS_SELECTOR, 'div[data-test="fop-price-wrapper"] strong[data-test="fop-price"]')
            print(f"Found: {len(item_elements)} products")
            # Ensure that the number of item elements matches the number of price elements
            if len(item_elements) == len(price_elements):
                # Loop through both item_elements and price_elements
                for item, price in zip(item_elements, price_elements):
                    # Extract the name, link, and price for each item
                    item_name = item.text.strip()  # Get the name of the item
                    item_link = item.get_attribute('href')  # Get the link of the item
                    item_price = price.text.strip()  # Get the price of the item
                    # Add the item information to items_info list
                    items_info.append({'name': item_name, 'link': item_link, 'price': item_price})
            else:
                print("Mismatch between number of items and prices")
            # Update the order details with item names and links
            order['items'] = items_info
            print(f"Order {order['date']} - Items:")
            for item in items_info:
                print(f"  - Item: {item['name']}, Link: {item['link']}, Price: {item['price']}")
        except Exception as e:
            print(f"Error loading order details page for {order['link']}: {e}")

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

def unique_products(orders, unique_items):
    # Iterate through each order
    for order in orders:
        for item in order['items']:
            item_link = item['link']  # Use the link as the unique identifier
            # Only add the item if the link is not already in the unique_items dictionary
            if item_link not in unique_items:
                unique_items[item_link] = {'name': item['name'], 'link': item['link'], 'price': item['price']}
    # Now `unique_items` contains only unique items based on the link
    # Convert the dictionary back to a list of dictionaries if needed
    unique_items = list(unique_items.values())


# Original local selenium
# # Set up Chrome options for headless mode
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Running headless (no UI)
# options.add_argument("--window-size=1920,1080")  # Set window size for headless mode

# # Initialize the browser with Selenium Manager (no need to manually set chromedriver path)
# service = Service()
# driver = webdriver.Chrome(service=service, options=options)


## New test

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



try:
    login(driver)
    orders = get_order_details(driver)
    get_order_items_by_names_and_links_and_price(driver, orders)
    # Print all order details
    for order in orders:
        print(f"Date: {order['date']}, Total Price: {order['price']}, link: {order['link']}, items: {order['items']}")
    # Create a set to store unique items based on the link
    unique_items = {}
    unique_products(orders,unique_items)
    print(f"Unique product list: {len(unique_items)}")
    print(f"{unique_items}")

    # Update DB
    # Insert all items from unique_items dictionary
    for item_link, item_data in unique_items.items():
        print(f"instering to db: {item_data}")
        insert_item(item_data['name'], item_data['link'], item_data['price'])


finally:
    # Close the browser after the operation
    driver.quit()
