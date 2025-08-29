"""
### 🔄 Persistent Process Runner
Processes multiple EPROC cases using a single persistent Selenium instance for improved efficiency.
This module replaces the temporary script approach with direct function calls.

### 🖥️ Architecture
Uses the SeleniumManager singleton to maintain a single browser instance across all process executions.
"""

import os
import time
import traceback
import shutil
from typing import List, Tuple
from selenium_manager import selenium_manager
from Autofill.autofill_persistent import process_single_case
from Tools import WorkflowLogger

logger = WorkflowLogger("PersistentRunner")


def get_pending_processes() -> List[str]:
    """
    ### 📋 Get Pending Processes
    Retrieves list of processes that need to be filled from the Reports directory.

    ### 🖥️ Parameters
        - None

    ### 🔄 Returns
        - `List[str]`: List of process numbers to be processed

    ### 💡 Example

    >>> processes = get_pending_processes()
    >>> print(f"Found {len(processes)} processes to fill")

    ### 📚 Notes
    - Looks for .md and .txt files in Reports directory
    - Extracts first 20 characters as process number
    - Ignores files in Processed subfolder
    """
    reports_dir = os.path.join("Reports")
    processes = []

    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        return processes

    try:
        for file in os.listdir(reports_dir):
            file_path = os.path.join(reports_dir, file)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Process only markdown and text files
            if file.endswith(".md") or file.endswith(".txt"):
                process_number = file[:20]
                processes.append(process_number)
                logger.info(f"Found process to fill: {process_number}")

    except Exception as e:
        logger.error(f"Error scanning reports directory: {e}")

    return processes


def process_batch(processes: List[str], batch_size: int = 10) -> Tuple[List[str], List[str]]:
    """
    ### 📦 Process Batch
    Processes a batch of cases using the persistent Selenium instance.

    ### 🖥️ Parameters
        - `processes` (`List[str]`): List of process numbers to process
        - `batch_size` (`int`, optional): Number of processes per batch before driver reset. Default: 10

    ### 🔄 Returns
        - `Tuple[List[str], List[str]]`: Tuple of (successful_processes, failed_processes)

    ### ⚠️ Raises
        - `Exception`: If critical error occurs that prevents batch processing

    ### 💡 Example

    >>> processes = ["50008601220254047106", "50008602220254047106"]
    >>> success, failed = process_batch(processes, batch_size=5)
    >>> print(f"Processed: {len(success)}, Failed: {len(failed)}")

    ### 📚 Notes
    - Resets driver state between processes for stability
    - Performs full driver restart after each batch
    - Handles failures gracefully without stopping entire batch
    """
    successful = []
    failed = []

    # ■■■■■■■■■■■
    #  INITIALIZATION
    # ■■■■■■■■■■■
    logger.step("Batch Processing", f"Starting batch of {len(processes)} processes")
    print(f"[📦]: Processing batch of {len(processes)} processes")

    # Get driver and ensure login
    driver = selenium_manager.get_driver()
    if not selenium_manager.ensure_login():
        logger.error("Failed to login to EPROC system")
        raise Exception("Login failed - cannot proceed with batch processing")

    # ■■■■■■■■■■■
    #  PROCESS LOOP
    # ■■■■■■■■■■■
    for idx, process_number in enumerate(processes, 1):
        try:
            print(f"\n{'='*60}")
            print(f"[🔄]: Processing {idx}/{len(processes)}: {process_number}")
            print(f"{'='*60}")

            logger.info(f"Processing case {process_number} ({idx}/{len(processes)})")

            # Process single case
            success = process_single_case(driver, process_number)

            if success:
                successful.append(process_number)
                logger.success(f"Case {process_number} processed successfully")
                print(f"[✅]: Process {process_number} completed successfully")

                # Move report to Processed folder
                report_path = f"Reports/{process_number}_final_report.md"
                if os.path.exists(report_path):
                    processed_dir = os.path.join("Reports", "Processed")
                    os.makedirs(processed_dir, exist_ok=True)
                    shutil.move(
                        report_path,
                        os.path.join(processed_dir, f"{process_number}_final_report.md")
                    )
            else:
                failed.append(process_number)
                logger.warning(f"Case {process_number} processing failed")
                print(f"[❌]: Process {process_number} failed")

                # Move to Pending folder
                report_path = f"Reports/{process_number}_final_report.md"
                if os.path.exists(report_path):
                    pending_dir = os.path.join("Reports", "Pending")
                    os.makedirs(pending_dir, exist_ok=True)
                    shutil.move(
                        report_path,
                        os.path.join(pending_dir, f"{process_number}_final_report.md")
                    )

            # Reset driver state after each process
            selenium_manager.reset_driver()

            # Restart driver after batch_size processes for stability
            if idx % batch_size == 0 and idx < len(processes):
                print(f"[🔄]: Restarting driver after {batch_size} processes")
                logger.info(f"Restarting driver after batch of {batch_size}")
                selenium_manager.quit_driver()
                time.sleep(5)
                driver = selenium_manager.get_driver()
                selenium_manager.ensure_login()

            # Small delay between processes
            time.sleep(3)

        except Exception as e:
            failed.append(process_number)
            logger.error(f"Critical error processing {process_number}: {e}")
            print(f"[❌]: Critical error processing {process_number}: {e}")
            print(f"Stack trace: {traceback.format_exc()}")

            # Move to Pending folder
            report_path = f"Reports/{process_number}_final_report.md"
            if os.path.exists(report_path):
                pending_dir = os.path.join("Reports", "Pending")
                os.makedirs(pending_dir, exist_ok=True)
                shutil.move(
                    report_path,
                    os.path.join(pending_dir, f"{process_number}_final_report.md")
                )

    return successful, failed


