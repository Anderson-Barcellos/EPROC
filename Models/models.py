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
import shutil
import base64
from google.genai import types
from google.genai.client import Client


# Add the parent directory to path so Python can find your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# GLOBALS

gemini_key:str | None = os.environ.get("GEMINI_API_KEY")
openai_key:str | None = os.environ.get("OPENAI_API_KEY")


if gemini_key:
    genai.configure(api_key=gemini_key) # type: ignore[attr-defined]
#!GENERATION CONFIG
generation_config = {
 "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 65536,
  "response_mime_type": "text/plain",
}

# Adicione uma variável global para controlar o estado do template
template_ready = Event()
client = OpenAI(api_key=openai_key)

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
                # Use os.path.splitext to drop the extension without leaving a trailing dot
                base_name = os.path.splitext(name)[0]
                output_path = os.path.join(".", "Reports", f"{base_name}_final_report.md")
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

def MiniTemplate(model: str, file_path: str, template_event) -> None:
    """### 📝 MiniTemplate
    Organizes text using the GPT-4o-mini model to generate a structured output.

    #### 🖥️ Parameters
    - `model` (`str`): The model identifier to be used for processing.
    - `file_path` (`str`): The path to the input file containing the text to be organized.
    - `template_event` (`Event`, optional): A threading event (Barrier) to signal when the template is ready. Defaults to None.

    #### 🔄 Returns
    - `None`: The function does not return a value but writes the output to a file.

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
    def wrapper(file_path: str, template_event: Event):
        try:
            print("Starting mini template")
            prompt = ""
            with open(file_path, "r", encoding="utf-8") as f:
                prompt = f.read()
            print(f"Awaking {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """
# SISTEMA DE ANÁLISE DE PROCESSO JUDICIAL PREVIDENCIÁRIO

## OBJETIVO
Você é um assistente especializado em análise de processos judiciais previdenciários. Sua tarefa é extrair informações específicas de um documento processual e organizá-las em formato JSON estruturado para integração com o sistema EPROC via Selenium.

## PROCESSO DE ANÁLISE (CHAIN OF THOUGHT)

### PASSO 1: LEITURA COMPREENSIVA
Primeiro, leia TODO o conteúdo processual identificando:
- Dados pessoais e profissionais do requerente
- Histórico médico e perícias
- Datas relevantes (DER, DID, DCB, DAP)
- Documentação médica anexada
- Conclusões periciais

### PASSO 2: CATEGORIZAÇÃO DAS INFORMAÇÕES
Classifique as informações encontradas em três categorias:

#### CATEGORIA A - EXTRAÇÃO DIRETA
Informações que devem ser extraídas diretamente do texto:
- **FormacaoTecnicoProfissional**: Escolaridade/formação do requerente
- **UltimaAtividade**: Último trabalho/ocupação exercida
- **AteQuandoUltimaAtividade**: Data de término da última atividade
- **DCB**: Data de Cessação do Benefício (se não houver, use a DER)
- **DID**: Data de Início da Doença
- **DER**: Data de Entrada do Requerimento
- **DAP**: Data da última Atividade Profissional
- **MotivoIncapacidade**: Resumo em até 3 palavras da causa principal

#### CATEGORIA B - SEÇÕES ESPECÍFICAS
Informações que possuem seções próprias no documento e devem ser copiadas integralmente:
- **DocumentosMedicosAnalisados**: Listar os 10 documentos médicos mais recentes
- **HistoricoAnamnese**: Resumir em até 100 palavras
- **ExameFisicoMental**: Copiar integralmente se existir
- **CONCLUSAO PERICIAL**: Resumir em até 70 palavras
- **CIF**: Se houver escala CIF, copiar integralmente

#### CATEGORIA C - VALORES PADRÃO
Manter valores padrão quando não houver informação:
- **TarefasExigidasUltimaAtividade**: "Não especificado"
- **QuantoTempoUltimaAtividade**: "Não especificado"
- **ExperienciasLaboraisAnt**: "-------"
- **CausaProvavelDiagnostico**: "Adquirida"

