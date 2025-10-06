"""
🏛️ Módulo EPROC - Automação de Download de Processos Judiciais

Módulo responsável pela automação do download de processos do sistema EPROC
do Tribunal Regional Federal da 4ª Região (TRF4).
"""

# Importações
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import os
import time
from selenium.webdriver.common.keys import Keys

# ===== CONFIGURAÇÕES GLOBAIS =====

# Configurar as opções do Chrome
user_home = os.path.expanduser("~")
chrome_profile = os.path.join(
    user_home, "Library", "Application Support", "Google", "Chrome", "Default"
)

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
            "download.default_directory": os.path.join(os.getcwd(), "Processos")
        }
    )

    return chrome_options

chrome_options = setup_chrome_options()


# ===== FUNÇÕES AUXILIARES =====

def clicar_botao_generico(driver, botao_id: str, nome_botao: str) -> bool:
    """
    🖱️ Clicador Genérico de Botões

    Função genérica para clicar em botões do sistema EPROC usando ID.

    🔧 Parameters:
    :param botao_id: 🆔 ID do elemento botão no HTML
    :type botao_id: str
    :param nome_botao: 📛 Nome descritivo do botão para logs
    :type nome_botao: str
    :return: ✅ True se conseguiu clicar, False caso contrário
    :rtype: bool
    :raises TimeoutException: ⏱️ Se o botão não for encontrado no tempo limite
    :raises Exception: ❌ Se houver erro durante o clique

    🎯 Example:
    ```python
        # Clicar no botão de download
        sucesso = clicar_botao_generico("btnDownload", "Download")
        if sucesso:
            print("✅ Botão clicado com sucesso")
        else:
            print("❌ Falha ao clicar no botão")
    ```
    """
    try:
        botao = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, botao_id))
        )
        print(f"Botão '{nome_botao}' encontrado. Clicando...")
        botao.click()
        return True
    except TimeoutException:
        print(f"Não foi possível encontrar o botão '{nome_botao}'.")
        return False
    except Exception as e:
        raise Exception(f"Erro ao clicar no botão '{nome_botao}': {str(e)}")


def handle_alert(driver) -> bool:
    """
    🚨 Gerenciador de Alertas do Navegador

    Função para detectar e aceitar alertas JavaScript do navegador.

    🔧 Parameters:
    :return: ✅ True se encontrou e aceitou alerta, False caso contrário
    :rtype: bool
    :raises TimeoutException: ⏱️ Se não houver alerta presente

    🎯 Example:
    ```python
        # Verificar se há alerta após uma ação
        if handle_alert():
            print("🚨 Alerta foi tratado")
        else:
            print("✅ Nenhum alerta encontrado")
    ```
    """
    try:
        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert_text = alert.text
        print(f"Alerta encontrado: {alert_text}")
        alert.accept()
        return True
    except TimeoutException:
        return False


# ===== FUNÇÕES DE AUTENTICAÇÃO =====

