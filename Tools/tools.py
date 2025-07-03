
"""Module with tools for the project"""

import tiktoken
from tqdm import tqdm
import os

def check_presence(number)->bool | str:
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


