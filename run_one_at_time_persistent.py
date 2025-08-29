"""
### 🔄 Run One at Time - Persistent Version
Pipeline that generates reports from Output files and fills forms using a persistent Selenium instance.
Only handles report generation and form filling - assumes OCR output already exists.
"""

import os
import time
import sys
import yaml
from selenium_manager import selenium_manager
from Autofill.autofill_persistent import process_single_case
from Models.models import Generate_Final_Report


def load_prompts():
    """
    ### 📄 Load Prompts
    Loads prompt configuration from YAML file.

    ### 🖥️ Parameters
        - None

    ### 🔄 Returns
        - `dict`: Loaded prompt data

    ### ⚠️ Raises
        - `FileNotFoundError`: If prompts file not found
        - `yaml.YAMLError`: If YAML parsing fails
    """
    try:
        with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        return data
    except Exception as e:
        print(f"[❌]: Error loading prompts: {e}")
        raise


def run_processes_sequentially(model: str = "gemini-2.5-pro", generate_reports: bool = True):
    """
    ### 📝 run_processes_sequentially
    Pipeline that generates reports from Output files and fills forms using a persistent Selenium instance.

    ### 🖥️ Parameters
        - `model` (`str`, optional): AI model to use for report generation. Default: "gemini-2.5-pro"
        - `generate_reports` (`bool`, optional): Whether to generate reports from Output files. Default: True

    ### 🔄 Returns
        - `None`: This function does not return a value. It performs side effects by processing files and printing status messages.

    ### ⚠️ Raises
        - `Exception`: If any error occurs during the directory listing or process execution, an exception is raised with a descriptive message.

    ### 📌 Notes
        - Step 1: If generate_reports is True, processes all files in Output/ to generate Reports/*.md
        - Step 2: Processes all .md or .txt files in the Reports/ directory for form filling
        - Uses a single persistent browser instance for all form filling (much faster)
        - Does NOT handle Download or OCR - assumes Output/ files already exist

    ### 💡 Example

    >>> # Generate reports and fill forms
    >>> run_processes_sequentially(model="gpt-4.1")

    >>> # Only fill forms (skip report generation)
    >>> run_processes_sequentially(generate_reports=False)
    """

    # ■■■■■■■■■■■
    #  INITIALIZATION
    # ■■■■■■■■■■■
    print("\n" + "="*70)
    print(" EPROC REPORT GENERATOR & FORM FILLER ".center(70, "="))
    print("="*70 + "\n")
    print("[ℹ️]: This tool processes in 2 steps:")
    print("     1. Generate reports from Output/ files (if enabled)")
    print("     2. Fill forms using Reports/ files")
    print()

    # ■■■■■■■■■■■
    #  PHASE 1: REPORT GENERATION
    # ■■■■■■■■■■■
    if generate_reports:
        print("[📄]: Starting report generation phase...")

        # Check if Output directory has files
        output_dir = os.path.join("Output")
        if not os.path.exists(output_dir):
            print(f"[❌]: Output directory not found")
            return

        output_files = [f for f in os.listdir(output_dir)
                       if os.path.isfile(os.path.join(output_dir, f))]

        if output_files:
            print(f"[📊]: Found {len(output_files)} files in Output directory")

            # Load prompts
            try:
                prompt_data = load_prompts()
                if "legacy_prompt" not in prompt_data:
                    print("[❌]: legacy_prompt not found in prompts file")
                    return

                print(f"[🤖]: Generating reports using {model}...")
                Generate_Final_Report(model, prompt_data["legacy_prompt"])
                print("[✅]: Report generation completed\n")

            except Exception as e:
                print(f"[❌]: Error generating reports: {e}")
                return
        else:
            print("[📭]: No files found in Output directory")
            print("[ℹ️]: Skipping report generation phase\n")

    # ■■■■■■■■■■■
    #  PHASE 2: FORM FILLING
    # ■■■■■■■■■■■
    print("[📝]: Starting form filling phase...")

    reports_dir = os.path.join("Reports")

    if not os.path.exists(reports_dir):
        print(f"[❌]: Directory '{reports_dir}' not found")
        return

    # Get list of files to process
    files_to_process = []
    try:
        for file in os.listdir(reports_dir):
            if file.endswith(".md") or file.endswith(".txt"):
                # Skip files in subdirectories
                file_path = os.path.join(reports_dir, file)
                if os.path.isfile(file_path):
                    process_number = file[:20]
                    files_to_process.append(process_number)
    except Exception as e:
        print(f"[❌]: Error listing directory: {e}")
        return

    if not files_to_process:
        print("[📭]: No .md or .txt files found in Reports directory")
        return

    print(f"[📋]: Found {len(files_to_process)} files to process")
    for num in files_to_process:
        print(f"    - {num}")
    print()

    # ■■■■■■■■■■■
    #  GET DRIVER AND LOGIN
    # ■■■■■■■■■■■
    print("[🌐]: Initializing persistent browser instance...")
    driver = selenium_manager.get_driver()

    print("[🔐]: Ensuring login...")
    if not selenium_manager.ensure_login():
        print("[❌]: Failed to login to EPROC")
        selenium_manager.quit_driver()
        return

    print("[✅]: Login successful, starting processing\n")

    # ■■■■■■■■■■■
    #  PROCESS EACH FILE
    # ■■■■■■■■■■■
    successful = 0
    failed = 0
    start_time = time.time()

    for i, process_number in enumerate(files_to_process, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(files_to_process)}: {process_number}")
        print(f"{'='*60}")

        try:
            # Process using persistent driver
            success = process_single_case(driver, process_number)

            if success:
                print(f"[✅]: Processo {process_number} concluído com sucesso")
                successful += 1
            else:
                print(f"[❌]: Processo {process_number} falhou")
                failed += 1

            # Reset driver state for next process
            selenium_manager.reset_driver()

            # Small delay between processes
            if i < len(files_to_process):
                print("[⏳]: Waiting 2 seconds before next process...")
                time.sleep(2)

        except Exception as e:
            print(f"[❌]: Error processing {process_number}: {e}")
            failed += 1

            # Try to recover by resetting driver
            try:
                selenium_manager.reset_driver()
            except:
                # If reset fails, recreate driver
                selenium_manager.quit_driver()
                driver = selenium_manager.get_driver()
                selenium_manager.ensure_login()

    # ■■■■■■■■■■■
    #  SUMMARY
    # ■■■■■■■■■■■
    elapsed_time = time.time() - start_time

    print("\n" + "="*60)
    print(" PROCESSING COMPLETE ".center(60, "="))
    print("="*60)
    print(f"✅ Successful: {successful} processes")
    print(f"❌ Failed: {failed} processes")
    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"⚡ Average time per process: {elapsed_time/len(files_to_process):.2f} seconds")
    print("="*60)

    # ■■■■■■■■■■■
    #  CLEANUP
    # ■■■■■■■■■■■
    print("\n[🧹]: Closing browser...")
    selenium_manager.quit_driver()
    print("[✅]: Browser closed successfully")


# ■■■■■■■■■■■
#  MAIN EXECUTION
# ■■■■■■■■■■■
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EPROC Report Generator and Form Filler")
    parser.add_argument("--model", type=str, default="gemini-2.5-pro",
                        help="AI model for report generation (default: gemini-2.5-pro)")
    parser.add_argument("--skip-reports", action="store_true",
                        help="Skip report generation and only fill forms")

    args = parser.parse_args()

    try:
        run_processes_sequentially(
            model=args.model,
            generate_reports=not args.skip_reports
        )
    except KeyboardInterrupt:
        print("\n\n[⚠️]: Process interrupted by user")
        print("[🧹]: Cleaning up...")
        selenium_manager.quit_driver()
        print("[✅]: Cleanup complete")
        sys.exit(0)
    except Exception as e:
        print(f"\n[❌]: Fatal error: {e}")
        selenium_manager.quit_driver()
        sys.exit(1)