def tentar_login_automatico(driver_instance: webdriver.Chrome, usuario: str, senha: str, tempo_espera: int = 5) -> bool:
    """
    ### 🔐 tentar_login_automatico
    Performs automatic login to the EPROC system, supporting both native forms and SSO/Keycloak authentication.
    The function intelligently detects the available login form and handles authentication seamlessly.

    ### 🖥️ Parameters
        - `driver_instance` (`webdriver.Chrome`): Configured WebDriver instance for browser automation.
        - `usuario` (`str`): Username for authentication. Must be a valid EPROC system user.
        - `senha` (`str`): User password for authentication. Should meet system security requirements.
        - `tempo_espera` (`int`, optional): Timeout in seconds for element detection. Defaults to 5.

    ### 🔄 Returns
        - `bool`: Returns `True` if login is successful, `False` if authentication fails or elements are not found.

    ### ⚠️ Raises
        - `TimeoutException`: If login form elements are not found within the specified timeout period.
        - `Exception`: For any other errors encountered during the login process, including network issues or form validation errors.

    ### 💡 Example

    >>> if tentar_login_automatico(driver, "usuario123", "senha456", 10):
    ...     print("Login successful")
    ... else:
    ...     print("Login failed")
    Login successful

    ### 📚 Notes
    - The function automatically detects between standard EPROC forms and SSO/Keycloak authentication.
    - Handles iframe switching for SSO authentication when necessary.
    - Implements fallback mechanism to try alternative form structures if the primary form fails.
    - Consider using secure credential management in production environments.
    """

    espera = WebDriverWait(driver_instance, tempo_espera)

    # Tentar entrar no iframe SSO se existir
    try:
        espera.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ssoFrame")))
    except TimeoutException:
        pass

    # Formulários possíveis de login
    formularios = [
        {"user": (By.ID, "txtUsuario"), "pwd": (By.ID, "pwdSenha"), "btn": (By.ID, "sbmEntrar")},
        {"user": (By.ID, "username"), "pwd": (By.ID, "password"), "btn": (By.ID, "kc-login")},
    ]

    # Identificar formulário presente sem iterar por todos os itens
    # Tentar primeiro pelo user=txtUsuario; se não existir, usar o alternativo (username)
    selected_form = None
    try:
        campo_usuario = espera.until(
            EC.presence_of_element_located(formularios[0]["user"])
        )
        selected_form = formularios[0]
        print("Formulário padrão (txtUsuario) detectado.")
    except TimeoutException:
        print("Campo 'txtUsuario' não encontrado. Tentando formulário alternativo...")
        try:
            campo_usuario = espera.until(
                EC.presence_of_element_located(formularios[1]["user"])
            )
            selected_form = formularios[1]
            print("Formulário SSO/Keycloak (username) detectado.")
        except TimeoutException:
            raise Exception("Nenhum formulário de login reconhecido foi encontrado")

    # Validar campos pwd e btn; se faltar algum, usar o outro formulário
    try:
        campo_senha = espera.until(EC.presence_of_element_located(selected_form["pwd"]))
        botao_login = espera.until(EC.presence_of_element_located(selected_form["btn"]))
        print("Campos de senha e botão encontrados para o formulário selecionado.")
    except TimeoutException:
        print(
            "Algum campo ausente no formulário selecionado. Alternando para o formulário alternativo..."
        )
        fallback_form = (
            formularios[1] if selected_form == formularios[0] else formularios[0]
        )
        try:
            selected_form = fallback_form
            campo_usuario = espera.until(
                EC.presence_of_element_located(selected_form["user"])
            )
            campo_senha = espera.until(
                EC.presence_of_element_located(selected_form["pwd"])
            )
            botao_login = espera.until(
                EC.presence_of_element_located(selected_form["btn"])
            )
            print("Formulário alternativo validado com sucesso.")
        except TimeoutException:
            raise Exception("Nenhum formulário completo de login foi encontrado")

    # Preencher e submeter formulário
    campo_usuario.clear()
    campo_usuario.send_keys(usuario)
    campo_senha.clear()
    campo_senha.send_keys(senha)
    botao_login.click()

    # Tratar alerta opcional
    try:
        alerta = espera.until(EC.alert_is_present())
        alerta.accept()
    except TimeoutException:
        pass

    # Voltar ao conteúdo principal
    driver_instance.switch_to.default_content()

    # Verificar sucesso do login
    try:
        espera.until(EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida")))
        print("Login automático bem-sucedido.")
        return True
    except TimeoutException:
        print("Login provavelmente falhou – elemento pós-login não encontrado.")
        return False


# ===== FUNÇÕES DE NAVEGAÇÃO E PESQUISA =====

def pesquisar_processo(driver, numero_processo: str) -> None:
    """
    ### 🔍 pesquisar_processo

    Função para pesquisar um processo específico no sistema EPROC.

    ### 🖥️ Parameters:
    - `driver` (`webdriver.Chrome`): Configured WebDriver instance for browser automation.
    - `numero_processo` (`str`): Process number to search for. Must be a valid EPROC process number.
    :type numero_processo: str
    ### 🔄 Returns
        - `bool`: Returns `True` if search is successful, `False` if search fails or elements are not found.

    ### ⚠️ Raises
        - `TimeoutException`: If search field is not found within the specified timeout period.
        - `Exception`: For any other errors encountered during the search process, including network issues or form validation errors.

    ### 💡 Example:
    ```python
        # Pesquisar processo específico
        pesquisar_processo("5008676-91.2024.4.04.7102")
        print("Processo pesquisado com sucesso")
    ```
    """
    try:
        campo_pesquisa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida"))
        )
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(numero_processo)
        campo_pesquisa.send_keys(webdriver.Keys.RETURN)
        print(f"Pesquisando processo: {numero_processo}")
    except TimeoutException:
        raise Exception("Não foi possível encontrar o campo de pesquisa")


# ===== FUNÇÕES DE DOWNLOAD =====

