"""Module with tools for the project"""

import tiktoken
from tqdm import tqdm
import os

# ■■■■■■■■■■■
#  LOGGING SETUP
# ■■■■■■■■■■■

import logging
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Dict, Optional


class ErrorType(Enum):
    """Error categorization for contextual logging"""

    NETWORK = "network"  # Connection, timeout, HTTP errors
    OCR = "ocr"  # Image processing, text recognition
    PARSING = "parsing"  # Data extraction, format errors
    VALIDATION = "validation"  # Input validation, constraint errors
    FILESYSTEM = "filesystem"  # File I/O, permissions, paths
    AUTH = "authentication"  # Login, credentials, sessions
    BROWSER = "browser"  # Selenium, element not found
    BUSINESS = "business"  # Workflow logic, business rules


class WorkflowLogger:
    """
    ### 📝 WorkflowLogger
    Enhanced logging class with contextual error handling and dynamic level assignment.
    Provides different logging strategies for different error types in EPROC workflows.

    ### 🖥️ Parameters
        - `name` (`str`): Logger name identifier, typically the module or workflow name.
        - `log_level` (`str`, optional): Base logging level. Defaults to 'INFO'.
        - `log_to_file` (`bool`, optional): Whether to save logs to file. Defaults to True.
        - `log_dir` (`str`, optional): Directory path for log files. Defaults to 'Logs'.
        - `error_levels` (`dict`, optional): Custom error level mappings per error type.

    ### 🔄 Returns
        - `WorkflowLogger`: Configured logger instance with contextual error handling.

    ### 💡 Example
    >>> logger = WorkflowLogger("EPROC_OCR", "DEBUG")
    >>> logger.ocr_error("Failed to recognize text in document", details="Low image quality")
    >>> logger.network_warning("Slow connection detected", retry_count=2)

    ### 📚 Notes
    - Different error types can have different logging levels for fine-tuned control
    - Includes specialized methods for EPROC-specific error scenarios
    """

    # ■■■■■■■■■■■
    #  LOG LEVEL MAPPING
    # ■■■■■■■■■■■

    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # ■■■■■■■■■■■
    #  DEFAULT ERROR TYPE LEVELS
    # ■■■■■■■■■■■

    DEFAULT_ERROR_LEVELS = {
        ErrorType.NETWORK: logging.WARNING,  # Network issues often recoverable
        ErrorType.OCR: logging.ERROR,  # OCR failures need immediate attention
        ErrorType.PARSING: logging.ERROR,  # Data parsing critical for workflow
        ErrorType.VALIDATION: logging.WARNING,  # Input validation can be handled
        ErrorType.FILESYSTEM: logging.ERROR,  # File issues are serious
        ErrorType.AUTH: logging.CRITICAL,  # Authentication failures critical
        ErrorType.BROWSER: logging.WARNING,  # Browser issues often recoverable
        ErrorType.BUSINESS: logging.ERROR,  # Business logic errors important
    }

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_dir: str = "Logs",
        error_levels: Optional[Dict[ErrorType, int]] = None,
    ):
        print(f"🔧: initializing logger '{name}'")

        self.logger = logging.getLogger(name)

        # ✅ FIXED: Direct level mapping instead of getattr
        base_level = self.LOG_LEVELS.get(log_level.upper(), logging.INFO)
        self.logger.setLevel(base_level)

        # Setup custom error level mappings
        self.error_levels = error_levels or self.DEFAULT_ERROR_LEVELS.copy()

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # [Rest of __init__ remains the same...]
        if log_to_file:
            log_path = Path(log_dir)
            log_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_path / f"{name}_{timestamp}.log"

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s [%(error_type)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "[%(asctime)s] %(emoji)s %(levelname)s [%(error_type)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        print(f"✅: logger '{name}' configured successfully")

    def _log_contextual(
        self,
        error_type: ErrorType,
        message: str,
        emoji: str,
        details: str = "",
        override_level: Optional[int] = None,
    ):
        """Enhanced internal logging with error type context"""

        # Use override level or default level for error type
        level = override_level or self.error_levels.get(error_type, logging.INFO)
        level_name = logging.getLevelName(level).upper()

        # Build enhanced message
        full_message = message
        if details:
            full_message += f" | Details: {details}"

        # Create log record with context
        extra = {"emoji": emoji, "error_type": error_type.value.upper()}

        # Log at appropriate level
        self.logger.log(level, full_message, extra=extra)

    # ■■■■■■■■■■■
    #  CONTEXTUAL ERROR METHODS
    # ■■■■■■■■■■■

    def network_error(self, message: str, details: str = "", url: str = ""):
        """Log network-related errors with 🌐 emoji"""
        enhanced_details = f"{details} | URL: {url}" if url else details
        self._log_contextual(ErrorType.NETWORK, message, "🌐", enhanced_details)

    def network_warning(self, message: str, details: str = "", retry_count: int = 0):
        """Log network warnings with ⚡ emoji"""
        enhanced_details = (
            f"{details} | Retry: {retry_count}" if retry_count > 0 else details
        )
        self._log_contextual(
            ErrorType.NETWORK, message, "⚡", enhanced_details, logging.WARNING
        )

    def ocr_error(self, message: str, details: str = "", image_path: str = ""):
        """Log OCR processing errors with 👁️ emoji"""
        enhanced_details = f"{details} | Image: {image_path}" if image_path else details
        self._log_contextual(ErrorType.OCR, message, "👁️", enhanced_details)

    def parsing_error(self, message: str, details: str = "", data_source: str = ""):
        """Log data parsing errors with 📄 emoji"""
        enhanced_details = (
            f"{details} | Source: {data_source}" if data_source else details
        )
        self._log_contextual(ErrorType.PARSING, message, "📄", enhanced_details)

    def validation_warning(self, message: str, details: str = "", field_name: str = ""):
        """Log validation warnings with 🔍 emoji"""
        enhanced_details = f"{details} | Field: {field_name}" if field_name else details
        self._log_contextual(
            ErrorType.VALIDATION, message, "🔍", enhanced_details, logging.WARNING
        )

    def filesystem_error(self, message: str, details: str = "", file_path: str = ""):
        """Log filesystem errors with 📁 emoji"""
        enhanced_details = f"{details} | Path: {file_path}" if file_path else details
        self._log_contextual(ErrorType.FILESYSTEM, message, "📁", enhanced_details)

    def auth_critical(self, message: str, details: str = "", username: str = ""):
        """Log authentication critical errors with 🔐 emoji"""
        enhanced_details = f"{details} | User: {username}" if username else details
        self._log_contextual(
            ErrorType.AUTH, message, "🔐", enhanced_details, logging.CRITICAL
        )

    def browser_warning(self, message: str, details: str = "", element: str = ""):
        """Log browser automation warnings with 🌍 emoji"""
        enhanced_details = f"{details} | Element: {element}" if element else details
        self._log_contextual(
            ErrorType.BROWSER, message, "🌍", enhanced_details, logging.WARNING
        )

    def business_error(self, message: str, details: str = "", workflow_step: str = ""):
        """Log business logic errors with 💼 emoji"""
        enhanced_details = (
            f"{details} | Step: {workflow_step}" if workflow_step else details
        )
        self._log_contextual(ErrorType.BUSINESS, message, "💼", enhanced_details)

    # ■■■■■■■■■■■
    #  EXISTING METHODS (PRESERVED)
    # ■■■■■■■■■■■

    def _log_with_emoji(self, level: str, message: str, emoji: str):
        """Internal method to add emoji to log records (backward compatibility)"""
        extra = {"emoji": emoji, "error_type": "GENERAL"}
        getattr(self.logger, level.lower())(message, extra=extra)

    def debug(self, message: str):
        """Log debug message with 🔍 emoji."""
        self._log_with_emoji("DEBUG", message, "🔍")

    def info(self, message: str):
        """Log info message with 🔄 emoji."""
        self._log_with_emoji("INFO", message, "🔄")

    def success(self, message: str):
        """Log success message with ✅ emoji."""
        self._log_with_emoji("INFO", message, "✅")

    def warning(self, message: str):
        """Log warning message with ⚠️ emoji."""
        self._log_with_emoji("WARNING", message, "⚠️")

    def error(self, message: str):
        """Log error message with ❌ emoji."""
        self._log_with_emoji("ERROR", message, "❌")

    def critical(self, message: str):
        """Log critical message with 🚨 emoji."""
        self._log_with_emoji("CRITICAL", message, "🚨")

    def step(self, step_name: str, message: str = ""):
        """Log workflow step with 📋 emoji."""
        full_message = f"STEP: {step_name}"
        if message:
            full_message += f" - {message}"
        self._log_with_emoji("INFO", full_message, "📋")

    def progress(self, current: int, total: int, message: str = ""):
        """Log progress with 📊 emoji."""
        percentage = (current / total) * 100 if total > 0 else 0
        progress_message = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if message:
            progress_message += f" - {message}"
        self._log_with_emoji("INFO", progress_message, "📊")


def check_presence(number) -> bool | str:
    """
    ### 🔍 check_presence
    This function checks for the presence of a file with a specific identifier number in predefined directories.
    It searches through files with extensions .PDF, .md, and .txt, extracting the relevant part of the filename
    to match against the provided number. The function is useful for verifying the existence of files based on
    a unique identifier within a structured directory setup.

    ### 🖥️ Parameters
        - `number` (`str`): The unique identifier to search for within the filenames. It should be a string
          representation of the number.

    ### 🔄 Returns
        - `tuple` or `bool`: Returns a tuple (True, file_path) if the file is found, where `file_path` is the
          full path to the file. Returns `False` if no matching file is found.

    ### ⚠️ Raises
        - `TypeError`: If the `number` parameter is not a string.

    ### 💡 Example

    >>> check_presence("12345678901234567890")
    (True, 'Processos/12345678901234567890.PDF')
    """
    path_list =["Processos", "Output", "Reports"]
    for path in path_list:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".PDF"):
                    name = f"{file[3:23]}"
                    if name == number:
                        if "Processed" in root:
                            print(f"Arquivo {file} já processado", root)
                            return True
                        else:
                            return False
                elif file.endswith(".md"):
                    file = file.split("_")[0]
                    if file == number:
                        return True
                elif file.endswith(".txt"):
                    file = file.split(".")[0]
                    if file == number:
                        return True
    return False


