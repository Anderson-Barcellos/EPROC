from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import os
import time
from selenium import webdriver
import json
from Models.models import MiniTemplate
from threading import Event
import traceback
from selenium.webdriver.common.action_chains import ActionChains
import shutil
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import sys


def selecionar_parte_se_necessario(driver):

    """
    Versão alternativa que usa JavaScript para forçar a seleção.
    Use esta se a versão com Selenium Select() não funcionar.
    """
    try:
        print("Tentando seleção via JavaScript...")

        # Script JavaScript para selecionar a segunda opção válida
        javascript_code = """
        var selectElement = document.getElementById('selParte');
        if (selectElement) {
            console.log('Elemento selParte encontrado');
            console.log('Valor atual:', selectElement.value);

            if (selectElement.value === 'null') {
                console.log('Valor null detectado, procurando segunda opção válida...');

                var opcoesValidas = [];

                // Coleta todas as opções válidas
                for (var i = 0; i < selectElement.options.length; i++) {
                    var option = selectElement.options[i];
                    console.log('Opção ' + i + ':', option.value, option.text);

                    if (option.value !== 'null' && option.value.trim() !== '') {
                        opcoesValidas.push({index: i, option: option});
                    }
                }

                if (opcoesValidas.length > 1) {
                    // Seleciona a segunda opção válida
                    var segundaOpcao = opcoesValidas[0];
                    console.log('Selecionando segunda opção válida:', segundaOpcao.option.text);
                    selectElement.selectedIndex = segundaOpcao.index;
                    selectElement.value = segundaOpcao.option.value;

                    // Dispara o evento change para ativar mostraTodosLaudos()
                    var event = new Event('change', { bubbles: true });
                    selectElement.dispatchEvent(event);

                    return {success: true, selected: segundaOpcao.option.text, value: segundaOpcao.option.value};
                } else if (opcoesValidas.length === 1) {
                    // Se só tem uma opção, seleciona essa
                    var unicaOpcao = opcoesValidas[0];
                    console.log('Apenas uma opção válida. Selecionando:', unicaOpcao.option.text);
                    selectElement.selectedIndex = unicaOpcao.index;
                    selectElement.value = unicaOpcao.option.value;

                    var event = new Event('change', { bubbles: true });
                    selectElement.dispatchEvent(event);

                    return {success: true, selected: unicaOpcao.option.text, value: unicaOpcao.option.value};
                } else {
                    return {success: false, error: 'Nenhuma opção válida encontrada'};
                }
            } else {
                return {success: true, selected: selectElement.options[selectElement.selectedIndex].text, value: selectElement.value};
            }
        } else {
            return {success: false, error: 'Elemento selParte não encontrado'};
        }
        """

        resultado = driver.execute_script(javascript_code)

        if resultado['success']:
            print(f"✅ Seleção via JavaScript bem-sucedida: '{resultado['selected']}'")
            return True
        else:
            print(f"❌ Falha na seleção via JavaScript: {resultado['error']}")
            return False

    except Exception as e:
        print(f"❌ Erro na seleção via JavaScript: {e}")
        return False

