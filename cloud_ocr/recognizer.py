"""
### 📝 Recognize Module
This module is designed to perform Optical Character Recognition (OCR) on PDF documents using a multi-threaded approach. It leverages the `fitz` library for PDF handling and the `concurrent.futures` module for parallel processing, ensuring efficient and fast processing of large documents.

"""

import fitz
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from cloud_ocr import OCR
from Tools import ProgressBar
import shutil


def _process_page(page, page_num):
    """
    Process a single page with OCR
    """
    try:
        return OCR(page, page_num)
    except Exception as e:
        print(f"Error processing page {page_num}: {str(e)}")


def _process_pdf(file_path: str, output_path: str, max_workers: int =int(os.cpu_count()*2),) -> str:
    """
    Process a single PDF file and perform OCR on all its pages using multiple threads
    """
    total_text = []  # Using list for thread-safe append
    document = fitz.open(file_path)

    try:

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pages to thread pool
            future_to_page = {}
            for page_num in range(len(document)):
                future = executor.submit(_process_page, document[page_num], page_num)
                future_to_page[future] = page_num

            # Collect results as they complete
            progress_pages = ProgressBar(len(document), "Processing pages", "pages")
            for future in as_completed(future_to_page):
                progress_pages.update(1)
                page_num = future_to_page[future]
                try:
                    result = future.result()
                    total_text.append((page_num, result))

                except Exception as e:
                    print(f"Error processing page {page_num}: {str(e)}")
            progress_pages.close()
        # Sort results by page number and join texts
        final_text = "".join(text for _, text in sorted(total_text))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_text)

        return final_text
    finally:
        document.close()

def Recognize() -> None:
    """
    ### 📝 Recognize
    Coordinate the OCR process for PDF files located in the 'Processos' directory.

    #### 🖥️ Parameters
    - None

    #### 🔄 Returns
    - `None`: This function does not return any value. It processes files and writes output to the 'Output' directory.

    #### ⚠️ Raises
    - `FileNotFoundError`: If the 'Processos' directory does not exist or contains no PDF files.
    - `Exception`: For any critical errors encountered during the main process.

    #### 📌 Notes
    - The function processes each PDF file, performs OCR, and moves processed files to a 'Processed' subdirectory.
    - Utilizes a progress bar to indicate the processing status of files.
    - Ensures that the output directory structure is created if it does not exist.

    #### 💡 Example
    >>> Recognize()
    # Processes all PDF files in 'Processos' and outputs text files to 'Output'.
    """
    try:
        if not os.path.exists("Processos"):
            raise FileNotFoundError("Directory 'Processos' not found")
        files = [f for f in os.listdir("Processos") if f.lower().endswith('.pdf')]

        if len(files) == 0:
            raise FileNotFoundError("No PDF files found in 'Processos' directory")

        else:
            progress_files = ProgressBar(len(files), "Processing files", "file")
            os.makedirs(os.path.join("Processos", "Processed"), exist_ok=True)

            os.makedirs(os.path.join("Processos", "Processed"), exist_ok=True)

            for file in files:
                try:
                    name, _ = os.path.splitext(file)  # Extract filename without extension
                    file_path = os.path.join("Processos", file)
                    output_path = os.path.join("Output", f"{name}.txt")

                    _process_pdf(file_path, output_path)
                    shutil.move(
                        file_path,
                        os.path.join("Processos", "Processed", f"{name}.pdf"),
                    )

                    _process_pdf(file_path, output_path)
                    dest = os.path.join("Processos", "Processed", f"{name}.pdf")
                    shutil.move(file_path, dest)
                    progress_files.update(1)

                except Exception as e:
                    print(f"Error processing file {file}: {str(e)}")
            progress_files.close()


    except Exception as e:
        print(f"Critical error in main process: {str(e)}")
        return False
    finally:
        print("OCR process completed successfully")
        return True

system_instruction = """
"Você atuará como perito médico judicial, encarregado de analisar e resumir documentos médicos referentes a um processo previdenciário, objetivando a elaboração de um laudo técnico completo, preciso e coerente, que realce os aspectos periciais relevantes. Use as informações do documento disponibilizado e siga com rigor as instruções a seguir:

Resumo Detalhado do Documento:
-Demanda Processual,
-Data de início da doença (DID),
-data de cessação do benefício (DCB),
-data de entrada do requerimento (DER) e
-data da última atividade profissional, incluindo detalhes adicionais pertinentes ao contexto pericial.

Histórico Clínico do Autor
Sua tarefa consiste em gerar um parágrafo estruturado, impessoal e profissional, simulando o estilo do perito médico ao redigir o corpo do laudo no dia da avaliação pericial. Utilize obrigatoriamente as informações específicas fornecidas pelo usuário sobre o quadro clínico do paciente, a impressão geral observada pelo perito e as possíveis causas consideradas pertinentes ao caso. Além disso, com base nas doenças mencionadas pelo perito, inclua brevemente os principais sinais e sintomas geralmente associados a essas condições de maneira genérica, enriquecendo o contexto clínico descrito. A narrativa deverá ser coesa, clara, objetiva e não ultrapassar 250 palavras. Redija o laudo com foco principal no quadro psiquiátrico, sua proporcionalidade entre os achados descritos pelo usuário e dados de documentos se presentes. Limite-se a descrever sintomas clínicos apresentados que podem  ocasionar secundariamente condições psiquiátricas. Destaque-se genericamente sintomas psiquiátricos. Nunca utilize nomes próprios. Adapta a linguagem para o ambiente jurídico.


Documentos Médicos (Seção Mais Importante)
Organize, de forma enumerada, cada atestado médico, informando o nome do profissional emissor, a data do documento, o CID e as principais informações clínicas. Verifique se cada atestado reúne as informações básicas para subsidiar a perícia, lembrando que avaliações feitas pelo INSS não devem ser consideradas documentos médicos.

Conclusão Pericial
Fundamente, com objetividade, se o autor apresenta incapacidade total ou parcial, temporária ou permanente, sempre relacionando a conclusão aos achados clínicos e aos dados coletados ao longo da análise."
"""


