# app/services/whatsapp_automation.py - CORRECTED VERSION
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import asyncio
import os
from datetime import datetime


def get_chrome_profile_path():
    """Get the default Chrome profile path for Windows"""
    username = os.getenv('USERNAME')
    default_path = f"C:/Users/{username}/AppData/Local/Google/Chrome/User Data"
    
    # Check if default path exists
    if os.path.exists(default_path):
        return default_path
    
    # Fallback paths
    fallback_paths = [
        f"C:/Users/{username}/AppData/Local/Google/Chrome/User Data/Default",
        "C:/Users/admin/AppData/Local/Google/Chrome/User Data",  # Your original
    ]
    
    for path in fallback_paths:
        if os.path.exists(path):
            return path
    
    print("⚠️ Chrome profile path not found. Please update manually.")
    return "C:/Users/Admin/AppData/Local/Google/Chrome/User Data"  # Correct path


def create_chrome_driver():
    """Create Chrome WebDriver with proper configuration"""
    options = webdriver.ChromeOptions()
    
    # Use the correct Chrome profile path
    options.add_argument("--user-data-dir=C:/Users/Admin/AppData/Local/Google/Chrome/User Data")
    
    # Additional options for stability
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Optional: Run in background (comment out for debugging)
    # options.add_argument("--headless")
    
    try:
        print("🔧 Attempting to create Chrome driver...")
        print("📁 Using profile: C:/Users/Admin/AppData/Local/Google/Chrome/User Data")
        
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver created successfully")
        
        # Remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ WebDriver detection avoidance applied")
        
        return driver
    except WebDriverException as e:
        print(f"❌ Error initializing WebDriver: {e}")
        print("💡 Make sure ChromeDriver is installed and in PATH")
        print("💡 Install with: pip install chromedriver-autoinstaller")
        print("🔍 Checking if Chrome profile path exists...")
        
        import os
        profile_path = "C:/Users/Admin/AppData/Local/Google/Chrome/User Data"
        if os.path.exists(profile_path):
            print(f"✅ Chrome profile path exists: {profile_path}")
        else:
            print(f"❌ Chrome profile path NOT found: {profile_path}")
            print("💡 Try updating the path in create_chrome_driver()")
        
        raise
    except Exception as e:
        print(f"❌ Unexpected error creating Chrome driver: {e}")
        import traceback
        traceback.print_exc()
        raise


async def wait_for_whatsapp_load(driver, timeout=60):
    """Wait for WhatsApp Web to load properly"""
    try:
        print("⏳ Waiting for WhatsApp Web to load...")
        # Wait for either the QR code or the chat interface
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]') or
                     d.find_elements(By.XPATH, '//canvas[@aria-label="Scan me!"]')
        )
        
        # Check if QR code is present (not logged in)
        qr_code = driver.find_elements(By.XPATH, '//canvas[@aria-label="Scan me!"]')
        if qr_code:
            print("📱 QR Code detected. Please scan with your phone to login to WhatsApp Web")
            print("⏳ Waiting for login...")
            # Wait for login completion
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            print("✅ Login successful!")
        else:
            print("✅ Already logged in to WhatsApp Web")
            
    except TimeoutException:
        print("❌ Timeout waiting for WhatsApp Web to load")
        print("💡 Make sure you're connected to the internet and WhatsApp Web is accessible")
        raise


