"""
### 🌐 Selenium Instance Manager
A singleton-pattern manager for maintaining a persistent Selenium WebDriver instance across multiple process executions.
This module ensures efficient resource utilization by reusing a single browser instance.

### 🖥️ Architecture
The manager handles driver lifecycle, ensuring proper initialization, reuse, and cleanup of browser instances.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import time
from typing import Optional


class SeleniumManager:
    """
    ### 🌐 SeleniumManager
    Manages a singleton Selenium WebDriver instance for efficient browser automation.
    Ensures only one browser instance is created and reused across multiple operations.

    ### 🖥️ Parameters
        - None required for initialization

    ### 🔄 Returns
        - `SeleniumManager`: Singleton instance of the manager

    ### 💡 Example

    >>> manager = SeleniumManager()
    >>> driver = manager.get_driver()
    >>> # Use driver for automation
    >>> manager.reset_driver()  # Reset for next process
    >>> manager.quit_driver()   # Clean shutdown

    ### 📚 Notes
    - Implements singleton pattern to ensure only one instance exists
    - Automatically configures Chrome with required options
    - Handles driver lifecycle management and error recovery
    """

    _instance = None
    _driver = None
    _is_logged_in = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SeleniumManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.base_url = "https://eproc.jfrs.jus.br/eprocV2/"
            self.usuario = "crmrs035013"
            self.senha = "*Andi009134"

    def _setup_chrome_options(self) -> Options:
        """
        ### ⚙️ Chrome Options Setup
        Configures Chrome options for optimal automation performance.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `Options`: Configured Chrome options object

        ### 📚 Notes
        - Uses existing Chrome user profile for session persistence
        - Disables download prompts and configures default directory
        - Sets PDF handling to external mode for automatic downloads
        """
        user_home = os.path.expanduser("~")
        chrome_profile = os.path.join(
            user_home, "AppData", "Local", "Google", "Chrome", "Default"
        )

        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={chrome_profile}")

        # ■■■■■■■■■■■
        #  CHROME PREFERENCES
        # ■■■■■■■■■■■
        chrome_options.add_experimental_option(
            "prefs", {
                "download.prompt_for_download": False,
                "download.directory_upgrade": False,
                "plugins.always_open_pdf_externally": True,
                "download.default_directory": os.path.join(os.getcwd(), "Processos")
            }
        )

        # Additional stability options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        return chrome_options

    def get_driver(self) -> webdriver.Chrome:
        """
        ### 🚀 Get WebDriver Instance
        Returns the singleton WebDriver instance, creating it if necessary.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `webdriver.Chrome`: Active Chrome WebDriver instance

        ### ⚠️ Raises
            - `WebDriverException`: If driver creation fails

        ### 💡 Example

        >>> manager = SeleniumManager()
        >>> driver = manager.get_driver()
        >>> driver.get("https://example.com")

        ### 📚 Notes
        - Creates driver only on first call
        - Subsequent calls return existing instance
        - Validates driver health before returning
        """
        if self._driver is None:
            print("[🚀]: Initializing new Chrome driver instance")
            try:
                chrome_options = self._setup_chrome_options()
                self._driver = webdriver.Chrome(options=chrome_options)
                self._driver.maximize_window()
                print("[✅]: Chrome driver initialized successfully")
            except WebDriverException as e:
                print(f"[❌]: Failed to initialize Chrome driver: {e}")
                raise
        else:
            # Validate existing driver is still functional
            try:
                _ = self._driver.current_url
                print("[♻️]: Reusing existing Chrome driver instance")
            except:
                print("[⚠️]: Driver instance is stale, recreating...")
                self._driver = None
                return self.get_driver()

        return self._driver

    def ensure_login(self) -> bool:
        """
        ### 🔐 Ensure Login
        Ensures the driver is logged into the EPROC system.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `bool`: True if login successful, False otherwise

        ### 💡 Example

        >>> if manager.ensure_login():
        >>>     print("Ready to process")

        ### 📚 Notes
        - Checks if already logged in before attempting login
        - Handles automatic login with stored credentials
        - Falls back to manual login if automatic fails
        """
        if self._is_logged_in:
            # Verify still logged in
            try:
                self._driver.find_element(By.ID, "txtNumProcessoPesquisaRapida")
                print("[✅]: Already logged in")
                return True
            except:
                print("[⚠️]: Session expired, logging in again")
                self._is_logged_in = False

        driver = self.get_driver()

        # ■■■■■■■■■■■
        #  LOGIN PROCESS
        # ■■■■■■■■■■■
        print("[🔐]: Starting login process")

        # Navigate to EPROC if not already there
        if self.base_url not in driver.current_url:
            driver.get(self.base_url)
            time.sleep(3)

        # Check if already logged in
        if "painel_perito_listar" in driver.current_url:
            self._is_logged_in = True
            print("[✅]: Already logged in (detected from URL)")
            return True

        try:
            # Try automatic login
            wait = WebDriverWait(driver, 10)

            # Try iframe first
            try:
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ssoFrame")))
            except TimeoutException:
                pass

            # Look for login fields
            formularios = [
                {"user": (By.ID, "txtUsuario"), "pwd": (By.ID, "pwdSenha"), "btn": (By.ID, "sbmEntrar")},
                {"user": (By.ID, "username"), "pwd": (By.ID, "password"), "btn": (By.ID, "kc-login")},
            ]

            for form in formularios:
                try:
                    campo_usuario = wait.until(EC.presence_of_element_located(form["user"]))
                    campo_senha = driver.find_element(*form["pwd"])
                    botao_login = driver.find_element(*form["btn"])

                    campo_usuario.clear()
                    campo_usuario.send_keys(self.usuario)
                    campo_senha.clear()
                    campo_senha.send_keys(self.senha)
                    botao_login.click()

                    print("[🔄]: Login credentials submitted")
                    break
                except TimeoutException:
                    continue

            # Return to main content
            driver.switch_to.default_content()

            # Wait for login to complete
            time.sleep(5)

            # Verify login success
            try:
                wait.until(EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida")))
                self._is_logged_in = True
                print("[✅]: Login successful")
                return True
            except TimeoutException:
                print("[❌]: Automatic login failed")
                print("Please login manually...")
                input("Press Enter after manual login...")
                self._is_logged_in = True
                return True

        except Exception as e:
            print(f"[❌]: Login error: {e}")
            return False

    def reset_driver(self) -> None:
        """
        ### 🔄 Reset Driver State
        Resets the driver to a clean state for processing the next item.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - None

        ### 💡 Example

        >>> manager.reset_driver()
        >>> # Driver is now ready for next process

        ### 📚 Notes
        - Closes extra windows/tabs
        - Returns to main EPROC page
        - Clears any alerts or modals
        """
        if self._driver is None:
            return

        print("[🔄]: Resetting driver state")

        try:
            # Close all windows except the first one
            if len(self._driver.window_handles) > 1:
                original_window = self._driver.window_handles[0]
                for handle in self._driver.window_handles[1:]:
                    self._driver.switch_to.window(handle)
                    self._driver.close()
                self._driver.switch_to.window(original_window)

            # Return to default content
            self._driver.switch_to.default_content()

            # Handle any pending alerts
            try:
                alert = self._driver.switch_to.alert
                alert.accept()
            except:
                pass

            # Navigate back to main page if logged in
            if self._is_logged_in:
                self._driver.get(self.base_url + "controlador.php?acao=painel_perito_listar")
                time.sleep(2)

            print("[✅]: Driver state reset complete")

        except Exception as e:
            print(f"[❌]: Error resetting driver: {e}")

    def quit_driver(self) -> None:
        """
        ### 🛑 Quit Driver
        Safely shuts down the WebDriver instance and cleans up resources.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - None

        ### 💡 Example

        >>> manager.quit_driver()
        >>> # Browser closed and resources freed

        ### 📚 Notes
        - Ensures proper cleanup of browser process
        - Resets login state
        - Safe to call multiple times
        """
        if self._driver:
            print("[🛑]: Shutting down Chrome driver")
            try:
                self._driver.quit()
                print("[✅]: Chrome driver closed successfully")
            except Exception as e:
                print(f"[❌]: Error closing driver: {e}")
            finally:
                self._driver = None
                self._is_logged_in = False

    def is_driver_active(self) -> bool:
        """
        ### ❓ Check Driver Status
        Checks if the driver is active and responsive.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `bool`: True if driver is active, False otherwise

        ### 💡 Example

        >>> if manager.is_driver_active():
        >>>     print("Driver is ready")

        ### 📚 Notes
        - Performs health check on driver instance
        - Does not create driver if it doesn't exist
        """
        if self._driver is None:
            return False

        try:
            _ = self._driver.current_url
            return True
        except:
            return False


# ■■■■■■■■■■■
#  SINGLETON INSTANCE
# ■■■■■■■■■■■
selenium_manager = SeleniumManager()
