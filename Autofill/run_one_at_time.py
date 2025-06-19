import os
import subprocess
import time
import sys

def create_temp_script(i, process_number: str) -> str:
    """### 📝 create_temp_script
    Generates a temporary Python script that executes the autofill process for a single process number. This function is typically used to isolate the execution of the autofill logic for each process in a separate script, which can then be run independently or in sequence.

    #### 🖥️ Parameters
        - `i` (`int`): The index or identifier for the temporary script file. Used to ensure unique filenames.
        - `process_number` (`str`): The process number to be processed by the generated script. Must be a valid string identifier for the process.

    #### 🔄 Returns
        - `str`: The absolute file path to the generated temporary Python script.

    #### ⚠️ Raises
        - `OSError`: If the script file cannot be created or written to disk.
        - `Exception`: For any other unexpected errors during script generation.

    #### 📌 Notes
        - The generated script will import necessary modules and invoke the `main` function from the `autofill` module.
        - The script is written to the current working directory and named using the provided index.
        - Ensure that the `autofill` module and its dependencies are available in the environment where the script will be executed.

    #### 💡 Example

    >>> create_temp_script(0, "50008601220254047106")
    '/path/to/current/dir/0_temp_script.py'
    """

    script_content = f"""

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from Autofill import main
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

    with open(os.path.join(os.getcwd(), f"{i}_temp_script.py"),   "w", encoding="utf-8") as f:
        f.write(script_content)

    return os.path.join(os.getcwd(), f"{i}_temp_script.py")

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
    reports = "Reports"
    i = 0
    try:
        for file in os.listdir(reports):

            if file.endswith(".md") or file.endswith(".txt"):
                process_number = file.split("_")[0]
                path = create_temp_script(i, process_number)
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