### PASSO 3: FORMATAÇÃO E VALIDAÇÃO

#### REGRAS DE FORMATAÇÃO:
1. **Parágrafos**: Use \n para separar parágrafos quando apropriado
2. **Datas**: Formato DD/MM/AAAA
3. **Documentos Médicos**:
   - Formato: [Número]. [Tipo de Documento]: Data: [DD/MM/AAAA] - Médico: [Nome] ([CRM])
   - CID: [Código] ([Descrição])
   - Informações: [Detalhes relevantes]
4. **Texto**: Sem formatação (sem markdown, HTML ou similares)

#### VALIDAÇÕES OBRIGATÓRIAS:
- ✓ Verificar se DCB existe; caso contrário, usar DER
- ✓ Limitar DocumentosMedicosAnalisados aos 10 mais recentes
- ✓ Respeitar limites de palavras onde especificado
- ✓ Garantir que todas as datas estejam no formato correto

### PASSO 4: ESTRUTURA JSON FINAL

Retorne APENAS o JSON abaixo, sem markdown ou formatação adicional:

{
    "json": {
        "FormacaoTecnicoProfissional": "[extrair do texto]",
        "UltimaAtividade": "[extrair do texto]",
        "TarefasExigidasUltimaAtividade": "Não especificado",
        "QuantoTempoUltimaAtividade": "Não especificado",
        "AteQuandoUltimaAtividade": "[extrair do texto]",
        "ExperienciasLaboraisAnt": "-------",
        "MotivoIncapacidade": "[máximo 3 palavras]",
        "HistoricoAnamnese": "[seção específica - máx 150 palavras]",
        "DocumentosMedicosAnalisados": "[seção específica - máx 10 itens]",
        "ExameFisicoMental": "[seção específica - integral]",
        "CONCLUSAO PERICIAL": "[seção específica - máx 70 palavras]",
        "DCB": "[extrair ou usar DER]",
        "DID": "[extrair do texto]",
        "DER": "[extrair do texto]",
        "DAP": "[extrair do texto]",
        "CausaProvavelDiagnostico": "Adquirida",
        "CIF": "[copiar escala CIF se existir]"
    }
}

## EXEMPLOS DE REFERÊNCIA

### Exemplo de DocumentosMedicosAnalisados:
"DocumentosMedicosAnalisados": "1. Receituário Médico: Data: 22/08/2024 - Médico: Dr. Hilton Silva (CRM RS12345)\nCID: F33 (Transtorno depressivo recorrente)\nInformações: Paciente necessita acompanhamento com cuidador. Prescrição de 180 dias.\n\n2. Laudo Psiquiátrico: Data: 15/07/2024 - Médico: Dra. Maria Santos (CRM RS54321)\nCID: F41.1 (Transtorno de ansiedade generalizada)\nInformações: Paciente apresenta sintomas ansiosos graves com prejuízo funcional."

### Exemplo de HistoricoAnamnese:
"HistoricoAnamnese": "Paciente relata início dos sintomas depressivos há 3 anos, com piora progressiva. Refere tristeza profunda, anedonia, insônia e ideação suicida. Tentou retornar ao trabalho em duas ocasiões sem sucesso. Faz acompanhamento psiquiátrico regular no CAPS desde 2022."