class ProgressBar:

    """
    ### ⏳ Progress Bar
    Class to display a progress bar using the tqdm library

    ### 📝 Parameters:

        🔹 `total: int` - The total number of steps for the progress bar
        🔹 `description: str` - The description displayed next to the progress bar (default: 'Processing')
        🔹 `variable: str` - The unit of measurement displayed on the progress bar (default: 'items')

    ### ⚙️ How to use:
    ```python
    from Tools.tools import ProgressBar

    pbar = ProgressBar(total=100, description="Loading", variable="files")
    for i in range(100):
        # your processing code here
        pbar.update(1)
    pbar.close()
    ```
    """

    def __init__(self, total, description="Processing", variable="items") -> None:

        self.pbar = tqdm(total=total, desc=description, unit=variable)

    def update(self, n):
        """
        Update the progress bar by a given number of steps.

        Parameters:
        - n (int): Number of steps to update the progress bar by.
        """
        self.pbar.update(n)

    def reset(self):
        """
        Reset the progress bar.
        """
        self.pbar.reset()

    def close(self):
        """
        Close the progress bar.
        """
        self.pbar.close()


def count_tokens(file_path, model_name, mode):
    """
    ### 🔢 Contador de Tokens
    Função para contar tokens de um arquivo ou string e calcular o preço com suporte aos modelos mais recentes (junho/agosto 2024)

    ### 📝 Parameters:

        🔹 `file_path: str` - O caminho para o arquivo ou a string para contar os tokens
        🔹 `model_name: str` - O nome do modelo a ser usado para contagem
        🔹 `mode: str` - "input" ou "output" para determinar o preço

    ### 🔄 Returns:
        🔹 `tuple` - (número de tokens, preço)

    ### ⚙️ Como usar:
    ```python
    from Tools.tools import count_tokens
    n_tokens, preco = count_tokens("meuarquivo.txt", "gpt-4.1", "input")
    ```
    """
    try:
        num_tokens = 0
        price = 0
        factor = 0
        text = ""

        # Preços atualizados (junho/agosto 2024)
        # Referências: OpenAI, Google Gemini
        # Valores em dólares por 1.000 tokens
        model_pricing = {
            # OpenAI
            "gpt-4.1": {"input": 0.00200, "output": 0.00800},
            "gpt-4o": {"input": 0.00250, "output": 0.01000},
            "gpt-4o-2024-08-06": {"input": 0.00250, "output": 0.01000},
            "gpt-4o-mini": {"input": 0.000150, "output": 0.00060},
            # Gemini
            "gemini-1.5-pro": {"input": 0.00350, "output": 0.01050},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.00030},
        }

        # Normalização do nome do modelo
        model_key = model_name.lower().replace(" ", "-")
        if "gemini" in model_key and "flash" in model_key:
            model_key = "gemini-1.5-flash"
        elif "gemini" in model_key:
            model_key = "gemini-1.5-pro"
        elif "gpt-4.1" in model_key:
            model_key = "gpt-4.1"
        elif "gpt-4o-mini" in model_key:
            model_key = "gpt-4o-mini"
        elif "gpt-4o" in model_key:
            model_key = "gpt-4o"
        elif "gpt-3.5" in model_key:
            # GPT-3.5 Turbo (mantido para compatibilidade)
            model_pricing["gpt-3.5-turbo"] = {"input": 0.00050, "output": 0.00150}
            model_key = "gpt-3.5-turbo"
        else:
            raise ValueError(f"Modelo não suportado: {model_name}")

        if mode not in ["input", "output"]:
            raise ValueError("O parâmetro 'mode' deve ser 'input' ou 'output'.")

        if model_key not in model_pricing:
            raise ValueError(f"Modelo não suportado: {model_name}")

        factor = model_pricing[model_key][mode] / 1000  # preço por token

        # Leitura do texto
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
        else:
            text = file_path

        # Contagem de tokens
        if "gemini" in model_key:
            num_tokens = len(text) // 4
        else:
            try:
                enc = tiktoken.encoding_for_model(model_name)
                tokens = enc.encode(text)
                num_tokens = len(tokens)
            except Exception as e:
                raise RuntimeError(f"Erro ao codificar tokens: {str(e)}")

        price = num_tokens * factor

        print(f"Number of tokens: {num_tokens}")
        print(f"The price is: $ {price}")

        return num_tokens, price

    except Exception as e:
        raise RuntimeError(f"Erro ao contar tokens: {str(e)}")


