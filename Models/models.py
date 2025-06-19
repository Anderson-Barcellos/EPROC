"""
Este módulo contém as funções e classes principais para o processamento de documentos,
geração de relatórios e interação com modelos de IA.

Funções principais:
- count_tokens: Conta os tokens de um arquivo ou string.
- GPT_generate_report: Gera um relatório usando o modelo GPT.
- organize_text: Organiza o texto extraído usando GPT-4o-mini.
- Gemini_generate_report: Gera um relatório usando o modelo Gemini.

Classes:
- Nenhuma classe definida neste módulo.

Constantes:
- save_path: Caminho para salvar os relatórios.
- generation_config: Configuração para geração de conteúdo com Gemini.

Dependências:
- tiktoken, os, threading, google.generativeai, openai, logging, ocrmac
"""

import os
import threading
import google.generativeai as genai
from openai import OpenAI
import json
import time
from threading import Event
import sys

# Add the parent directory to path so Python can find your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Tools import count_tokens

# GLOBALS
save_path = os.path.join(".", "Reports")
results = {}

#KEYS
gemini_key = os.getenv("GEMINI")
openai_key = os.getenv("OPENAI")


#!KEYS and APIS
genai.configure(api_key=gemini_key)

generation_config = {
 "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 65536,
  "response_mime_type": "text/plain",
}

# Adicione uma variável global para controlar o estado do template
template_ready = Event()


def GPTReport(name: str, model: str, system_instruction: str, reasoning_effort: str = "medium", threaded: bool = False):
    """### 📝 GPTReport
    Generates a medical report from a given text using the `OPENAI` models. This function can operate either synchronously or asynchronously in a separate thread.

    #### 🖥️ Parameters
        - `name` (`str`): The name of the input file to process, including its extension.
        - `model` (`str`): The identifier of the model to be used for report generation.
        - `system_instruction` (`str`): Instructions provided to the system for processing.
        - `reasoning_effort` (`str`, optional): The effort level for reasoning. Defaults to `medium`.
        - `threaded` (`bool`, optional): If set to `True`, the function runs in a separate thread. Defaults to `False`.

    #### 🔄 Returns
        - `None`: The function does not return a value but writes the output to a file.

    #### ⚠️ Raises
        - `FileNotFoundError`: If the specified input file does not exist.
        - `Exception`: For any other errors encountered during processing.

    #### 📌 Notes
    - The generated report is saved in the `Reports` directory with the filename format: `{name}_final_report.md`.

    #### 💡 Example

    >>> GPTReport("patient_file.pdf", model="gpt-4o-2024-08-06", system_instruction="Analyze the medical data", threaded=True)


    """


    def wrapper(name: str):
        try:
            prompt = ""
            print("Starting GPT Report")
            file_path = os.path.join(".", "Output", name)
            with open(file_path, "r", encoding="utf-8") as f:
                print(f"Reading file {name}")
                prompt = f.read()
                print("Requesting report generation")
                config = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_instruction
                        },
                        {
                            "role": "user",
                            "content": f"DADOS PARA PERICIA:{prompt}\n",
                        },
                    ],
                    "temperature": 0.3,
                }
                if "o3" in model.lower() or "o4-mini" in model.lower():
                    config["reasoning_effort"] = reasoning_effort
                    config.pop("temperature")

                response = client.chat.completions.create(**config)
                content = response.choices[0].message.content
                output_path = os.path.join(".", "Reports", f"{name[:-3]}_final_report.md")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"{content}")
                print(f"Final report generated and saved to {output_path}")

        except Exception as e:
            print(f"Error processing page {name}: {str(e)}")


    if threaded:
        threading.Thread(target=wrapper, args=(name,)).start()
    else:
        return wrapper(name)


def clean_and_validate_json(content):
    # Remove qualquer texto antes ou depois do JSON
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start != -1 and json_end != -1:
        content = content[json_start:json_end]

    try:
        # Tenta carregar e depois descarregar o JSON para garantir a validade
        return json.dumps(json.loads(content), ensure_ascii=False, indent=4)
    except json.JSONDecodeError:
        print("Conteúdo não é um JSON válido após limpeza.")
        return None