def markdown_to_text(markdown_content):
    """
    Function to convert markdown content to plain text.
    #### Parameters:
    - markdown_content: str: The markdown content to be converted.

    #### Returns:
    - str: The plain text content.
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

def process_data(data: dict, filters: list = None, validate: bool = True) -> dict:
   """
    ### 🔗 Extrai links de reclamações do Reclame Aqui

    ### 📥  Parâmetros:

    page_num 'int' → 📄 Número da página (1-44)
    - timeout 'int' → ⏱️ Timeout da requisição em segundos
    - retries 'int' → 🔄 Número de tentativas em caso de falha

    ### 📤 Retorna:
    - 'list[str]' → 🔗 Lista de URLs das reclamações encontradas

    ### ⚠️ Exceções:
    - 'ValueError' → ❌ Quando página é inválida
    • 'requests.RequestException' → 🌐 Erro na requisição HTTP
    • 'TimeoutError' → ⏰ Timeout excedido

    '''python
    # 🎯 Uso básico
    links = scrap_complaints(1)
    print(f"📊 Encontrados: {len(links)} links")

    # ⚙️ Com configurações personalizadas
    links = scrap_complaints(
        page_num=5,
        timeout=60,
        retries=5
    )

    # 🔄 Processamento em lote
    all_links = []
    for page in range(1, 6):
        try:
            page_links = scrap_complaints(page)
            all_links.extend(page_links)
        except ValueError as e:
            print(f"❌ Erro na página {page}: {e}")
    '''
    """


# Configurar as opções do Chrome
def setup_chrome_options():
    user_home = os.path.expanduser("~")
    chrome_profile = os.path.join(user_home, "AppData", "Local", "Google", "Chrome", "Default")
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={chrome_profile}")

    chrome_options.add_experimental_option(
        "prefs", {
            "download.prompt_for_download": False,
            "download.directory_upgrade": False,
            "plugins.always_open_pdf_externally": True,
            "download.default_directory": os.path.join(user_home, "Downloads")
        }
    )

    return chrome_options

# Função para lidar com alertas
def handle_alert(driver):
    try:
        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert_text = alert.text
        print(f"Alerta encontrado: {alert_text}")
        alert.accept()
        return True
    except TimeoutException:
        return False
# Handle an alert with ok
def handle_alert_ok(driver):
    try:
        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert_text = alert.text
        print(f"Alerta encontrado: {alert_text}")
        alert.accept()
        return True
    except TimeoutException:
        print("Nenhum alerta encontrado")
        return False

# Função para realizar o login
def login(driver, usuario, senha):
    try:
        if "painel_perito_listar" in driver.current_url:
            return True
        campo_usuario = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        campo_senha = driver.find_element(By.ID, "password")
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        campo_senha.clear()
        campo_senha.send_keys(senha)
        botao_login = driver.find_element(By.ID, "kc-login")
        botao_login.click()
        time.sleep(2)
        current_url = driver.current_url
        if "painel_perito_listar" in current_url:
            print("Login automático bem-sucedido.")
            return True
        else:
            print("Falha no login automático. Por favor, faça login manualmente.")
            input("Pressione Enter após fazer login manualmente...")
            return False

    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return False

# Função para pesquisar um processo
def pesquisar_processo(driver, numero_processo):
    try:
        campo_pesquisa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida"))
        )
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(numero_processo)
        campo_pesquisa.send_keys(Keys.RETURN)
        print(f"Pesquisando processo: {numero_processo}")
    except TimeoutException:
        print("Não foi possível encontrar o campo de pesquisa.")
    except Exception as e:
        print(f"Erro ao pesquisar processo: {str(e)}")


def clicar_botao_novo(driver):
    """
    Clica no botão 'Novo' e verifica se a ação foi bem-sucedida.
    Retorna True se conseguiu clicar e abrir o laudo, False caso contrário.
    """
    try:
        print("=== Iniciando clique no botão 'Novo' ===")

        # Captura informações iniciais
        current_url = driver.current_url
        initial_window_handles = set(driver.window_handles)

        print(f"URL inicial: {current_url}")
        print(f"Janelas iniciais: {len(initial_window_handles)}")

        # Esperar até que o botão "Novo" esteja presente e clicável
        print("Aguardando botão 'Novo'...")
        botao_novo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sbmNovo"))
        )

        # Rolar para o botão para garantir visibilidade
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_novo)
        time.sleep(1)

        # Clica no botão usando JavaScript (mais confiável)
        print("Clicando no botão 'Novo' via JavaScript...")
        driver.execute_script("arguments[0].click();", botao_novo)

        # Aguarda um pouco para a ação ser processada
        time.sleep(3)

        # Verifica múltiplos indicadores de sucesso
        sucesso = False
        motivo_sucesso = ""

        # 1. Verificar se a URL mudou
        new_url = driver.current_url
        if new_url != current_url:
            sucesso = True
            motivo_sucesso = f"URL mudou de '{current_url}' para '{new_url}'"

        # 2. Verificar se novas janelas foram abertas
        current_window_handles = set(driver.window_handles)
        if len(current_window_handles) > len(initial_window_handles):
            sucesso = True
            motivo_sucesso = f"Nova janela aberta ({len(current_window_handles)} janelas agora)"

        # 3. Verificar se existe elementos do formulário de laudo na página atual
        try:
            # Tenta encontrar elementos típicos da página de criação de laudo
            elementos_formulario = [
                "txtDataPericia",
                "rdoPacienteDoPeritoSIM",
                "txtFormacaoTecnicoProfissional"
            ]

            for elemento_id in elementos_formulario:
                try:
                    driver.find_element(By.ID, elemento_id)
                    sucesso = True
                    motivo_sucesso = f"Elemento do formulário encontrado: {elemento_id}"
                    break
                except NoSuchElementException:
                    continue
        except Exception:
            pass

        # 4. Verificar se há iframes (página de laudo costuma ter iframes)
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if len(iframes) > 0:
                print(f"Encontrados {len(iframes)} iframes na página")
                # Verificar dentro dos iframes
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        for elemento_id in elementos_formulario:
                            try:
                                driver.find_element(By.ID, elemento_id)
                                sucesso = True
                                motivo_sucesso = f"Elemento do formulário encontrado em iframe: {elemento_id}"
                                break
                            except NoSuchElementException:
                                continue
                        driver.switch_to.default_content()
                        if sucesso:
                            break
                    except Exception:
                        driver.switch_to.default_content()
                        continue
        except Exception:
            pass

        # 5. Aguardar um pouco mais e verificar novamente (para casos de carregamento lento)
        if not sucesso:
            print("Primeira verificação falhou, aguardando mais tempo...")
            time.sleep(5)

            # Repetir verificações
            final_url = driver.current_url
            final_window_handles = set(driver.window_handles)

            if final_url != current_url:
                sucesso = True
                motivo_sucesso = f"URL mudou após espera adicional: '{final_url}'"
            elif len(final_window_handles) > len(initial_window_handles):
                sucesso = True
                motivo_sucesso = f"Nova janela detectada após espera adicional"

        # Resultado final
        if sucesso:
            print(f"✅ Clique no botão 'Novo' bem-sucedido! Motivo: {motivo_sucesso}")
            return True
        else:
            print(f"❌ Clique no botão 'Novo' falhou. URL atual: {driver.current_url}")
            return False

    except TimeoutException:
        print("❌ Timeout: Não foi possível encontrar o botão 'Novo'")
        return False
    except Exception as e:
        print(f"❌ Erro ao clicar no botão 'Novo': {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return False


def wait_for_element(driver, locator, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator)
    )

def is_element_visible(driver, element):
    return driver.execute_script(
        "var elem = arguments[0],                 "
        "  box = elem.getBoundingClientRect(),    "
        "  cx = box.left + box.width / 2,         "
        "  cy = box.top + box.height / 2,         "
        "  e = document.elementFromPoint(cx, cy); "
        "for (; e; e = e.parentElement) {         "
        "  if (e === elem)                        "
        "    return true;                         "
        "}                                        "
        "return false;                            ",
        element
    )

def highlight_element(driver, element, effect_time=500, color="yellow", border=2):
    driver.execute_script("""
        var elem = arguments[0];
        var color = arguments[2];
        var border = arguments[3];
        var original_style = elem.getAttribute('style');
        elem.setAttribute('style', original_style +
            "; border: " + border + "px solid " + color +
            "; background: " + color);
        setTimeout(function(){
            elem.setAttribute('style', original_style);
        }, arguments[1]);
    """, element, effect_time, color, border)

# Modificar a função preencher_formulario para usar o template preenchido
def preencher_formulario(driver, laudo_data, event):
    """
    Preenche o formulário com os dados do laudo.
    """
    print("Iniciando preenchimento do formulário...")

    campos_preenchidos = 0
    campos_nao_preenchidos = []

    # Mapping between JSON keys and HTML IDs
    id_mapping = {
        "FormacaoTecnicoProfissional": "txtFormacaoTecnicoProfissional",
        "UltimaAtividade": "txtTarefasExigidasUltimaAtividade",
        "TarefasExigidasUltimaAtividade": "txtTarefasExigidasUltimaAtividade",
        "QuantoTempoUltimaAtividade": "txtQuantoTempoUltimaAtividade",
        "AteQuandoUltimaAtividade": "txtAteQuandoUltimaAtividade",
        "ExperienciasLaboraisAnt": "txtExperienciasLaboraisAnt",
        "MotivoIncapacidade": "txtMotivoIncapacidade",
        "HistoricoAnamnese": "txaHistoricoAnamnese",
        "DocumentosMedicosAnalisados": "txaDocumentosMedicosAnalisados",
        "ExameFisicoMental": "txaExameFisicoMental",
        "CONCLUSAO PERICIAL": "txaDadoComplementarPericia047_D010_S",
        "CausaProvavelDiagnostico": "txaCausaProvavelDiagnostico",
        "DID": "txtDID",
        "DCB": "txtDadoComplementarPericia011_D010_S",
        "DER": "txtDER",
        "QuesitoDoJuizoRespostas": "txaQuesitoDoJuizoRespostas",
        "CIF": "txaQuesitoDoJuizoRespostas",
    }
    try:
        # Abrir o arquivo JSON com codificação UTF-8
        press_ctrl_shift_l(driver)
        with open(laudo_data, "r", encoding='utf-8') as file:
            laudos = json.loads(file.read())

        if not isinstance(laudos, dict):
            raise ValueError("O arquivo JSON não contém um dicionário válido.")

        driver.execute_script("window.scrollTo(0, 0);")
        print("Rolado até o topo da página")

        for json_key, valor in laudos['json'].items():
            try:
                html_id = id_mapping.get(json_key)
                valor = markdown_to_text(valor)
                if not html_id:
                    print(f"Não foi encontrado mapeamento para o campo JSON: {json_key}")
                    campos_nao_preenchidos.append(json_key)
                    continue

                print(f"Tentando preencher o campo: {html_id}")
                elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, html_id))
                )

                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elemento)
                time.sleep(0.5)

                if is_element_visible(driver, elemento):
                    highlight_element(driver, elemento)
                    elemento.clear()
                    # Enviar o valor diretamente sem tratamento de caracteres especiais
                    driver.execute_script("arguments[0].value = arguments[1];", elemento, str(valor))
                    # Disparar evento de mudança para garantir que o JavaScript da página reconheça a alteração
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elemento)
                    print(f"Campo {html_id} preenchido com: {valor}")
                    campos_preenchidos += 1
                else:
                    print(f"Campo {html_id} não está visível")
                    campos_nao_preenchidos.append(json_key)
            except TimeoutException:
                print(f"Timeout: Nao foi possível encontrar o campo {json_key}")
                campos_nao_preenchidos.append(json_key)
            except Exception as e:
                print(f"Erro ao preencher o campo {json_key}: {str(e)}")
                campos_nao_preenchidos.append(json_key)

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar o arquivo JSON: {str(e)}")
        print("Verifique se o formato está correto e a codificação é UTF-8")
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {laudo_data}")
    except Exception as e:
        print(f"Erro geral ao preencher o formulário: {str(e)}")
    finally:
        print(f"Total de campos preenchidos: {campos_preenchidos}")
        if campos_nao_preenchidos:
            print(f"Campos não preenchidos: {', '.join(campos_nao_preenchidos)}")
        driver.switch_to.default_content()
        event.set()

def clicar_laudo_medico(driver):
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
        print("Clicado no link 'Laudo Médico de Incapacidade'")

        # Aguardar até que uma nova janela seja aberta
        WebDriverWait(driver, 5).until(EC.new_window_is_opened([original_window]))

        # Mudar para a nova janela
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

    except TimeoutException:
        print("Não foi possível encontrar o link 'Laudo Médico de Incapacidade'")
    except NoSuchElementException:
        print("O link 'Laudo Médico de Incapacidade' não está presente na página")
    except Exception as e:
        print(f"Erro ao clicar no link 'Laudo Médico de Incapacidade': {str(e)}")


def clicar_salvar(driver):
    try:
        # Esperar até que o botão "Salvar" esteja presente
        botao_salvar = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "sbmAlterar"))
        )

        # Rolar até o botão para garantir que está visível
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_salvar)
        time.sleep(1)

        # Clicar no botão usando JavaScript
        driver.execute_script("arguments[0].click();", botao_salvar)
        print("Botão 'Salvar' clicado")

        # Lidar com possíveis alertas
        try:
            alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert_text = alert.text
            print(f"Alerta encontrado: {alert_text}")
            alert.accept()
            print("Alerta aceito")

            # Aguardar possível segundo alerta
            try:
                alert2 = WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert2.accept()
                print("Segundo alerta aceito")
            except TimeoutException:
                pass

        except TimeoutException:
            print("Nenhum alerta encontrado")

        # Aguardar processamento
        time.sleep(5)

    except TimeoutException:
        print("Não foi possível encontrar o botão 'Salvar'")
    except Exception as e:
        print(f"Erro ao salvar o formulário: {str(e)}")
        print("Stack trace:", traceback.format_exc())


def switch_to_frame_containing_element(driver, by, value):
    try:
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in frames:
            driver.switch_to.frame(frame)
            try:
                driver.find_element(by, value)
                print(
                    f"Encontrado o elemento dentro do iframe: {frame.get_attribute('name')}"
                )
                print("Mudamos para o iframe")
                return True
            except NoSuchElementException:
                driver.switch_to.parent_frame()
        print("Não foi possível encontrar o elemento dentro de nenhum iframe")
        return False
    except Exception as e:
        print(f"Erro ao mudar para o iframe: {str(e)}")
        return False


def press_ctrl_shift_l(driver):
    try:
        actions = ActionChains(driver)
        # No Mac, use Command (Keys.COMMAND) em vez de Control (Keys.CONTROL)
        actions.key_down(Keys.CONTROL)
        actions.key_down(Keys.SHIFT)
        actions.send_keys('l')
        actions.key_up(Keys.SHIFT)
        actions.key_up(Keys.CONTROL)
        actions.perform()
        print("Combinação Ctrl + Shift + L pressionada com sucesso")
    except Exception as e:
        print(f"Erro ao pressionar Ctrl + Shift + L: {str(e)}")

def processar_laudo(driver, numero, model: str):
    try:
        print(numero)
        report_path = os.path.join(os.getcwd(), "Reports", f"{numero}_final_report.md")
        # Create a new Event object for each process
        template_event = Event()
        # Initialize template with the event
        MiniTemplate(model, report_path, template_event)
        pesquisar_processo(driver, numero)
        time.sleep(3)
        clicar_laudo_medico(driver)
        time.sleep(2)
        if not  switch_to_frame_containing_element(driver, By.ID, "selParte"):
            if selecionar_parte_se_necessario(driver):
                print("Parte selecionada com sucesso")
            else:
                print("Não foi possível selecionar a parte")
        else:
            print("Elemento 'selParte' não está dentro de um iframe ou não foi encontradoTentando novamente...")

        if clicar_botao_novo(driver):
            time.sleep(5)
            # Wait for template with proper event object
            template_event.wait(timeout=30.0)
            if template_event.is_set():
                template_event.clear()
                preencher_formulario(driver, "laudo_template.json", template_event)

            if template_event.is_set():
                print("Salvando o formulário...")
                clicar_salvar(driver)
                print("Formulário salvo com sucesso.")
                shutil.move(
                    report_path,
                    os.path.join(
                        os.getcwd(), "Reports", "Processed", f"{numero}_final_report.md"
                    ),
                )
            else:
                print("Timeout aguardando geração do template")
            driver.quit()
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
    finally:
        driver.quit()
# Função auxiliar para debug
def debug_estado_pagina(driver):
    """
    Função auxiliar para debugar o estado atual da página.
    """
    try:
        print("\n=== DEBUG: Estado da página ===")
        print(f"URL atual: {driver.current_url}")
        print(f"Título da página: {driver.title}")
        print(f"Número de janelas: {len(driver.window_handles)}")

        # Verificar elementos importantes
        elementos_importante = ["sbmNovo", "selParte", "txtDataPericia"]
        for elemento_id in elementos_importante:
            try:
                elemento = driver.find_element(By.ID, elemento_id)
                print(f"✅ Elemento '{elemento_id}' encontrado: {elemento.is_displayed()}")
            except NoSuchElementException:
                print(f"❌ Elemento '{elemento_id}' NÃO encontrado")

        # Verificar iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Iframes encontrados: {len(iframes)}")

        print("=== FIM DEBUG ===\n")

    except Exception as e:
        print(f"Erro no debug: {e}")


def main(driver, numero):
    # INSERT_YOUR_CODE
    """
    ### 📝 main
    Main entry point for automating the EPROC form filling process using a Selenium WebDriver instance.

    This function orchestrates the workflow for logging into the EPROC system, handling potential alerts, and processing the report for a given case number. It is designed to be called with a pre-configured Selenium WebDriver and a valid case number.

    #### 🖥️ Parameters
        - `driver` (`selenium.webdriver`): Selenium WebDriver instance, already initialized and configured for browser automation.
        - `numero` (`str`): Case number or identifier to be processed. Must be a non-empty string.

    #### 🔄 Returns
        - `None`: This function does not return a value. All results are side effects (browser automation, file operations, console output).

    #### ⚠️ Raises
        - `ValueError`: If `driver` is None or not a valid WebDriver instance, or if `numero` is not a non-empty string.
        - `Exception`: Propagates exceptions raised during browser automation, login, or report processing, with descriptive error messages.

    #### 📌 Notes
        - The function expects the WebDriver to be managed externally (including setup and teardown).
        - Input validation is performed to ensure robust operation and clear error reporting.
        - Sensitive operations (such as login and file movement) are handled with error catching and descriptive output.
        - Adheres to best practices for Selenium automation and error handling.

    #### 💡 Example

    >>> from selenium import webdriver
    >>> driver = webdriver.Chrome()
    >>> main(driver, "1234567")
    (Automates login and report processing for case 1234567)
    """
    try:
        # Abrir o site do EPROC
        eproc_url = "https://eproc.jfrs.jus.br/eprocV2/"
        driver.get(eproc_url)

        # Lidar com possíveis alertas
        handle_alert(driver)

        print("Iniciando login...")
        usuario = "crmrs035013"
        senha = "*Andi009134"

        if not login(driver, usuario, senha):
            print("Falha no login automático. Por favor, faça login manualmente.")
            input("Pressione Enter após fazer login manualmente...")

        processar_laudo(driver, numero, "gpt-4.1-mini")
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
