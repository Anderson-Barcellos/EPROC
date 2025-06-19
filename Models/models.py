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
from Browsing import *
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


client = OpenAI(api_key=openai_key)

generation_config = {
 "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 65536,
  "response_mime_type": "text/plain",
}

# Adicione uma variável global para controlar o estado do template
template_ready = Event()


def GPTReport(name: str, model: str, system_instruction: str, threaded: bool = False):
    """### 📝 GPTReport
    Generates a medical report from a given text using the `OPENAI` models. This function can operate either synchronously or asynchronously in a separate thread.

    #### 🖥️ Parameters
        - `name` (`str`): The name of the input file to process, including its extension.
        - `model` (`str`): The identifier of the model to be used for report generation.
        - `system_instruction` (`str`): Instructions provided to the system for processing.
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
                    config["max_completion_tokens"] = 100000
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


def O3Report(name: str, model: str, system_instruction: str, threaded: bool = False, reasoning_effort: str = "medium"):
    """### 📝 O3Report
    Generates a medical report using OpenAI's o3/o4-mini reasoning models with enhanced capabilities.
    These models excel at complex reasoning tasks and support advanced parameters for better control.

    #### 🖥️ Parameters
        - `name` (`str`): The name of the input file to process, including its extension.
        - `model` (`str`): The identifier of the o3/o4-mini model (e.g., "o3-2025-04-16", "o4-mini").
        - `system_instruction` (`str`): Instructions provided to the system for processing.
        - `threaded` (`bool`, optional): If set to `True`, the function runs in a separate thread. Defaults to `False`.
        - `reasoning_effort` (`str`, optional): Reasoning effort level for o3 models ("low", "medium", "high"). Defaults to "medium".

    #### 🔄 Returns
        - `None`: The function does not return a value but writes the output to a file.

    #### ⚠️ Raises
        - `FileNotFoundError`: If the specified input file does not exist.
        - `Exception`: For any other errors encountered during processing.

    #### 📌 Notes
        - Optimized for o3 and o4-mini models with enhanced reasoning capabilities.
        - Supports reasoning effort control for o3 models to balance quality vs speed.
        - Uses increased max_completion_tokens for better output quality.
        - The generated report is saved in the `Reports` directory with the filename format: `{name}_o3_final_report.md`.

    #### 💡 Example

    >>> O3Report("patient_file.pdf", model="o3-2025-04-16", system_instruction="Analyze the medical data", threaded=True, reasoning_effort="high")

    """

    def wrapper(name: str):
        try:
            prompt = ""
            print(f"Starting O3/O4-mini Report with model: {model}")
            file_path = os.path.join(".", "Output", name)

            with open(file_path, "r", encoding="utf-8") as f:
                print(f"Reading file {name}")
                prompt = f.read()
                print("Requesting report generation with enhanced reasoning capabilities")

                # Enhanced parameters for o3/o4-mini models
                request_params = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_instruction
                        },
                        {
                            "role": "user",
                            "content": f"DADOS PARA PERICIA:{prompt}\n"
                        }
                    ],
                    "max_completion_tokens": 16384,  # Higher token limit for detailed reports
                    "temperature": 0.3,  # Lower temperature for more consistent outputs
                    "top_p": 0.9,
                    "presence_penalty": 0.1,
                    "frequency_penalty": 0.1,

                }

                # Add reasoning effort for o3 models
                if "o3" in model.lower() and "mini" not in model.lower():
                    request_params["reasoning_effort"] = reasoning_effort

                response = client.chat.completions.create(**request_params)

                content = response.choices[0].message.content

                # Enhanced metadata for o3/o4-mini reports
                metadata = f"# Relatório Médico Pericial\n"
                metadata += f"**Modelo:** {model}\n"
                metadata += f"**Tokens de Entrada:** {response.usage.prompt_tokens if response.usage else 'N/A'}\n"
                metadata += f"**Tokens de Saída:** {response.usage.completion_tokens if response.usage else 'N/A'}\n"
                metadata += f"**Data de Geração:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                metadata += "---\n\n"

                output_path = os.path.join(save_path, f"{name[:-3]}_o3_final_report.md")

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(metadata + content)

                print(f"Enhanced O3/O4-mini report generated and saved to {output_path}")

                # Display usage statistics if available
                if response.usage:
                    print(f"Token usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")

        except Exception as e:
            print(f"Error processing file {name} with {model}: {str(e)}")
            # Enhanced error logging for debugging
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")


    if threaded:
        threading.Thread(target=wrapper, args=(name,)).start()
    else:
        return wrapper(name)


def O3MiniTemplate(model: str, file_path: str, template_event, reasoning_effort: str = "medium") -> str:
    """### 📝 O3MiniTemplate
    Organizes text using OpenAI's o3-mini or o4-mini models with enhanced reasoning capabilities.
    These models excel at structured reasoning and logical organization tasks.

    #### 🖥️ Parameters
        - `model` (`str`): The o3-mini/o4-mini model identifier to be used for processing.
        - `file_path` (`str`): The path to the input file containing the text to be organized.
        - `template_event` (`Event`): A threading event to signal when the template is ready.
        - `reasoning_effort` (`str`, optional): Reasoning effort level for o3-mini ("low", "medium", "high"). Defaults to "medium".

    #### 🔄 Returns
        - `str`: The organized text in a structured JSON format.

    #### ⚠️ Raises
        - `FileNotFoundError`: If the specified file path does not exist.
        - `ValueError`: If the model identifier is invalid or unsupported.

    #### 📌 Notes
        - Optimized for o3-mini and o4-mini models with advanced reasoning.
        - Enhanced JSON validation and error handling.
        - Better token management for complex processing tasks.

    #### 💡 Example

    >>> O3MiniTemplate("o3-mini", "path/to/file.txt", template_event, reasoning_effort="high")

    """
    def wrapper(file_path: str, template_event: Event = None):
        try:
            print(f"Starting O3/O4-mini template generation with model: {model}")

            with open(file_path, "r", encoding="utf-8") as f:
                prompt = f.read()

            print(f"Processing with enhanced reasoning model: {model}")

            # Enhanced parameters for o3-mini/o4-mini
            request_params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": """
                        Você é um especialista em análise de processos judiciais previdenciários com capacidades avançadas de raciocínio.
                        Sua função é produzir um arquivo JSON estruturado e preciso conforme as instruções detalhadas.

                        Use suas capacidades de raciocínio aprimoradas para:
                        1. Analisar cuidadosamente todo o conteúdo processual
                        2. Identificar e extrair informações relevantes com precisão
                        3. Organizar os dados de forma lógica e estruturada
                        4. Validar a consistência das informações extraídas

                        ESTRUTURE AS STRINGS COM PARÁGRAFOS ADEQUADAMENTE SEPARADOS POR NOVAS LINHAS QUANDO ADEQUADO:

                        # INSTRUÇÕES DE PREENCHIMENTO:

                        ## ELEMENTOS SEM SEÇÃO ESPECÍFICA:
                        Devem ser preenchidos a partir das informações disponíveis no conteúdo:
                        - "FormacaoTecnicoProfissional": "ESCOLARIDADE"
                        - "UltimaAtividade": "ÚLTIMO TRABALHO REALIZADO"
                        - "TarefasExigidasUltimaAtividade": "MANTENHA O VALOR PADRÃO => Não especificado"
                        - "QuantoTempoUltimaAtividade": "MANTENHA O VALOR PADRÃO => Não especificado"
                        - "AteQuandoUltimaAtividade": "DATA DE TÉRMINO DA ÚLTIMA ATIVIDADE"
                        - "ExperienciasLaboraisAnt": "MANTENHA O VALOR PADRÃO => -------"
                        - "DCB": "ÚLTIMA DATA DE CESSAÇÃO DE BENEFÍCIO OU DER NA AUSÊNCIA DE BENEFÍCIO"
                        - "DID": "DATA DE INÍCIO DA DOENÇA"
                        - "DER": "DATA DE ENTRADA DO REQUERIMENTO"
                        - "DAP": "DATA DA ÚLTIMA ATIVIDADE PROFISSIONAL"

                        ## ELEMENTOS COM SEÇÃO PRÓPRIA:
                        Devem ter seu valor substituído pela INTEGRIDADE DO TEXTO DA SEÇÃO:
                        - "DocumentosMedicosAnalisados": MÁXIMO 10 itens (Mais recentes)
                        - "HistoricoAnamnese": Máximo de 100 palavras
                        - "ExameFisicoMental": ""
                        - "CONCLUSAO PERICIAL": Máximo de 70 palavras
                        - "ESCALA CIF": Se presente, deve ser copiada em sua integridade

                        <TEMPLATE DE JSON>
                        {
                            "json": {
                                "FormacaoTecnicoProfissional": "",
                                "UltimaAtividade": "",
                                "TarefasExigidasUltimaAtividade": "Não especificado",
                                "QuantoTempoUltimaAtividade": "Não especificado",
                                "AteQuandoUltimaAtividade": "",
                                "ExperienciasLaboraisAnt": "-------",
                                "MotivoIncapacidade": "(MÁXIMO 3 PALAVRAS)",
                                "HistoricoAnamnese": "",
                                "DocumentosMedicosAnalisados": "",
                                "DCB": "",
                                "DID": "",
                                "CausaProvavelDiagnostico": "Adquirida",
                                "CIF": "Existindo uma seção de escala CIF, deve ser copiada em sua integridade aqui"
                            }
                        }
                        </TEMPLATE DE JSON>

                        OBSERVAÇÕES IMPORTANTES:
                        - Na falta de DCB, preencha com a mesma data de DER
                        - Retorne APENAS o JSON válido, sem markdown ou outras formatações
                        - Use raciocínio cuidadoso para garantir precisão e consistência
                        """
                    },
                    {
                        "role": "user",
                        "content": f"CONTEÚDO PROCESSUAL PARA ANÁLISE: {prompt}"
                    }
                ],
                "max_completion_tokens": 8192,  # Higher limit for detailed analysis
                "temperature": 0.1,  # Very low for consistent JSON structure
                "top_p": 0.95,
                "response_format": {"type": "json_object"}  # Ensure JSON output
            }

            # Add reasoning effort for o3-mini models
            if "o3" in model.lower():
                request_params["reasoning_effort"] = reasoning_effort

            response = client.chat.completions.create(**request_params)
            content = response.choices[0].message.content

            # Enhanced JSON validation
            try:
                import json
                parsed_json = json.loads(content)
                # Re-format for consistency
                content = json.dumps(parsed_json, ensure_ascii=False, indent=4)
                print("JSON validation successful")
            except json.JSONDecodeError as e:
                print(f"JSON validation failed: {e}")
                print("Attempting to clean and validate JSON...")
                content = clean_and_validate_json(content)
                if not content:
                    raise ValueError("Failed to generate valid JSON after cleaning attempts")

            print("Saving enhanced template with metadata")

            # Add metadata header
            metadata = f"""// O3/O4-mini Enhanced Template
// Model: {model}
// Reasoning Effort: {reasoning_effort if 'o3' in model.lower() else 'N/A'}
// Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
// Tokens Used: {response.usage.total_tokens if response.usage else 'N/A'}

"""

            with open(os.path.join(".", "laudo_template.json"), "w", encoding="utf-8") as f:
                f.write(metadata + content)

            print("Enhanced O3/O4-mini template saved successfully")

            # Set the event to signal template is ready
            if template_event:
                template_event.set()

            return content

        except Exception as e:
            print(f"Error processing template with {model}: {str(e)}")
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")
            if template_event:
                template_event.set()  # Signal completion even on error
            return None

    threading.Thread(target=wrapper, args=(file_path, template_event)).start()