def MiniTemplate(model: str, file_path: str, template_event) -> str:
    """### 📝 MiniTemplate
    Organizes text using the GPT-4o-mini model to generate a structured output.

    #### 🖥️ Parameters
    - `model` (`str`): The model identifier to be used for processing.
    - `file_path` (`str`): The path to the input file containing the text to be organized.
    - `template_event` (`Event`, optional): A threading event (Barrier) to signal when the template is ready. Defaults to None.

    #### 🔄 Returns
    - `str`: The organized text in a structured format.

    #### ⚠️ Raises
    - `FileNotFoundError`: If the specified file path does not exist.
    - `ValueError`: If the model identifier is invalid or unsupported.

    #### 📌 Notes
    - Ensure the file at `file_path` is accessible and contains valid text data.
    - The function leverages threading for asynchronous processing when `template_event` is provided.

    #### 💡 Example

    >>> MiniTemplate("gpt-4o-mini", "path/to/file.txt", template_event)
    #"Organized text output"

    """
    def wrapper(file_path: str, template_event: Event = None):
        try:
            print("Starting mini template")
            prompt = ""
            file_path = file_path
            with open(file_path, "r", encoding="utf-8") as f:
                prompt = f.read()
            print(f"Awaking {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        Você receberá resumo do conteúdo de um processo judicial previdenciário. Sua função sera produzir um arquivo JSON conforme as instruções a seguir. ESTRUTURE AS STRINGS COM PARAGRAFOS ADEQUADAMENTES SEPARADOS POR NOVAS LINHAS QUANDO ADEQUADO:
                        # O PREENCHIMENTO SE DA DA SEGUINTE FORMA:
                        Organize as secoes usando espacos \n.

                        - ELEMENTOS QUE NAO POSSUEM UMA SECAO ESPECIFICA, DEVEM SER PREENCHIDOS A PARTIR DAS INFORMAÇÕES DISPONIVEIS NO CONTEÚDO. ABAIXO ESTA A LISTA DE ELEMENTOS A SEREM PREENCHIDOS:
                                "FormacaoTecnicoProfissional": "ESCOLARIDADE",
                                "UltimaAtividade": "ULTIMO TRABALHO REALIZADO",
                                "TarefasExigidasUltimaAtividade": "MANTENHA O VALOR PADRAO => Nao especificado",
                                "QuantoTempoUltimaAtividade": "MANTENHA O VALOR PADRAO => Nao especificado",
                                "AteQuandoUltimaAtividade": "DATA DE TERMINO DA ULTIMA ATIVIDADE",
                                "ExperienciasLaboraisAnt": "MANTENHA O VALOR PADRAO => -------",
                                "DCB": "ULTIMA DATA DE CESSACAO DE BENEFICIO OU DER NA AUSENCIA DE BENEFICIO",
                                "DID": "DATA DE INICIO DA DOENÇA",
                                "DER": "DATA DE ENTRADA DO REQUERIMENTO",
                                "DAP": "DATA DA ULTIMA ATIVIDADE PROFISSIONAL",



                        - OS ELEMENTOS QUE POSSUEM O VALOR ABAIXO IDENTICO, POSSUEM UMA SEÇÃO PROPRIA DE MESMO NOME. Sendo assim, devem ter seu valor substituido pela INTEGRIDADE DO TEXTO DA SEÇÃO:
                                "DocumentosMedicosAnalisados":  MAXIMO 10 itens (Mais recentes)
                                "HistoricoAnamnese":  Máximo de 100 palavras
                                "ExameFisicoMental": ""
                                "CONCLUSAO PERICIAL":  Máximo de 70 palavras
                                "ESCALA CIF": "" - Esta se presente junto do documento analisado, deve ser copiada em sua integridade.

                        - OS DEMAIS ELEMENTOS DEVEM SER PREENCHIDOS COM O VALOR JA ESPECIFICADO NO JSON
                        UMA VEZ PRONTO, RETORNE O TEMPLATE DE JSON COM OS VALORES PREENCHIDOS CONFORME AS INSTRUCOES ANTERIORES.

                        # EXEMPLOS:
                          <EXEMPLO PARA ELEMENTOS SEM SECAO ESPECIFICA>
                            "CONCLUSAO PERICIAL" : "SUBSTITUIR A STRING PADRAO PELA SUA PROCURA NO CONTEÚDO"
                            </EXEMPLO PARA ELEMENTOS SEM SECAO ESPECIFICA>

                            <EXEMPLO PARA ELEMENTOS COM SECAO ESPECIFICA>
                                "DocumentosMedicosAnalisados" : DOCUMENTOS MEDICOS ANALISADOS:
                                1. Receituário Médico:  Data: 22/08/2024- Médico: Dr. Hilton (assinatura ilegível)
                                CID: F33 (Transtorno depressivo recorrente)
                                Informações: A paciente Vera Lúcia Rangel da Rosa necessita de acompanhamento com cuidador. Prescrição de 180 dias.

                                2. Receituário Médico: Data: 13/08/2024- Médico: Dr. Nilton Souto - Psiquiatra (CRM RS7918)
                                CID: F33 (Transtorno depressivo recorrente)
                                Informações: Paciente em tratamento no CAPS com sintomas depressivos. Prescrição de Duloxetina 30g/dia, Amitriptilina 25mg/noite e outro medicamento ilegível 10mg/noite.

                            </EXEMPLO PARA ELEMENTOS COM SECAO ESPECIFICA>

                        <TEMPLATE DE JSON>
                        {
                            "json": {
                                "FormacaoTecnicoProfissional":"" ,
                                "UltimaAtividade": "",
                                "TarefasExigidasUltimaAtividade": "Nao especificado",
                                "QuantoTempoUltimaAtividade": "Nao especificado",
                                "AteQuandoUltimaAtividade": "",
                                "ExperienciasLaboraisAnt": "",
                                "MotivoIncapacidade": "(MAXIMO 3 PALAVRAS)",
                                "HistoricoAnamnese": "",
                                "DocumentosMedicosAnalisados": "",
                                "DCB": "",
                                "DID": "",
                                "CausaProvavelDiagnostico": "Adquirida",
                                "CIF": "Existindo um seção de escala CIF, deve ser copiada em sua integridade aqui"


                            }
                        }
                        </TEMPLATE DE JSON>
                        Observações:
                        Na falta de DCB, preencha a seção DCB com a mesma data de DER "
                        Esta devera ser o formato exato de texto json que sera retornado. Nao adicione mark languages ou outras informações.
                        NAO UTILIZE QUALQUER ESTILIZACAO NO TEXTO COMO MARKDOWN, HTML OU QUALQUER OUTRO FORMATO DE MARK LANGUAGE
                        NA SECAO DE DOCUMENTOS MEDICOS, PODE SER SUGERIDO O USO DE MARKDOWN PARA ORGANIZAR O TEXTO.

                        """
                    },
                    {
                        "role": "user",
                        "content": f"CONTEUDO PROCESSUAL: {prompt}",
                    },
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            print("Saving template")

            with open(os.path.join(".", "laudo_template.json"), "w", encoding="utf-8") as f:
                f.write(content)
            print("Template saved successfully")
            # Set the event to signal template is ready
            if template_event:
                template_event.set()

        except Exception as e:
            print(f"Error processing template: {str(e)}")

    threading.Thread(target=wrapper, args=(file_path, template_event)).start()


def GeminiReport(name: str, model_name: str, system_instruction: str, threaded: bool = False) -> None | bool:
    """
    ## 📝 Generate the Final Report from PDF


    Processes a PDF file and generates a medical report using the `Gemini AI` model.
    Can be run either synchronously or in a separate thread.

    #### 🖥️ Parameters
        - `name` (`str`): The name of the input file to process.
        - `system_instruction` (`str`): The system instruction to use.
        - `model_name` (`str`): The name of the model to use.
        - `threaded` (`bool, optional`): Whether to run the function in a new thread. Defaults to `False`.


    #### 📌 Notes
        - The output file will be written to the `Reports` directory and will have the filename: `{name}_final_report.md`.


    >>> GeminiReport("patient_file.pdf", model="gemini-1.5-flash-latest", threaded=True)

    """
    global generation_config


    #PATH FOR THE REPORT FILE
    md_path = os.path.join(".", "Output", f"{name}")

    def wrapper(name: str) -> bool:
        """
        Wrapper functions to call the Gemini model asynchronously.
        #### Parameters:
        - name: str: The name of the file. `(Automatically passed by the main function)`
        """
        try:
            print(f"Starting GeminiReport for file: {name}")

            model = genai.GenerativeModel(
                model_name= model_name,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            print("Initializing Gemini model...")
            #!CHECKING FILE PATH
            if not os.path.exists(md_path):
                print(f"Input file not found: {md_path}")
                return False

            print(f"Reading content from {name} file...")
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"Content read. File size: {len(content)} characters")

            #!PATH FOR THE REPORT FILE
            output_path = os.path.join(".", "Reports", f"{name[:-3]}_final_report.md")
            print(f"Output will be saved to: {output_path}")

            #!SENDING REQUEST TO THE GEMINI MODEL
            print("Sending request to Gemini model...")
            start_time = time.time()
            try:
                print("Generating content...")
                response = model.generate_content(f"DOCUMENTO:{content}")
                if response:
                    print("Content generated. Processing response...")
                    answer = response.text
                    print(f"Writing response to file: {output_path}")
                    with open( os.path.join(".", "Reports", f"{name[:-3]}_final_report.md"), "w", encoding="utf-8") as f:
                        f.write("\n" + answer)

                    print("Response written to file successfully")
                    end_time = time.time()
                    print(f"Report generation completed in {end_time - start_time:.2f} seconds")
                    return True
                else:
                    print("No response from Gemini")
                    return False
            except Exception as e:
                print(f"Error during content generation: {str(e)}")
                return False

        except FileNotFoundError:
            print(f"Input file not found: {md_path}")
            return False
        except Exception as e:
            print(f"Error in GeminiReport: {str(e)}")
            return False

    print(f"Starting GeminiReport in a new thread for file: {name}.md")
    if threaded:
        t = threading.Thread(target=wrapper, args=(name,))
        t.start()

    else:
        return wrapper(name)