def run_processes_sequentially_persistent():
    """
    ### 🚀 Run Processes Sequentially (Persistent)
    Main entry point for processing all pending reports using a persistent Selenium instance.

    ### 🖥️ Parameters
        - None

    ### 🔄 Returns
        - None

    ### 💡 Example

    >>> run_processes_sequentially_persistent()
    Processing: 50008601220254047106
    Process completed successfully
    All processes completed. Successful: 1, Failed: 0

    ### 📚 Notes
    - Maintains single browser instance for all processes
    - Automatically handles login once per session
    - Provides detailed progress and error reporting
    - Cleans up resources on completion or error
    """
    print("\n" + "="*70)
    print(" EPROC PERSISTENT PROCESS RUNNER ".center(70, "="))
    print("="*70 + "\n")

    logger.step("Session Start", "Initializing persistent process runner")

    try:
        # ■■■■■■■■■■■
        #  GET PROCESSES
        # ■■■■■■■■■■■
        processes = get_pending_processes()

        if not processes:
            print("[📭]: No processes found to fill")
            logger.info("No pending processes found")
            return

        print(f"[📋]: Found {len(processes)} processes to fill")
        logger.info(f"Found {len(processes)} processes to fill")

        # ■■■■■■■■■■■
        #  PROCESS BATCH
        # ■■■■■■■■■■■
        start_time = time.time()
        successful, failed = process_batch(processes)
        elapsed_time = time.time() - start_time

        # ■■■■■■■■■■■
        #  SUMMARY REPORT
        # ■■■■■■■■■■■
        print("\n" + "="*70)
        print(" PROCESSING SUMMARY ".center(70, "="))
        print("="*70)
        print(f"✅ Successful: {len(successful)} processes")
        print(f"❌ Failed: {len(failed)} processes")
        print(f"⏱️ Total time: {elapsed_time:.2f} seconds")
        print(f"⚡ Average time per process: {elapsed_time/len(processes):.2f} seconds")

        if failed:
            print(f"\n[⚠️]: Failed processes moved to Pending folder:")
            for process in failed:
                print(f"    - {process}")

        logger.info(f"""
        =============================================
        PROCESSING COMPLETE
        =============================================
        Total Processes: {len(processes)}
        Successful: {len(successful)}
        Failed: {len(failed)}
        Success Rate: {len(successful)/len(processes)*100:.2f}%
        Total Time: {elapsed_time:.2f}s
        Avg Time/Process: {elapsed_time/len(processes):.2f}s
        =============================================
        """)

    except Exception as e:
        logger.critical_error("Session failed", e)
        print(f"\n[❌]: Critical error during session: {e}")
        print(f"Stack trace: {traceback.format_exc()}")

    finally:
        # ■■■■■■■■■■■
        #  CLEANUP
        # ■■■■■■■■■■■
        print("\n[🧹]: Cleaning up resources...")
        selenium_manager.quit_driver()
        logger.success("Session complete - resources cleaned up")
        print("[✅]: Session complete")


# ■■■■■■■■■■■
#  MAIN EXECUTION
# ■■■■■■■■■■■
if __name__ == "__main__":
    run_processes_sequentially_persistent()
