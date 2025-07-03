from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time


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
        "download.default_directory": os.path.join(user_home, "Downloads"),  # Diretório de download padrão
    }
)

# Iniciar o driver do Chrome#
#driver = webdriver.Chrome(options=chrome_options)

def clicar_botao_generico(driver, botao_id, nome_botao):
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
        print(f"Erro ao clicar no botão '{nome_botao}': {str(e)}")
        return False

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


def tentar_login_automatico(driver, usuario, senha):
    try:
        # Esperar pelo campo de usuário
        if driver.find_element(By.ID, "username"):
            campo_usuario = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
        elif driver.find_element(By.ID, "txtUsuario"):
            campo_usuario = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtUsuario"))
            )
        else:
            print("Não foi possível encontrar o campo de usuário.")
            return False
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        # Encontrar e preencher o campo de senha
        if driver.find_element(By.ID, "password"):
            campo_senha = driver.find_element(By.ID, "password")
        elif driver.find_element(By.ID, "pwdSenha"):
            campo_senha = driver.find_element(By.ID, "pwdSenha")
        else:
            print("Não foi possível encontrar o campo de senha.")
            return False
        campo_senha.clear()
        campo_senha.send_keys(senha)



        # Clicar no botão de login
        if driver.find_element(By.ID, "kc-login"):
            botao_login = driver.find_element(By.ID, "kc-login")
        elif driver.find_element(By.ID, "sbmEntrar"):
            botao_login = driver.find_element(By.ID, "sbmEntrar")
        else:
            print("Não foi possível encontrar o botão de login.")
            return False
        botao_login.click()

        alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert.accept()
        botao_login.click()

        # Esperar pela página carregar após o login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida"))
        )

        print("Login automático bem-sucedido.")
        return True
    except Exception as e:
        print(f"Erro no login automático: {str(e)}")
        return False


# Função para pesquisar um processo
def pesquisar_processo(driver, numero_processo):
    try:
        campo_pesquisa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtNumProcessoPesquisaRapida"))
        )
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(numero_processo)
        campo_pesquisa.send_keys(webdriver.Keys.RETURN)
        print(f"Pesquisando processo: {numero_processo}")
    except TimeoutException:
        print("Não foi possível encontrar o campo de pesquisa.")


# Função para clicar no botão de download
def clicar_botao_download(driver):
    try:
        botao_download = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnDownloadCompletoRS"))
        )
        print("Botão de seçao gerar download encontrado. Clicando...")
        botao_download.click()
    except TimeoutException:
        print("Não foi possível encontrar o botão de seçao gerar download.")
    except Exception as e:
        print(f"Erro ao clicar no botão de seçao gerar download: {str(e)}")


# Função para clicar no botão "Gerar"
def clicar_botao_gerar(driver):
    return clicar_botao_generico(driver, "btnGerar", "Gerar")


# Função para esperar a mudança na página
def esperar_arquivo_pronto(driver):
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
            print(f"Erro durante a verificação: {str(e)}")

    print("Tempo limite excedido. O arquivo não foi gerado após 2 minutos.")
    return False

def processar_numero(driver, numero_processo):
    print(f"\nProcessando número: {numero_processo}")
    max_tentativas = 3
    tentativa = 0

    while tentativa < max_tentativas:
        tentativa += 1
        print(f"Tentativa {tentativa} de {max_tentativas}")

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

    print(f"Não foi possível baixar o arquivo para o processo {numero_processo} após {max_tentativas} tentativas.")

# Adicione esta função
def clicar_botao_baixar(driver):
    return clicar_botao_generico(driver, "lblBaixar", "Baixar")

# Lista de números de processos






def EPROC_Download(numeros_processos: list):

    """### 📝 EPROC_Download
            Initiates the download process for a list of process numbers from the EPROC system.

            #### 🖥️ Parameters
                - `numeros_processos` (`list`): A list of process numbers to be downloaded. Each process number should be a string.

            #### 🔄 Returns
                - `bool`: Returns `True` when all processes have been attempted for download.

            #### ⚠️ Raises
                - `Exception`: If there is an issue with the login process or if the download fails after maximum attempts.

            #### 📌 Notes
                - Ensure that the user credentials are correctly set before running the function.
                - The function assumes that the necessary web driver and other dependencies are properly configured.
                - The function will prompt for manual login if automatic login fails.

            #### 💡 Example

            >>> EPROC_Download(["50008601220254047106", "50008515020254047106"])
            True
    """
    driver = webdriver.Chrome(options=chrome_options)
    # Abrir o site que requer autenticação
    driver.get("https://eproc.jfrs.jus.br/eprocV2/")

 #   remaining = [x for x in numeros_processos if x not in cleaningDownloaded()]
    # Tentar login automático
    usuario = "crmrs035013"  # Substitua com seu usuário real
    senha = "*Andi009134"  # Substitua com sua senha real
    presence = lambda x:os.path.exists(os.path.join(".", x))

    if tentar_login_automatico(driver,  usuario, senha):
        print("Login automático bem-sucedido. Continuando com o processamento.")

    # Esperar um pouco para a página carregar
    time.sleep(3)

    # Verificar se estamos na página correta
    if "painel_perito_listar" in driver.current_url:
        print("Login bem-sucedido. Estamos na página correta.")
    else:
        print(
            "Não foi possível fazer login automaticamente. Por favor, faça login manualmente."
        )
        input("Pressione Enter depois de fazer login manualmente...")

    # Iterar sobre a lista de números de processos
    for numero in numeros_processos:
        if not presence(numero):
            processar_numero(driver, numero)
            time.sleep(5)  # Pequena pausa entre processos
        else:
            print(f"Arquivo {numero} já existe. Pulando...")

    print("Todos os processos foram concluídos.")

    # Manter o navegador aberto até que o usuário decida fechar
    input("Pressione Enter para fechar o navegador...")

    # Fechar o navegador quando terminar
    driver.quit()
    return True

