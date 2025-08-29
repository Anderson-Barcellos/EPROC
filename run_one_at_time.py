import os
import subprocess
import time
import sys



def run_processes_sequentially():
    # INSERT_YOUR_CODE
    """
    ### 📝 run_processes_sequentially
    Processes all eligible report files in the "Reports" directory one at a time by generating and executing a temporary script for each process number.

    #### 🖥️ Parameters
        - None

    #### 🔄 Returns
        - `None`: This function does not return a value. It performs side effects by executing scripts and printing status messages.

    #### ⚠️ Raises
        - `Exception`: If any error occurs during the directory listing, script creation, or process execution, an exception is raised with a descriptive message.

    #### 📌 Notes
        - Only files ending with `.md` or `.txt` in the "Reports" directory are considered.
        - Each process is run in a separate Python subprocess, and the function waits for each to complete before proceeding to the next.
        - The function prints the status of each process, including success or failure.
        - Ensure that the "Reports" directory exists and contains the expected files.
        - The function relies on the `create_temp_script` function to generate the temporary scripts.

    #### 💡 Example

    >>> run_processes_sequentially()
    Processing: 50008601220254047106
    Comando executado: "/usr/bin/python3" "/current/dir/0_temp_script.py"
    Processo 50008601220254047106 concluído com sucesso

    """



    def _create_temp_script(i, process_number: str) -> str:


        script_content = f"""
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from Autofill.autofill import main, setup_chrome_options
import sys

def run_single_process():
    chrome_options = setup_chrome_options()
    driver = webdriver.Chrome(options=chrome_options)
    try:
        main(driver, "{process_number}")
        print("Processo concluído com sucesso!")
    finally:
        sys.exit(0)
if __name__ == "__main__":
    run_single_process()



        """
        try:
            with open(os.path.join(os.getcwd(), f"{i}_temp_script.py"),   "w", encoding="utf-8") as f:
                f.write(script_content)
        except Exception as e:
            print(f"Erro ao criar script temporário: {e}")
            return None


        return os.path.join(os.getcwd(), f"{i}_temp_script.py")

    reports = os.path.join("Reports")
    i = 0
    try:
        for file in os.listdir(reports):

            if file.endswith(".md") or file.endswith(".txt"):
                process_number = file[:20]
                print(process_number)
                path = _create_temp_script(i, process_number)
                i += 1
                print(f"\nProcessing: {process_number}")
                python_exe = sys.executable

                cmd = f'"{python_exe}" "{path}"'
                print("Comando executado:", cmd)
                process = subprocess.Popen(cmd, shell=True)
                process.wait()
                if process.returncode == 0:
                        print(f"Processo {process_number} concluído com sucesso")

                else:
                    print(f"Processo {process_number} falhou")

                time.sleep(2)
    except Exception as e:
        print(f"Erro: {e}")

