#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# SEQUENTIAL PROCESS RUNNER
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

import os
import subprocess
import time
import sys


def create_temp_script(i, process_number: str) -> str:
    r"""
    ### 📝 [create_temp_script]
    Creates a temporary Python script to run autofill for a single process.
    This function generates a standalone script that can be executed independently
    to process a single case number through the autofill system.

    ### 🖥️ Parameters
        - `i` (`int`): Sequential index for naming the temporary script file
        - `process_number` (`str`): The process number to be handled by the autofill system

    ### 🔄 Returns
        - `str`: Full path to the created temporary script file

    ### 💡 Example

    >>> script_path = create_temp_script(1, "50039062120254047102")
    >>> print(script_path)
    C:\path\to\1_temp_script.py

    ### 📚 Notes
    - The temporary script includes proper cleanup with sys.exit(0)
    - Uses the same Chrome options as the main autofill system
    r"""

    print(f"🔧 Creating temporary script for process: {process_number}")

    script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# TEMPORARY AUTOFILL SCRIPT - PROCESS: {process_number}
#■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from Autofill.autofill import main, setup_chrome_options
import sys



def run_single_process():
    '''Execute autofill for a single process number'''
    try:
        print("🚀 Starting Chrome driver setup...")
        chrome_options = setup_chrome_options()
        driver = webdriver.Chrome(options=chrome_options)

        try:
            print(f"📋 Processing: {process_number}")
            main(driver, "{process_number}")
            print("✅ Processo concluído com sucesso!")
        finally:
            print("🔒 Closing driver...")
            driver.quit()

    except Exception as e:
        print("❌ Error occurred during processing:")

        sys.exit(1)
    finally:
        sys.exit(0)


if __name__ == "__main__":
    run_single_process()
"""

    script_path = os.path.join(os.getcwd(), f"{i}_temp_script.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        print(f"✅ Temporary script created: {script_path}")
        return script_path

    except Exception as e:
        print(f"❌ Error creating temporary script: {e}")

        raise


def run_processes_sequentially():
    r"""
    ### 🔄 [run_processes_sequentially]
    Executes autofill processes sequentially for a predefined list of case numbers.
    Each process runs in isolation using a temporary script to prevent interference
    between different cases.

    ### 🔄 Returns
        - `None`: Function executes processes and prints status updates

    ### ⚠️ Raises
        - `Exception`: If critical errors occur during process execution

    ### 📚 Notes
    - Processes are executed one at a time to avoid resource conflicts
    - Each process gets a 2-second cooldown period
    - Temporary scripts are created and executed via subprocess
    r"""

    print("🏁 Starting sequential process execution...")

    reports = os.path.join(os.getcwd(), "Reports")
    i = 0
    n = len(os.listdir(reports))

    try:
        # ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
        # PROCESS LIST CONFIGURATION
        # ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

        md_list = [file.split("_")[0] for file in os.listdir(os.path.join(os.getcwd(), "Reports", "Processed"))]
        for file in os.listdir(reports):
            if file.split("-")[0] not in md_list and file.endswith(".md"):
                process_number = file.split("_")[0]

                print(f"\n{'='*60}")
                print(f"🔄 Processing [{i + 1}]: {process_number}")
                print(f"{'='*60}")

                # Create temporary script
                script_path = create_temp_script(i, process_number)
                i += 1

                # Execute the process
                python_exe = sys.executable
                cmd = f'"{python_exe}" "{script_path}"'

                print(f"💻 Executing command: {cmd}")

                try:
                    process = subprocess.Popen(cmd, shell=True)
                    process.wait()

                    if process.returncode == 0:
                        print(f"✅ Process {process_number} completed successfully")
                        processed_count += 1
                    else:
                        print(
                            f"❌ Process {process_number} failed with return code: {process.returncode}"
                        )

                except Exception as e:
                    print(f"❌ Error executing process {process_number}:")

                # Cleanup temporary script
                try:
                    if os.path.exists(script_path):
                        os.remove(script_path)
                        print(f"🗑️  Cleaned up temporary script: {script_path}")
                except Exception as e:
                    print(f"⚠️  Could not clean up temporary script: {e}")

                print(f"⏱️  Waiting 2 seconds before next process...")
                time.sleep(2)

        print(f"\n🎉 Sequential execution completed!")
    except Exception as e:
        print(f"❌ Critical error in sequential execution:")

        raise


if __name__ == "__main__":
    run_processes_sequentially()