async def open_chat(driver, phone_number, message):
    """Open chat with the specified phone number and send a message"""
    try:
        print(f"📱 Opening chat with: {phone_number}")
        
        # Navigate to WhatsApp with phone number
        encoded_message = message.replace('\n', '%0A').replace(' ', '%20')
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}"
        driver.get(url)
        
        # Wait for WhatsApp to load
        await wait_for_whatsapp_load(driver)
        
        # Wait for chat to open
        print("⏳ Waiting for chat to open...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        print("✅ Chat loaded successfully")
        
    except TimeoutException:
        print("❌ Timeout opening chat")
        raise
    except Exception as e:
        print(f"❌ Error opening chat: {e}")
        raise


async def send_message_to_input(driver, message, delay=1):
    """Send message to WhatsApp input box with proper formatting"""
    try:
        print(f"Sending message: {repr(message)}")
        
        # Find and focus input box
        input_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        input_box.click()
        await asyncio.sleep(0.5)
        
        # Clear existing text
        input_box.clear()
        
        # Send message line by line to preserve formatting
        lines = message.split('\n')
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                input_box.send_keys(line)
            
            # Add line break except for last line
            if i < len(lines) - 1:
                input_box.send_keys(Keys.SHIFT + Keys.ENTER)
                await asyncio.sleep(0.2)
        
        await asyncio.sleep(delay)
        
        # Send the message
        input_box.send_keys(Keys.ENTER)
        print("✅ Message sent successfully")
        
    except TimeoutException:
        print("❌ Timeout finding input box")
        raise
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        raise


async def send_test_message(phone_number, stop_event):
    """Send a simple test message via WhatsApp"""
    message = "🧪 This is a test message from the gas consumption system!"
    driver = None
    
    try:
        print("🚀 Starting WhatsApp test automation...")
        driver = create_chrome_driver()  # ← USE THE HELPER FUNCTION
        
        await open_chat(driver, phone_number, message)
        await send_message_to_input(driver, message)
        
        print("✅ Test message sent successfully!")
        await asyncio.sleep(3)
        
        # Keep browser open until stop event
        print("⏳ Keeping browser open... Press Ctrl+C to close")
        while not stop_event.is_set():
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Error in test message: {e}")
        raise
    finally:
        if driver:
            print("🔒 Closing browser...")
            driver.quit()


async def send_whatsapp_with_greeting(phone_number, message, stop_event):
    """
    Enhanced WhatsApp automation with greeting, menu selection, and message sending
    """
    driver = None
    
    try:
        print("Starting WhatsApp automation with greeting...")
        
        # Determine greeting based on time - using ASCII-safe characters
        current_hour = datetime.now().hour
        greeting = "Bom dia!" if current_hour < 12 else "Boa tarde!"
        
        driver = create_chrome_driver()
        
        # Step 1: Send greeting
        print(f"Sending greeting: {greeting}")
        await open_chat(driver, phone_number, greeting)
        await send_message_to_input(driver, greeting, delay=2)
        
        # Step 2: Wait for menu response (simulate time for menu to appear)
        print("Waiting for menu response...")
        await asyncio.sleep(10)
        
        # Step 3: Send menu option "1"
        print("Selecting menu option: 1")
        await send_message_to_input(driver, "1", delay=2)
        
        # Step 4: Wait before sending main message
        print("Waiting before sending main message...")
        await asyncio.sleep(5)
        
        # Step 5: Send the main gas consumption message
        print("Sending main gas consumption message...")
        await send_message_to_input(driver, message, delay=2)
        
        print("All messages sent successfully!")
        
        # Step 6: Keep browser open for a bit to ensure delivery
        print("Waiting to ensure message delivery...")
        await asyncio.sleep(10)
        
        # Keep browser open for a reasonable time, then close automatically
        print("Keeping browser open for 10 more seconds...")
        await asyncio.sleep(10)
        print("Closing browser automatically...")
            
    except Exception as e:
        print(f"Error in WhatsApp automation: {e}")
        raise
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()


async def send_simple_test_message(phone_number, message):
    """Send a simple test message without greeting sequence"""
    driver = None
    
    try:
        print("Starting simple WhatsApp test...")
        print(f"Target phone: {phone_number}")
        print(f"Message: {message}")
        
        driver = create_chrome_driver()
        print("Chrome driver created successfully")
        
        await open_chat(driver, phone_number, message)
        print("Chat opened successfully")
        
        await send_message_to_input(driver, message)
        print("Message sent to input successfully")
        
        print("Test message sent successfully!")
        
        # Keep browser open for 20 seconds to see the result
        print("Keeping browser open for 20 seconds...")
        for i in range(20, 0, -1):
            print(f"Browser will close in {i} seconds...")
            await asyncio.sleep(1)
        
        print("20 seconds completed, closing browser...")
        
    except Exception as e:
        print(f"Error in simple test: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if driver:
            print("Closing browser...")
            try:
                driver.quit()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")


def run_send_simple_test_message(phone_number, message, stop_event):
    """Sync wrapper for simple test message"""
    try:
        print(f"🔄 Starting subprocess for simple test message to {phone_number}")
        print(f"📝 Message: {message}")
        
        # Run the async function that includes the 20-second wait
        asyncio.run(send_simple_test_message(phone_number, message))
        
        print("✅ Simple test subprocess completed successfully")
        
    except KeyboardInterrupt:
        print("\n🛑 Simple test interrupted by user")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to ensure proper exit code


def run_send_test_message(phone_number, stop_event):
    """Sync wrapper for test message"""
    try:
        asyncio.run(send_test_message(phone_number, stop_event))
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def run_send_whatsapp_with_greeting(phone_number, message, stop_event):
    """Sync wrapper for WhatsApp automation with greeting"""
    try:
        asyncio.run(send_whatsapp_with_greeting(phone_number, message, stop_event))
    except KeyboardInterrupt:
        print("\n🛑 WhatsApp automation interrupted by user")
    except Exception as e:
        print(f"❌ WhatsApp automation failed: {e}")


# For testing the module directly
if __name__ == "__main__":
    from multiprocessing import Event
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python whatsapp_automation.py <phone_number> [test_message]")
        sys.exit(1)
    
    phone = sys.argv[1]
    test_msg = sys.argv[2] if len(sys.argv) > 2 else None
    
    stop_event = Event()
    
    try:
        if test_msg:
            print(f"🧪 Running test with message: {test_msg}")
            run_send_test_message(phone, stop_event)
        else:
            print("🧪 Running greeting automation test")
            test_message = "🏠 Test gas consumption message\n📊 This is a test from the automation system"
            run_send_whatsapp_with_greeting(phone, test_message, stop_event)
    except KeyboardInterrupt:
        print("\n🛑 Automation stopped")
        stop_event.set()