#!/usr/bin/env python3
"""
SimplePushbullet - Uma implementação minimalista e elegante para envio de notificações
Autor: Script criado para Anders
Data: Agosto 2025
Descrição: Este script implementa uma única classe que simplifica drasticamente
           o uso da API do Pushbullet, reduzindo toda a complexidade a um método simples.
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
import os


class SimplePushbullet:
    """
    📲 SimplePushbullet
    A minimalist class designed to interact with the Pushbullet API. This implementation emphasizes maximum simplicity: one token, one method, zero complications. All the magic happens internally, keeping the interface clean and intuitive.

    ### 🖥️ Parameters
    - `token` (`str`, optional): The API token for authentication. Can be passed directly or set as an environment variable `PUSHBULLET_TOKEN`. Defaults to a predefined token.

    ### 🔄 Returns
    - `None`: This class does not return a value but initializes an instance for API interaction.

    ### ⚠️ Raises
    - `ValueError`: If the token is not provided or is invalid.

    ### 📚 Notes
    - Ensure the token is kept secure and not hardcoded in production environments.
    - The class automatically verifies the token upon initialization to prevent future errors.
    """

    def __init__(self, token = "o.5FFnilYMZeEtI82l0r9np7NUhmRcG8qp"):
        """
        Inicializa o cliente Pushbullet.

        O token pode ser passado diretamente ou definido como variável de ambiente
        PUSHBULLET_TOKEN. Isso te dá flexibilidade para não hardcodar credenciais
        no código, mantendo tudo mais seguro.
        """
        self.token = token
        if not self.token:
            raise ValueError(
                "Token não fornecido! Passe o token no construtor ou "
                "defina a variável de ambiente PUSHBULLET_TOKEN"
            )

        # URL base da API - sempre a mesma, então deixamos como constante
        self.base_url = "https://api.pushbullet.com/v2"

        # Headers padrão para todas as requisições
        self.headers = {
            'Access-Token': self.token,
            'Content-Type': 'application/json'
        }

        # Vamos verificar se o token é válido logo na inicialização
        self._verify_token()

    def _verify_token(self) -> None:
        """
        Verifica se o token é válido fazendo uma requisição simples à API.

        Isso evita surpresas mais tarde - melhor descobrir agora se algo está errado
        do que quando tu realmente precisar enviar uma notificação importante.
        """
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            if response.status_code != 200:
                raise ValueError(f"Token inválido ou erro na API: {response.status_code}")

            # Aproveita e pega o nome do usuário para dar um feedback mais amigável
            user_data = response.json()
            self.user_email = user_data.get('email', 'Usuário')
            print(f"✓ Conectado ao Pushbullet como: {self.user_email}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro ao conectar com Pushbullet: {e}")

    def push(self,
             text: str,
             title: Optional[str] = None,
             url: Optional[str] = None) -> Dict[str, Any]:
        """
        ## 📲 Push Notification
        Sends a push notification using the Pushbullet API. This method allows you to send a message with an optional title and URL, handling the details of the API request for you.

        ### 🖥️ Parameters
            - `text` (`str`): The body of the message. This parameter is required.
            - `title` (`str`, optional): The title of the notification. Defaults to "Notification".
            - `url` (`str`, optional): A URL to open when the notification is clicked.

        ### 🔄 Returns
            - `Dict[str, Any]`: A dictionary containing the response data from the API, including the push ID if successful.

        ### ⚠️ Raises
            - `requests.exceptions.RequestException`: If there is an issue with the network request.

        ### 💡 Example

        >>> push("Hello World", title="Greeting", url="http://example.com")
        {'iden': 'ujpah72o0sjAoR', ...}

        ### 📚 Notes
        - Ensure that the Pushbullet API token is valid and set before calling this method.
        - The method handles both note and link types of pushes based on the presence of a URL.
        """
        # Define um título padrão se não foi fornecido
        title = f"{title} - {datetime.now().strftime('%H:%M')}"

        # Monta o payload baseado no tipo de push
        if url:
            # Push tipo link - abre uma URL quando clicado
            payload = {
                'type': 'link',
                'title': title,
                'body': text,
                'url': url
            }
        else:
            # Push tipo note - notificação simples de texto
            payload = {
                'type': 'note',
                'body': text,
                'title': title
            }

        try:
            # Faz a requisição POST para criar o push
            response = requests.post(
                f"{self.base_url}/pushes",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )

            # Verifica se deu tudo certo
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Push enviado com sucesso! ID: {result.get('iden', 'N/A')}")
                return result
            else:
                error_msg = f"Erro ao enviar push: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error_description', response.text)}"
                    except:
                        error_msg += f" - {response.text}"

                print(f"✗ {error_msg}")
                return {'error': error_msg, 'status_code': response.status_code}

        except requests.exceptions.Timeout:
            error_msg = "Timeout ao enviar push - a API demorou muito para responder"
            print(f"✗ {error_msg}")
            return {'error': error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão: {e}"
            print(f"✗ {error_msg}")
            return {'error': str(e)}

    def push_to_device(self,
                       device_iden: str,
                       text: str,
                       title: Optional[str] = None) -> Dict[str, Any]:
        """
        Envia uma notificação para um dispositivo específico.

        Útil quando tu tem múltiplos dispositivos e quer direcionar a notificação
        para apenas um deles - tipo mandar algo só pro teu celular, não pro tablet.

        Args:
            device_iden: Identificador do dispositivo
            text: Corpo da mensagem
            title: Título (opcional)

        Returns:
            Dict com a resposta da API
        """
        if title is None:
            title = f"Notificação - {datetime.now().strftime('%H:%M')}"

        payload = {
            'type': 'note',
            'title': title,
            'body': text,
            'device_iden': device_iden
        }

        try:
            response = requests.post(
                f"{self.base_url}/pushes",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Push enviado para dispositivo {device_iden}")
                return result
            else:
                error_msg = f"Erro ao enviar para dispositivo: {response.status_code}"
                print(f"✗ {error_msg}")
                return {'error': error_msg}

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro: {e}")
            return {'error': str(e)}

    def list_devices(self) -> list:
        """
        Lista todos os dispositivos conectados à conta.

        Bem útil para descobrir o device_iden quando tu quer enviar
        notificações direcionadas.
        """
        try:
            response = requests.get(
                f"{self.base_url}/devices",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                devices = response.json().get('devices', [])
                active_devices = [d for d in devices if d.get('active')]

                print(f"\n📱 Dispositivos ativos ({len(active_devices)}):")
                for device in active_devices:
                    print(f"  • {device.get('nickname', 'Sem nome')} "
                          f"({device.get('model', 'Modelo desconhecido')}) "
                          f"- ID: {device.get('iden')}")

                return active_devices
            else:
                print(f"✗ Erro ao listar dispositivos: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro: {e}")
            return []