## INSTRUÇÕES FINAIS
- Analise metodicamente cada seção do documento
- Extraia apenas informações explicitamente presentes
- Mantenha a objetividade e precisão
- Retorne APENAS o JSON, sem texto adicional

                        """
                    },
                    {
                        "role": "user",
                        "content": f"CONTEUDO PROCESSUAL: {prompt}",
                    },
                ],
                temperature=0.3,
            )
            content:str | None = response.choices[0].message.content
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
            # Use os.path.splitext to drop the extension without leaving a trailing dot
            base_name = os.path.splitext(name)[0]
            output_path = os.path.join(".", "Reports", f"{base_name}_final_report.md")
            print(f"Output will be saved to: {output_path}")

            #!SENDING REQUEST TO THE GEMINI MODEL
            print("Sending request to Gemini model...")
            start_time = time.time()
            try:
                print("Generating content...")
                response = model.generate_content( f"DOCUMENTO:{content}")
                if response:
                    print("Content generated. Processing response...")
                    answer = response.text
                    print(f"Writing response to file: {output_path}")
                    with open( os.path.join(".", "Reports", f"{base_name}_final_report.md"), "w", encoding="utf-8") as f:
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

def Generate_Final_Report(model, system_instruction, reasoning_effort: str = "medium")-> None:
    """
    ### 📄 Generate_Final_Report
    Coordinates the creation of a final report for each file in the 'Output' directory using the specified model and system instructions. The function supports multiple model types (e.g., 'gemini', 'gpt', 'o1', 'o3', 'o4-mini') and moves processed files to the 'Processed' subdirectory. This function is intended for batch processing of output files and assumes the presence of required report generation classes and a valid directory structure.

    ### 🖥️ Parameters
        - `model` (`str`): The name of the model to use for report generation. Must include one of the supported model identifiers (e.g., 'gemini', 'gpt', 'o1', 'o3', 'o4-mini').
        - `system_instruction` (`str`): Instruction string that guides the report generation process for the selected model.
        - `reasoning_effort` (`str`, optional): The reasoning effort level for `GPT reasoning models - "o" series. Defaults to "medium"`.

    ### 🔄 Returns
        - `None`: This function performs file operations and report generation but does not return a value.

    ### ⚠️ Raises
        - `Exception`: Raised if an error occurs during report generation or file movement, with a descriptive message indicating the context and source of the error.

    ### 💡 Example

    >>> Generate_Final_Report('gemini', 'Summarize the case details')
    # Processes all files in the 'Output' directory using the Gemini model and moves them to 'Processed'.
    """


    try:
        output_items = [item for item in os.listdir("Output") if os.path.isfile(os.path.join("Output", item))]

        if output_items:
            if "gemini" in model:
                for name in output_items:
                     GeminiReport(name, model, system_instruction)
                     shutil.move(os.path.join("Output", name), os.path.join("Output", "Processed", name))

            elif "gpt" in model or "o1" in model or "o3" in model or "o4-mini" in model:
                for name in output_items:
                    GPTReport(name, model, system_instruction, reasoning_effort)
                    shutil.move(os.path.join("Output", name), os.path.join("Output", "Processed", name))
    except Exception as e:
        print(f"Erro Detectado: {e}")

def Gemini_PDF_Report(model:str, system_instruction:str, file:str)-> None:
    """
    ### 📄 Gemini_Generate_Report
    Generates a final report for a given file using the Gemini model.
    """
    parts = []
    name: str = file.split("-")[1]
    print("File Name is: ", name)

    with open(file, "rb") as f:
        parts.append(types.Part.from_bytes(
        mime_type="application/pdf",
        data=base64.b64encode(f.read()).decode("utf-8"),
        ))

    try:
        print("Sending request to Gemini model...")
        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=0.6,
            thinking_config = types.ThinkingConfig(
                thinking_budget=32768,
            ),
            response_mime_type="text/plain",
            system_instruction=system_instruction,
        )
        gemini_client = Client(api_key=gemini_key)

        response = gemini_client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        if response:
            print("Response received from Gemini model...")
            answer = response.text
            with open(os.path.join(".", "Reports", f"{name}_final_report.md"), "w", encoding="utf-8") as f:
                f.write(markdown_to_text(answer))
            print("Report saved successfully")

    except Exception as e:
        print(f"Error generating report: {str(e)}")