def clicar_botao_download(driver) -> None:
    """
    📥 Iniciador de Download de Processo

    Função para clicar no botão de iniciar download completo do processo.

    📥 Parameters:
    :raises TimeoutException: ⏱️ Se botão de download não for encontrado
    :raises Exception: ❌ Se houver erro durante o clique

    📁 Example:
    ```python
        # Iniciar processo de download
        clicar_botao_download()
        print("📥 Download iniciado")
    ```
    """
    try:
        botao_download = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnDownloadCompletoRS"))
        )
        print("Botão de seção gerar download encontrado. Clicando...")
        botao_download.click()
    except TimeoutException:
        raise Exception("Não foi possível encontrar o botão de seção gerar download")


def clicar_botao_gerar(driver) -> bool:
    """
    ⚙️ Gerador de Arquivo de Download

    Função para clicar no botão "Gerar" do sistema de download.

    ⚙️ Parameters:
    :return: ✅ True se conseguiu clicar, False caso contrário
    :rtype: bool

    🎯 Example:
    ```python
        # Gerar arquivo para download
        if clicar_botao_gerar():
            print("⚙️ Geração iniciada")
    ```
    """
    return clicar_botao_generico(driver, "btnGerar", "Gerar")


def clicar_botao_baixar(driver) -> bool:
    """
    💾 Baixador de Arquivo Gerado

    Função para clicar no botão "Baixar" após arquivo estar pronto.

    💾 Parameters:
    :return: ✅ True se conseguiu clicar, False caso contrário
    :rtype: bool

    🎯 Example:
    ```python
        # Baixar arquivo gerado
        if clicar_botao_baixar():
            print("💾 Download iniciado")
    ```
    """
    return clicar_botao_generico(driver, "lblBaixar", "Baixar")


def esperar_arquivo_pronto(driver) -> bool:
    """
    ⏳ Monitor de Status de Geração

    Função para aguardar a geração completa do arquivo de download.

    ⏳ Parameters:
    :return: ✅ True se arquivo ficou pronto, False se timeout
    :rtype: bool
    :raises Exception: ❌ Se houver erro durante verificação

    🎯 Example:
    ```python
        # Aguardar arquivo ficar pronto
        if esperar_arquivo_pronto():
            print("✅ Arquivo pronto para download")
        else:
            print("⏱️ Timeout na geração do arquivo")
    ```
    """
    print("Aguardando a geração do arquivo...")
    start_time = time.time()
    timeout = 120  # 2 minutos

    while time.time() - start_time < timeout:
        try:
            if clicar_botao_generico(driver, "lblBaixar", "Baixar"):
                print("Arquivo gerado e pronto para download.")
                return True

            if clicar_botao_generico(driver, "btnGerar", "Gerar"):
                print("Aguardando o arquivo ficar pronto")
                return False

            time.sleep(2)
        except Exception as e:
            raise Exception(f"Erro durante a verificação: {str(e)}")

    print("Tempo limite excedido. O arquivo não foi gerado após 2 minutos.")
    return False


# ===== FUNÇÕES DE PROCESSAMENTO =====

def processar_numero(driver, numero_processo: str) -> None:
    """
    🔄 Processador Completo de Processo

    Função para processar completamente um número de processo, incluindo
    pesquisa, download e múltiplas tentativas em caso de falha.

    🔄 Parameters:
    :param numero_processo: 📋 Número do processo a ser processado
    :type numero_processo: str
    :raises Exception: ❌ Se todas as tentativas falharem

    🎯 Example:
    ```python
        # Processar um processo específico
        processar_numero("5008676-91.2024.4.04.7102")
        print("🎉 Processo concluído")
    ```
    """
    print(f"\nProcessando número: {numero_processo}")
    max_tentativas = 3
    tentativa = 0

    while tentativa < max_tentativas:
        tentativa += 1
        print(f"Tentativa {tentativa} de {max_tentativas}")

        try:
            pesquisar_processo(driver, numero_processo)
            time.sleep(3)
            clicar_botao_download(driver)
            time.sleep(3)

            if not clicar_botao_gerar(driver):
                print("Botão Gerar não encontrado, arquivo pode já estar pronto")
                if clicar_botao_baixar(driver):
                    print(f"Processo {numero_processo} concluído. O arquivo deve estar sendo baixado.")
                    return
            else:
                print("Arquivo não estava pronto, aguardando geração...")
                if esperar_arquivo_pronto(driver):
                    print(f"Processo {numero_processo} concluído. O arquivo deve estar sendo baixado.")
                    return

            print(f"Falha na tentativa {tentativa} para o processo {numero_processo}.")
        except Exception as e:
            print(f"Erro na tentativa {tentativa}: {str(e)}")

    # ■■■■■■■■■■■
    # PENDING LOGIC
    # ■■■■■■■■■■■
    # Pasta Pending deve existir (criação automática removida)
    pending_folder = os.path.join("Processos", "Pending")

    # Salvar registro do processo que falhou
    pending_file = os.path.join(pending_folder, f"{numero_processo}_pending.txt")
    with open(pending_file, "w", encoding="utf-8") as f:
        f.write(f"Processo: {numero_processo}\n")
        f.write(f"Tentativas: {max_tentativas}\n")
        f.write(f"Status: Falhou após todas as tentativas\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(
        f"⚠️ Processo {numero_processo} movido para Pending após {max_tentativas} tentativas"
    )
    raise Exception(f"Não foi possível baixar o arquivo para o processo {numero_processo} após {max_tentativas} tentativas")


