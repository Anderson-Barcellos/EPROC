"""
### 📝 Persistent Autofill Module
Adapted version of the autofill module designed to work with a persistent Selenium instance.
This module processes individual cases without creating or destroying the WebDriver.

### 🖥️ Architecture
Receives an active WebDriver instance and process number, performs all filling operations,
and returns control to the caller without closing the browser.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import os
import time
import json
import traceback
import shutil
from threading import Event
from Models.models import MiniTemplate


# ■■■■■■■■■■■
#  VALIDATION FUNCTIONS
# ■■■■■■■■■■■

def validar_estrutura_json(laudos):
    """
    ### ✅ Validate JSON Structure
    Validates that the JSON has the expected structure for form filling.

    ### 🖥️ Parameters
        - `laudos` (`dict`): JSON data loaded from template file

    ### 🔄 Returns
        - `dict`: Validated JSON data ready for processing

    ### ⚠️ Raises
        - `ValueError`: If required fields are missing

    ### 📚 Notes
    - Checks for all mandatory fields
    - Reports missing fields for debugging
    """
    campos_obrigatorios = [
        "FormacaoTecnicoProfissional",
        "UltimaAtividade",
        "MotivoIncapacidade",
        "HistoricoAnamnese",
        "DocumentosMedicosAnalisados",
        "DCB",
        "DID",
        "DER",
        "DAP",
    ]

    if "json" not in laudos:
        raise ValueError("JSON must contain main 'json' key")

    json_data = laudos["json"]
    campos_faltantes = [
        campo for campo in campos_obrigatorios if campo not in json_data
    ]

    if campos_faltantes:
        print(f"[⚠️]: Missing required fields: {', '.join(campos_faltantes)}")

    return json_data


def validar_limites_campos(json_data):
    """
    ### 📏 Validate Field Limits
    Validates and truncates fields that exceed character/word limits.

    ### 🖥️ Parameters
        - `json_data` (`dict`): JSON data to validate

    ### 🔄 Returns
        - `dict`: JSON data with truncated fields if necessary

    ### 📚 Notes
    - Enforces word limits for specific fields
    - Adds ellipsis to truncated content
    """
    limites = {
        "MotivoIncapacidade": 3,  # words
        "HistoricoAnamnese": 100,  # words
        "CONCLUSAO PERICIAL": 70,  # words
    }

    for campo, limite in limites.items():
        if campo in json_data and json_data[campo]:
            palavras = json_data[campo].split()
            if len(palavras) > limite:
                print(f"[⚠️]: Field {campo} exceeds limit ({len(palavras)} > {limite} words)")
                json_data[campo] = " ".join(palavras[:limite]) + "..."

    return json_data


def markdown_to_text(markdown_content):
    """
    ### 📄 Convert Markdown to Plain Text
    Removes markdown formatting to get plain text for form fields.

    ### 🖥️ Parameters
        - `markdown_content` (`str`): Markdown formatted text

    ### 🔄 Returns
        - `str`: Plain text without markdown formatting

    ### 📚 Notes
    - Removes headers, links, images, bold/italic, code blocks
    - Preserves actual content while removing formatting
    """
    import re

    # Remove markdown headers
    plain_text = re.sub(r'#+ ', '', markdown_content)
    # Remove markdown links
    plain_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', plain_text)
    # Remove markdown images
    plain_text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', plain_text)
    # Remove markdown bold and italic
    plain_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', plain_text)
    plain_text = re.sub(r'\*([^\*]+)\*', r'\1', plain_text)
    plain_text = re.sub(r'__([^_]+)__', r'\1', plain_text)
    plain_text = re.sub(r'_([^_]+)_', r'\1', plain_text)
    # Remove markdown code blocks
    plain_text = re.sub(r'```([^`]+)```', r'\1', plain_text)
    plain_text = re.sub(r'`([^`]+)`', r'\1', plain_text)
    # Remove markdown blockquotes
    plain_text = re.sub(r'> ', '', plain_text)
    # Remove markdown horizontal rules
    plain_text = re.sub(r'---', '', plain_text)
    # Remove markdown lists
    plain_text = re.sub(r'^\s*[-*+] ', '', plain_text, flags=re.MULTILINE)
    plain_text = re.sub(r'^\s*\d+\.\s+', '', plain_text, flags=re.MULTILINE)
    # Remove extra newlines
    plain_text = re.sub(r'\n+', '\n', plain_text)

    return plain_text


# ■■■■■■■■■■■
#  HELPER FUNCTIONS
# ■■■■■■■■■■■

def handle_alert(driver):
    """
    ### 🚨 Handle Browser Alert
    Detects and accepts JavaScript alerts if present.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - `bool`: True if alert was handled, False if no alert

    ### 📚 Notes
    - Non-blocking - returns quickly if no alert
    - Logs alert text before accepting
    """
    try:
        alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert_text = alert.text
        print(f"[🚨]: Alert found: {alert_text}")
        alert.accept()
        return True
    except TimeoutException:
        return False


def pesquisar_processo(driver, numero_processo):
    """
    ### 🔍 Search Process
    Searches for a specific process number in the EPROC system.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance
        - `numero_processo` (`str`): Process number to search

    ### 🔄 Returns
        - None

    ### ⚠️ Raises
        - `TimeoutException`: If search field not found

    ### 📚 Notes
    - Uses quick search field
    - Submits with Enter key
    """
    try:
        campo_pesquisa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida"))
        )
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(numero_processo)
        campo_pesquisa.send_keys(Keys.RETURN)
        print(f"[🔍]: Searching for process: {numero_processo}")
    except TimeoutException:
        raise Exception("Could not find search field")


def clicar_laudo_medico(driver):
    """
    ### 📋 Click Medical Report Link
    Clicks on the 'Laudo Médico de Incapacidade' link to open report form.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 📚 Notes
    - Handles new window opening
    - Switches context to new window
    """
    try:
        original_window = driver.current_window_handle

        link_laudo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[@class='infraButton' and contains(text(), 'Laudo Médico de Incapacidade')]",
                )
            )
        )
        link_laudo.click()
        print("[📋]: Clicked on 'Laudo Médico de Incapacidade' link")

        # Wait for new window
        WebDriverWait(driver, 5).until(EC.new_window_is_opened([original_window]))

        # Switch to new window
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        return True

    except TimeoutException:
        print("[❌]: Could not find 'Laudo Médico de Incapacidade' link")
        return False
    except Exception as e:
        print(f"[❌]: Error clicking medical report link: {e}")
        return False


def selecionar_parte_se_necessario(driver):
    """
    ### 👤 Select Party if Necessary
    Selects the appropriate party from dropdown using JavaScript.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 📚 Notes
    - Uses JavaScript for reliable selection
    - Handles null/empty options automatically
    """
    try:
        print("[👤]: Attempting party selection via JavaScript...")

        javascript_code = """
        var selectElement = document.getElementById('selParte');
        if (selectElement) {
            console.log('selParte element found');
            console.log('Current value:', selectElement.value);

            if (selectElement.value === 'null') {
                console.log('Null value detected, looking for valid option...');

                var opcoesValidas = [];

                for (var i = 0; i < selectElement.options.length; i++) {
                    var option = selectElement.options[i];
                    console.log('Option ' + i + ':', option.value, option.text);

                    if (option.value !== 'null' && option.value.trim() !== '') {
                        opcoesValidas.push({index: i, option: option});
                    }
                }

                if (opcoesValidas.length > 0) {
                    var primeiraOpcao = opcoesValidas[0];
                    console.log('Selecting first valid option:', primeiraOpcao.option.text);
                    selectElement.selectedIndex = primeiraOpcao.index;
                    selectElement.value = primeiraOpcao.option.value;

                    var event = new Event('change', { bubbles: true });
                    selectElement.dispatchEvent(event);

                    return {success: true, selected: primeiraOpcao.option.text, value: primeiraOpcao.option.value};
                } else {
                    return {success: false, error: 'No valid options found'};
                }
            } else {
                return {success: true, selected: selectElement.options[selectElement.selectedIndex].text, value: selectElement.value};
            }
        } else {
            return {success: false, error: 'selParte element not found'};
        }
        """

        resultado = driver.execute_script(javascript_code)

        if resultado['success']:
            print(f"[✅]: JavaScript selection successful: '{resultado['selected']}'")
            return True
        else:
            print(f"[❌]: JavaScript selection failed: {resultado['error']}")
            return False

    except Exception as e:
        print(f"[❌]: Error in JavaScript selection: {e}")
        return False


def clicar_botao_novo(driver):
    """
    ### ➕ Click New Button
    Clicks the 'Novo' button to create a new medical report.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 📚 Notes
    - Uses JavaScript for reliable clicking
    - Verifies success through multiple indicators
    """
    try:
        print("[➕]: Initiating click on 'Novo' button")

        current_url = driver.current_url
        initial_windows = set(driver.window_handles)

        botao_novo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sbmNovo"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_novo)
        time.sleep(1)

        driver.execute_script("arguments[0].click();", botao_novo)
        time.sleep(3)

        # Check for success indicators
        new_url = driver.current_url
        current_windows = set(driver.window_handles)

        if new_url != current_url or len(current_windows) > len(initial_windows):
            print("[✅]: 'Novo' button clicked successfully")
            return True

        # Check for form elements
        form_elements = ["txtDataPericia", "txtFormacaoTecnicoProfissional"]
        for element_id in form_elements:
            try:
                driver.find_element(By.ID, element_id)
                print(f"[✅]: Form element found: {element_id}")
                return True
            except NoSuchElementException:
                continue

        print("[❌]: Could not verify 'Novo' button action")
        return False

    except TimeoutException:
        print("[❌]: Timeout: Could not find 'Novo' button")
        return False
    except Exception as e:
        print(f"[❌]: Error clicking 'Novo' button: {e}")
        return False


def switch_to_frame_containing_element(driver, by, value):
    """
    ### 🖼️ Switch to Frame Containing Element
    Searches through iframes to find and switch to one containing specific element.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance
        - `by` (`By`): Selenium locator strategy
        - `value` (`str`): Locator value

    ### 🔄 Returns
        - `bool`: True if found and switched, False otherwise

    ### 📚 Notes
    - Searches all iframes on page
    - Returns to default content if not found
    """
    try:
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")

        for frame in frames:
            driver.switch_to.frame(frame)
            try:
                driver.find_element(by, value)
                print(f"[🖼️]: Element found in iframe")
                return True
            except NoSuchElementException:
                driver.switch_to.parent_frame()

        print("[⚠️]: Element not found in any iframe")
        driver.switch_to.default_content()
        return False

    except Exception as e:
        print(f"[❌]: Error switching frames: {e}")
        return False


def press_ctrl_shift_l(driver):
    """
    ### ⌨️ Press Ctrl+Shift+L
    Simulates keyboard shortcut Ctrl+Shift+L.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - None

    ### 📚 Notes
    - Used to trigger specific form actions
    - Cross-platform compatible
    """
    try:
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL)
        actions.key_down(Keys.SHIFT)
        actions.send_keys('l')
        actions.key_up(Keys.SHIFT)
        actions.key_up(Keys.CONTROL)
        actions.perform()
        print("[⌨️]: Ctrl+Shift+L pressed successfully")
    except Exception as e:
        print(f"[❌]: Error pressing Ctrl+Shift+L: {e}")


def preencher_formulario(driver, laudo_data):
    """
    ### 📝 Fill Form
    Fills the medical report form with data from JSON template.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance
        - `laudo_data` (`str`): Path to JSON template file

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 📚 Notes
    - Validates JSON structure before filling
    - Handles field visibility and scrolling
    - Reports detailed success/failure statistics
    """
    print("\n[📝]: Starting form filling process")

    campos_preenchidos = 0
    campos_nao_preenchidos = []

    # ■■■■■■■■■■■
    #  FIELD MAPPING
    # ■■■■■■■■■■■
    id_mapping = {
        "FormacaoTecnicoProfissional": "txtFormacaoTecnicoProfissional",
        "UltimaAtividade": "txtUltimaAtividade",
        "TarefasExigidasUltimaAtividade": "txtTarefasExigidasUltimaAtividade",
        "QuantoTempoUltimaAtividade": "txtQuantoTempoUltimaAtividade",
        "AteQuandoUltimaAtividade": "txtAteQuandoUltimaAtividade",
        "ExperienciasLaboraisAnt": "txtExperienciasLaboraisAnt",
        "MotivoIncapacidade": "txtMotivoIncapacidade",
        "HistoricoAnamnese": "txaHistoricoAnamnese",
        "DocumentosMedicosAnalisados": "txaDocumentosMedicosAnalisados",
        "ExameFisicoMental": "txaExameFisicoMental",
        "CONCLUSAO PERICIAL": "txaConclusaoPericial",
        "DCB": "txtDadoComplementarPericia011_D010_S",
        "DID": "txtDID",
        "DER": "txtDER",
        "DAP": "txtDAP",
        "CausaProvavelDiagnostico": "txaCausaProvavelDiagnostico",
        "CIF": "txaCIF",
        "QuesitoDoJuizoRespostas": "txaQuesitoDoJuizoRespostas",
    }

    try:
        # Press shortcut
        press_ctrl_shift_l(driver)

        # Load and validate JSON
        with open(laudo_data, "r", encoding='utf-8') as file:
            laudos = json.loads(file.read())

        json_data = validar_estrutura_json(laudos)
        json_data = validar_limites_campos(json_data)

        # Scroll to top
        driver.execute_script("window.scrollTo(0, 0);")

        # ■■■■■■■■■■■
        #  FILL FIELDS
        # ■■■■■■■■■■■
        for json_key, valor in json_data.items():
            try:
                html_id = id_mapping.get(json_key)

                if not html_id:
                    print(f"[⚠️]: No mapping for field: {json_key}")
                    campos_nao_preenchidos.append(json_key)
                    continue

                valor = markdown_to_text(str(valor))

                elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, html_id))
                )

                # Scroll to element
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    elemento,
                )
                time.sleep(0.5)

                # Fill field
                driver.execute_script("arguments[0].value = '';", elemento)
                driver.execute_script("arguments[0].value = arguments[1];", elemento, valor)

                # Trigger events
                driver.execute_script("""
                    var elemento = arguments[0];
                    elemento.dispatchEvent(new Event('input', { bubbles: true }));
                    elemento.dispatchEvent(new Event('change', { bubbles: true }));
                    elemento.dispatchEvent(new Event('blur', { bubbles: true }));
                """, elemento)

                campos_preenchidos += 1

            except TimeoutException:
                print(f"[⏱️]: Timeout on field {html_id}")
                campos_nao_preenchidos.append(json_key)
            except Exception as e:
                print(f"[❌]: Error filling {json_key}: {e}")
                campos_nao_preenchidos.append(json_key)

        # ■■■■■■■■■■■
        #  REPORT
        # ■■■■■■■■■■■
        print(f"\n[📊]: Form Filling Report")
        print(f"  ✅ Fields filled: {campos_preenchidos}")
        print(f"  ❌ Fields failed: {len(campos_nao_preenchidos)}")

        if campos_nao_preenchidos:
            print(f"  Failed fields: {', '.join(campos_nao_preenchidos)}")

        return campos_preenchidos > 0

    except Exception as e:
        print(f"[❌]: Critical error filling form: {e}")
        return False
    finally:
        driver.switch_to.default_content()


def clicar_salvar(driver):
    """
    ### 💾 Click Save Button
    Saves the filled medical report form.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 📚 Notes
    - Uses JavaScript for reliable clicking
    - Handles post-save alerts automatically
    """
    try:
        botao_salvar = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "sbmAlterar"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_salvar)
        time.sleep(1)

        driver.execute_script("arguments[0].click();", botao_salvar)
        print("[💾]: Save button clicked")

        # Handle alerts
        for _ in range(2):
            if handle_alert(driver):
                print("[✅]: Alert accepted")

        time.sleep(5)
        return True

    except TimeoutException:
        print("[❌]: Could not find save button")
        return False
    except Exception as e:
        print(f"[❌]: Error saving form: {e}")
        return False


# ■■■■■■■■■■■
#  MAIN PROCESSING FUNCTION
# ■■■■■■■■■■■

def process_single_case(driver, numero_processo: str) -> bool:
    """
    ### 🔄 Process Single Case
    Main function to process a single case using existing WebDriver instance.

    ### 🖥️ Parameters
        - `driver` (`webdriver`): Active WebDriver instance already logged in
        - `numero_processo` (`str`): Process number to fill

    ### 🔄 Returns
        - `bool`: True if successful, False otherwise

    ### 💡 Example

    >>> from selenium_manager import selenium_manager
    >>> driver = selenium_manager.get_driver()
    >>> success = process_single_case(driver, "50008601220254047106")
    >>> print(f"Process {'completed' if success else 'failed'}")

    ### 📚 Notes
    - Does not create or destroy WebDriver
    - Generates template using AI model
    - Handles all form filling steps
    - Moves files based on success/failure
    """
    try:
        print(f"\n[🔄]: Processing case: {numero_processo}")

        report_path = f"Reports/{numero_processo}_final_report.md"

        # ■■■■■■■■■■■
        #  TEMPLATE GENERATION
        # ■■■■■■■■■■■
        print("[🤖]: Generating template with AI model...")
        template_event = Event()
        MiniTemplate("gpt-4.1", report_path, template_event)

        # ■■■■■■■■■■■
        #  SEARCH PROCESS
        # ■■■■■■■■■■■
        pesquisar_processo(driver, numero_processo)
        time.sleep(3)

        # ■■■■■■■■■■■
        #  OPEN MEDICAL REPORT
        # ■■■■■■■■■■■
        if not clicar_laudo_medico(driver):
            print("[❌]: Failed to open medical report")
            return False
        time.sleep(2)

        # ■■■■■■■■■■■
        #  SELECT PARTY
        # ■■■■■■■■■■■
        if not switch_to_frame_containing_element(driver, By.ID, "selParte"):
            if selecionar_parte_se_necessario(driver):
                print("[✅]: Party selected successfully")
            else:
                print("[❌]: Could not select party")

        # ■■■■■■■■■■■
        #  CREATE NEW REPORT
        # ■■■■■■■■■■■
        if not clicar_botao_novo(driver):
            print("[❌]: Failed to create new report")
            return False
        time.sleep(5)

        # ■■■■■■■■■■■
        #  WAIT FOR TEMPLATE
        # ■■■■■■■■■■■
        print("[⏳]: Waiting for AI template generation...")
        template_event.wait(timeout=30.0)

        if not template_event.is_set():
            print("[❌]: Template generation timeout")
            # Move to Pending
            pending_dir = os.path.join("Reports", "Pending")
            os.makedirs(pending_dir, exist_ok=True)
            if os.path.exists(report_path):
                shutil.move(report_path, os.path.join(pending_dir, f"{numero_processo}_final_report.md"))
            return False

        # ■■■■■■■■■■■
        #  FILL FORM
        # ■■■■■■■■■■■
        template_event.clear()
        if not preencher_formulario(driver, "laudo_template.json"):
            print("[❌]: Form filling failed")
            return False

        # ■■■■■■■■■■■
        #  SAVE FORM
        # ■■■■■■■■■■■
        print("[💾]: Saving form...")
        if not clicar_salvar(driver):
            print("[❌]: Failed to save form")
            return False

        print(f"[✅]: Case {numero_processo} processed successfully")
        return True

    except Exception as e:
        print(f"[❌]: Critical error processing case {numero_processo}: {e}")
        print(f"Stack trace: {traceback.format_exc()}")

        # Move to Pending on error
        pending_dir = os.path.join("Reports", "Pending")
        os.makedirs(pending_dir, exist_ok=True)
        report_path = f"Reports/{numero_processo}_final_report.md"
        if os.path.exists(report_path):
            shutil.move(report_path, os.path.join(pending_dir, f"{numero_processo}_final_report.md"))

        return False
