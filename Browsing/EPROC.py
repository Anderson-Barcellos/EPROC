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

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={chrome_profile}")

# Adicionar configurações para forçar o download de PDFs
chrome_options.add_experimental_option(
    "prefs", {
        "download.prompt_for_download": False,
        "download.automatically_downloads": True,
        "plugins.disabled": ["Chrome PDF Viewer"],
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "download.default_directory": os.path.join("D:\\OneDrive\\Área de Trabalho\\Complementares\\Processos")
          # Diretório de download padrão
    }
)

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
    🔐 Autenticador Automático EPROC

    Função para realizar login automático no sistema EPROC, suportando tanto
    formulário nativo quanto SSO/Keycloak.

    🔧 Parameters:
    :param driver_instance: 🌐 Instância do WebDriver configurada
    :type driver_instance: webdriver.Chrome
    :param usuario: 👤 Nome de usuário para login
    :type usuario: str
    :param senha: 🔑 Senha do usuário
    :type senha: str
    :param tempo_espera: ⏱️ Timeout em segundos (padrão: 15)
    :type tempo_espera: int
    :return: ✅ True se login bem-sucedido, False caso contrário
    :rtype: bool
    :raises TimeoutException: ⏱️ Se elementos de login não forem encontrados
    :raises Exception: ❌ Se houver erro durante o processo de login

    🎯 Example:
    ```python
        # Login automático no sistema
        if tentar_login_automatico(driver, "usuario123", "senha456"):
            print("🎉 Login realizado com sucesso")
        else:
            print("❌ Falha no login automático")
    ```
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

    # Identificar formulário presente
    for form in formularios:
        try:
            campo_usuario = espera.until(EC.presence_of_element_located(form["user"]))
            campo_senha = driver_instance.find_element(*form["pwd"])
            botao_login = driver_instance.find_element(*form["btn"])
            break
        except TimeoutException:
            continue
    else:
        raise Exception("Nenhum formulário de login reconhecido foi encontrado")

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
    🔍 Pesquisador de Processos EPROC

    Função para pesquisar um processo específico no sistema EPROC.

    🔧 Parameters:
    :param numero_processo: 📋 Número do processo judicial
    :type numero_processo: str
    :raises TimeoutException: ⏱️ Se campo de pesquisa não for encontrado
    :raises Exception: ❌ Se houver erro durante a pesquisa

    🎯 Example:
    ```python
        # Pesquisar processo específico
        pesquisar_processo("5008676-91.2024.4.04.7102")
        print("🔍 Processo pesquisado com sucesso")
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
    🚀 Orquestrador Principal de Downloads

    Função principal para automatizar o download de múltiplos processos
    do sistema EPROC com login automático e verificação de duplicatas.

    🚀 Parameters:
    :param numeros_processos: 📋 Lista de números de processos para download
    :type numeros_processos: list[str]
    :return: ✅ True se todos os processos foram processados
    :rtype: bool
    :raises Exception: ❌ Se houver erro crítico durante execução

    🎯 Example:
    ```python
        # Processar lista de processos
        processos = ["5008676-91.2024.4.04.7102", "5003858-62.2025.4.04.7102"]
        if Download_Processos(processos):
            print("🎉 Todos os processos foram processados")
    ```
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
        if tentar_login_automatico(driver, usuario, senha):
            print("Login automático bem-sucedido. Continuando com o processamento.")
        else:
            print("Não foi possível fazer login automaticamente. Por favor, faça login manualmente.")
            input("Pressione Enter depois de fazer login manualmente...")

        time.sleep(3)

        # Verificar página correta
        if "painel_perito_listar" in driver.current_url:
            print("Login bem-sucedido. Estamos na página correta.")
        else:
            print("Verificação manual de login necessária.")
            input("Pressione Enter após confirmar que está logado...")

        # Processar cada número
        for numero in numeros_processos:
            processar_numero(driver, numero)
            time.sleep(5)


        print("Todos os processos foram concluídos.")
        input("Pressione Enter para fechar o navegador...")

        return True

    except Exception as e:
        print(f"❌ Erro crítico durante execução: {e}")
        raise e
    finally:
        driver.quit()