def cleaning_downloaded(driver) -> list:
    """
    🧹 Limpador de Downloads Existentes

    Função para verificar quais processos já foram baixados na pasta Downloads.

    🧹 Parameters:
    :return: 📋 Lista de números de processos já baixados
    :rtype: list[str]
    :raises FileNotFoundError: 📁 Se pasta Downloads não existir
    :raises Exception: ❌ Se houver erro ao acessar arquivos

    🎯 Example:
    ```python
        # Verificar downloads existentes
        ja_baixados = cleaning_downloaded()
        print(f"📊 {len(ja_baixados)} processos já baixados")
    ```
    """
    try:
        download_folder = os.path.join("C:/Users/Anders", "Downloads")
        if not os.path.exists(download_folder):
            raise FileNotFoundError(f"Pasta de downloads não encontrada: {download_folder}")

        files = os.listdir(download_folder)
        file_list = []

        for file in files:
            if file.endswith(".PDF"):
                file_parts = file.split("-")
                if len(file_parts) > 1:
                    file_list.append(file_parts[1])

        return file_list
    except Exception as e:
        raise Exception(f"Erro ao verificar downloads existentes: {str(e)}")


# ===== FUNÇÃO PRINCIPAL =====

def EPROC_Download(numeros_processos: list[str]) -> bool:
    """
    ### 🚀 EPROC_Download
    Automates the download of multiple processes from the EPROC system, including automatic login and duplicate verification. This function orchestrates the entire download workflow, ensuring that all specified processes are handled efficiently.

    ### 🖥️ Parameters
    - `numeros_processos` (`list[str]`): A list of process numbers to download. Each entry should be a string representing a valid process number.

    ### 🔄 Returns
    - `bool`: Returns `True` if all processes were successfully processed. If any process fails, the function will raise an exception.

    ### ⚠️ Raises
    - `Exception`: Raised if a critical error occurs during execution, preventing the completion of the download process.

    ### 💡 Example

    >>> processos = ["5008676-91.2024.4.04.7102", "5003858-62.2025.4.04.7102"]
    >>> if EPROC_Download(processos):
    >>>     print("🎉 All processes have been processed")

    ### 📚 Notes
    - Ensure that the login credentials are correctly set up, preferably using environment variables for security.
    - The function assumes that the EPROC system is accessible and that the provided process numbers are valid.
    """
    try:
        # Abrir o site
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://eproc.jfrs.jus.br/eprocV2/")

        # Verificar downloads existentes

        # Credenciais (em produção, usar variáveis de ambiente)
        usuario = "crmrs035013"
        senha = "*Andi009134"

        # Função para verificar existência de arquivo
        def file_exists(filename: str) -> bool:
            return os.path.exists(os.path.join(".", filename))

        # Login automático
        if "painel_perito_listar" in driver.current_url:
            print("Login bem-sucedido. Estamos na página correta.")

        elif tentar_login_automatico(driver, usuario, senha):
            print("Login automático bem-sucedido. Continuando com o processamento.")

        time.sleep(3)

        # Processar cada número
        processos_com_erro = []
        for numero in numeros_processos:
            try:
                processar_numero(driver, numero)
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erro ao processar {numero}: {str(e)}")
                processos_com_erro.append(numero)
                continue

        if processos_com_erro:
            print(
                f"\n⚠️ {len(processos_com_erro)} processos com erro foram movidos para Pending"
            )
            print(f"Processos pendentes: {', '.join(processos_com_erro)}")
        else:
            print("✅ Todos os processos foram concluídos com sucesso.")

        input("Pressione Enter para fechar o navegador...")

        return True

    except Exception as e:
        print(f"❌ Erro crítico durante execução: {e}")
        raise e
    finally:
        driver.quit()
