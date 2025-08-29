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
import sys


def Recognize() -> bool:
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

                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        result = future.result()
                        total_text.append((page_num, result))

                    except Exception as e:
                        print(f"Error processing page {page_num}: {str(e)}")
            # Sort results by page number and join texts
            final_text = "".join(text for _, text in sorted(total_text))

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            return final_text
        finally:
            document.close()

    try:
        files = [f for f in os.listdir("Processos") if  f.endswith('.PDF')]

        if len(files) == 0:
            raise FileNotFoundError("No PDF files found in 'Processos' directory")

        else:
            progress_files = ProgressBar(len(files), "Processing files", "file")
            os.makedirs(os.path.join("Processos", "Processed"), exist_ok=True)
            # ■■■■■■■■■■■
            # PENDING SETUP
            # ■■■■■■■■■■■
            os.makedirs(os.path.join("Processos", "Pending"), exist_ok=True)
            os.makedirs(os.path.join("Output", "Pending"), exist_ok=True)

            for file in files:

                try:
                    file_path = os.path.join("Processos", file)
                    name =  file[3:23]
                    output_path = os.path.join("Output", f"{name}.txt")

                    _process_pdf(file_path, output_path)
                    if os.path.exists(output_path):
                        shutil.move(file_path, os.path.join("Processos", "Processed", f"2-{file}"))
                    else:
                        shutil.move(file_path, os.path.join("Processos", "Processed", f"1-{file}"))
                    progress_files.update(1)

                except Exception as e:
                    print(f"Error processing file {file}: {str(e)}")
                    # ■■■■■■■■■■■
                    # PENDING LOGIC - OCR ERROR
                    # ■■■■■■■■■■■
                    try:
                        file_path = os.path.join("Processos", file)
                        if os.path.exists(file_path):
                            shutil.move(
                                file_path, os.path.join("Processos", "Pending", file)
                            )
                            print(f"⚠️ PDF {file} movido para Pending (erro no OCR)")

                            # Criar arquivo de log do erro
                            error_log_path = os.path.join(
                                "Output", "Pending", f"{file[3:23]}_error.txt"
                            )
                            with open(error_log_path, "w", encoding="utf-8") as f:
                                f.write(f"Erro ao processar arquivo: {file}\n")
                                f.write(f"Mensagem de erro: {str(e)}\n")
                                f.write(
                                    f"Timestamp: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}\n"
                                )
                    except Exception as move_error:
                        print(f"Erro ao mover arquivo para Pending: {move_error}")

            progress_files.close()

    except Exception as e:
        print(f"Critical error in main process: {str(e)}")
        return False
    finally:
        print("OCR process completed successfully")
        return True
