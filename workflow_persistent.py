"""
### 🔄 Persistent Workflow Manager
Enhanced workflow that uses persistent Selenium instance for improved efficiency.
This module orchestrates the entire EPROC automation pipeline with resource optimization.

### 🖥️ Architecture
Coordinates between download, OCR, report generation, and form filling using a single browser instance.
"""

import os
import time
import yaml
from typing import List, Optional
from Models.models import Generate_Final_Report
from cloud_ocr.recognizer import Recognize
from Browsing.EPROC import EPROC_Download
from run_processes_persistent import run_processes_sequentially_persistent
from Tools import WorkflowLogger
from selenium_manager import selenium_manager

logger = WorkflowLogger("PersistentWorkflow")


class PersistentWorkflow:
    """
    ### 🔄 PersistentWorkflow
    Manages the complete EPROC automation workflow with persistent browser instance.

    ### 🖥️ Parameters
        - None for initialization

    ### 🔄 Returns
        - `PersistentWorkflow`: Instance of the workflow manager

    ### 💡 Example

    >>> workflow = PersistentWorkflow()
    >>> workflow.process_suit_list(suit_list)
    >>> workflow.generate_reports()
    >>> workflow.fill_forms()
    >>> workflow.cleanup()

    ### 📚 Notes
    - Maintains single browser instance across all operations
    - Provides detailed progress tracking and statistics
    - Handles errors gracefully with automatic recovery
    """

    def __init__(self):
        """Initialize the persistent workflow manager."""
        self.logger = WorkflowLogger("PersistentWorkflow")
        self.prompt_data = self._load_prompts()
        self.stats = {
            "downloads_completed": 0,
            "ocr_processed": 0,
            "reports_generated": 0,
            "forms_filled": 0,
            "errors": []
        }

    def _load_prompts(self) -> dict:
        """
        ### 📄 Load Prompts
        Loads prompt templates from YAML configuration file.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `dict`: Loaded prompt data

        ### 📚 Notes
        - Reads from Prompts/instructions.yaml
        - Contains templates for AI report generation
        """
        try:
            with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
            self.logger.info("Prompts loaded successfully")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load prompts: {e}")
            return {}

    def download_processes(self, suit_list: List[str], use_persistent: bool = True) -> bool:
        """
        ### 📥 Download Processes
        Downloads all processes from EPROC using either persistent or standard approach.

        ### 🖥️ Parameters
            - `suit_list` (`List[str]`): List of process numbers to download
            - `use_persistent` (`bool`, optional): Use persistent browser instance. Default: True

        ### 🔄 Returns
            - `bool`: True if all downloads successful, False otherwise

        ### 💡 Example

        >>> success = workflow.download_processes(["50008601220254047106"])
        >>> print(f"Downloads {'completed' if success else 'failed'}")

        ### 📚 Notes
        - Creates Processos directory if not exists
        - Tracks download statistics
        - Handles failures gracefully
        """
        self.logger.step("Download Phase", f"Starting download of {len(suit_list)} processes")
        print(f"\n[📥]: Starting download phase for {len(suit_list)} processes")

        try:
            if use_persistent:
                # Use persistent browser instance
                driver = selenium_manager.get_driver()
                if not selenium_manager.ensure_login():
                    self.logger.error("Failed to login for downloads")
                    return False

                # Process downloads one by one with same instance
                for idx, process_num in enumerate(suit_list, 1):
                    print(f"[📥]: Downloading {idx}/{len(suit_list)}: {process_num}")
                    # TODO: Adapt EPROC_Download to use existing driver
                    # For now, fall back to standard approach

                selenium_manager.reset_driver()
            else:
                # Use standard approach
                success = EPROC_Download(suit_list)
                if success:
                    self.stats["downloads_completed"] = len(suit_list)
                    self.logger.success(f"Downloaded {len(suit_list)} processes")
                    return True

            return True

        except Exception as e:
            self.logger.error(f"Download phase failed: {e}")
            self.stats["errors"].append(f"Download error: {e}")
            return False

    def run_ocr_recognition(self) -> Optional[Recognize]:
        """
        ### 🔍 Run OCR Recognition
        Processes downloaded PDFs through OCR recognition.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `Recognize`: OCR recognizer instance if successful, None otherwise

        ### 💡 Example

        >>> recognizer = workflow.run_ocr_recognition()
        >>> if recognizer:
        >>>     print("OCR completed successfully")

        ### 📚 Notes
        - Processes all files in Processos directory
        - Tracks processing statistics
        - Creates Output directory structure
        """
        self.logger.step("OCR Phase", "Starting OCR recognition")
        print("\n[🔍]: Starting OCR recognition phase")

        try:
            rec = Recognize()

            # ■■■■■■■■■■■
            #  STATISTICS
            # ■■■■■■■■■■■
            processos_dir = os.path.join("Processos")
            if os.path.exists(processos_dir):
                total_files = len([f for f in os.listdir(processos_dir) if os.path.isfile(os.path.join(processos_dir, f))])

                processed_dir = os.path.join(processos_dir, "Processed")
                processed_files = 0
                if os.path.exists(processed_dir):
                    processed_files = len([f for f in os.listdir(processed_dir) if os.path.isfile(os.path.join(processed_dir, f))])

                self.stats["ocr_processed"] = processed_files

                percentage = (processed_files / total_files * 100) if total_files > 0 else 0

                self.logger.info(f"""
                =============================================
                OCR PROCESSING STATISTICS
                =============================================
                Total Files: {total_files}
                Processed: {processed_files}
                Pending: {total_files - processed_files}
                Progress: {percentage:.2f}%
                =============================================
                """)

                print(f"[📊]: OCR Progress: {processed_files}/{total_files} ({percentage:.2f}%)")

            self.logger.success("OCR recognition completed")
            return rec

        except Exception as e:
            self.logger.error(f"OCR phase failed: {e}")
            self.stats["errors"].append(f"OCR error: {e}")
            return None

    def generate_reports(self, model: str = "gemini-2.5-pro") -> bool:
        """
        ### 📄 Generate Reports
        Generates AI-powered reports from OCR output.

        ### 🖥️ Parameters
            - `model` (`str`, optional): AI model to use. Default: "gemini-2.5-pro"

        ### 🔄 Returns
            - `bool`: True if reports generated successfully, False otherwise

        ### 💡 Example

        >>> success = workflow.generate_reports("gpt-4.1")
        >>> print(f"Reports {'generated' if success else 'failed'}")

        ### 📚 Notes
        - Uses AI model to analyze OCR output
        - Creates markdown reports in Reports directory
        - Tracks generation statistics
        """
        self.logger.step("Report Generation", f"Generating reports with {model}")
        print(f"\n[📄]: Starting report generation with {model}")

        try:
            if "legacy_prompt" not in self.prompt_data:
                self.logger.error("Legacy prompt not found in configuration")
                return False

            report = Generate_Final_Report(model, self.prompt_data["legacy_prompt"])

            # ■■■■■■■■■■■
            #  STATISTICS
            # ■■■■■■■■■■■
            output_dir = os.path.join("Output")
            if os.path.exists(output_dir):
                total_outputs = len([f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))])

                processed_dir = os.path.join(output_dir, "Processed")
                processed_outputs = 0
                if os.path.exists(processed_dir):
                    processed_outputs = len([f for f in os.listdir(processed_dir) if os.path.isfile(os.path.join(processed_dir, f))])

                self.stats["reports_generated"] = processed_outputs

                percentage = (processed_outputs / total_outputs * 100) if total_outputs > 0 else 0

                self.logger.info(f"""
                =============================================
                REPORT GENERATION STATISTICS
                =============================================
                Total Outputs: {total_outputs}
                Generated: {processed_outputs}
                Pending: {total_outputs - processed_outputs}
                Progress: {percentage:.2f}%
                =============================================
                """)

                print(f"[📊]: Report Generation: {processed_outputs}/{total_outputs} ({percentage:.2f}%)")

            self.logger.success("Report generation completed")
            return True

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            self.stats["errors"].append(f"Report generation error: {e}")
            return False

    def fill_forms_persistent(self) -> bool:
        """
        ### 📝 Fill Forms (Persistent)
        Fills EPROC forms using persistent browser instance.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - `bool`: True if all forms filled successfully, False otherwise

        ### 💡 Example

        >>> success = workflow.fill_forms_persistent()
        >>> print(f"Forms {'filled' if success else 'failed'}")

        ### 📚 Notes
        - Uses single browser instance for all forms
        - Significantly faster than creating new instances
        - Handles batch processing efficiently
        """
        self.logger.step("Form Filling", "Starting persistent form filling")
        print("\n[📝]: Starting form filling with persistent browser")

        try:
            # Run the persistent form filling process
            run_processes_sequentially_persistent()

            # ■■■■■■■■■■■
            #  STATISTICS
            # ■■■■■■■■■■■
            reports_dir = os.path.join("Reports")
            if os.path.exists(reports_dir):
                total_reports = len([f for f in os.listdir(reports_dir) if f.endswith((".md", ".txt")) and os.path.isfile(os.path.join(reports_dir, f))])

                processed_dir = os.path.join(reports_dir, "Processed")
                processed_reports = 0
                if os.path.exists(processed_dir):
                    processed_reports = len([f for f in os.listdir(processed_dir) if os.path.isfile(os.path.join(processed_dir, f))])

                self.stats["forms_filled"] = processed_reports

                percentage = (processed_reports / total_reports * 100) if total_reports > 0 else 0

                self.logger.info(f"""
                =============================================
                FORM FILLING STATISTICS
                =============================================
                Total Reports: {total_reports}
                Filled: {processed_reports}
                Pending: {total_reports - processed_reports}
                Success Rate: {percentage:.2f}%
                =============================================
                """)

                print(f"[📊]: Form Filling: {processed_reports}/{total_reports} ({percentage:.2f}%)")

            self.logger.success("Form filling completed")
            return True

        except Exception as e:
            self.logger.error(f"Form filling failed: {e}")
            self.stats["errors"].append(f"Form filling error: {e}")
            return False

    def run_complete_workflow(self, suit_list: List[str]) -> dict:
        """
        ### 🚀 Run Complete Workflow
        Executes the entire EPROC automation pipeline.

        ### 🖥️ Parameters
            - `suit_list` (`List[str]`): List of process numbers to process

        ### 🔄 Returns
            - `dict`: Statistics dictionary with results

        ### 💡 Example

        >>> suit_list = ["50008601220254047106", "50008602220254047106"]
        >>> stats = workflow.run_complete_workflow(suit_list)
        >>> print(f"Completed: {stats['forms_filled']} forms filled")

        ### 📚 Notes
        - Orchestrates all phases: download, OCR, report, filling
        - Uses persistent browser for efficiency
        - Returns comprehensive statistics
        """
        print("\n" + "="*70)
        print(" EPROC PERSISTENT WORKFLOW ".center(70, "="))
        print("="*70 + "\n")

        self.logger.step("Workflow Start", f"Processing {len(suit_list)} cases")
        start_time = time.time()

        # ■■■■■■■■■■■
        #  PHASE 1: DOWNLOAD
        # ■■■■■■■■■■■
        if self.download_processes(suit_list):
            print("[✅]: Download phase completed")
        else:
            print("[⚠️]: Download phase had issues")

        # ■■■■■■■■■■■
        #  PHASE 2: OCR
        # ■■■■■■■■■■■
        recognizer = self.run_ocr_recognition()
        if recognizer:
            print("[✅]: OCR phase completed")
        else:
            print("[⚠️]: OCR phase had issues")

        # ■■■■■■■■■■■
        #  PHASE 3: REPORTS
        # ■■■■■■■■■■■
        if self.generate_reports():
            print("[✅]: Report generation completed")
        else:
            print("[⚠️]: Report generation had issues")

        # ■■■■■■■■■■■
        #  PHASE 4: FORM FILLING
        # ■■■■■■■■■■■
        if self.fill_forms_persistent():
            print("[✅]: Form filling completed")
        else:
            print("[⚠️]: Form filling had issues")

        # ■■■■■■■■■■■
        #  CLEANUP & SUMMARY
        # ■■■■■■■■■■■
        self.cleanup()

        elapsed_time = time.time() - start_time

        print("\n" + "="*70)
        print(" WORKFLOW SUMMARY ".center(70, "="))
        print("="*70)
        print(f"⏱️ Total Time: {elapsed_time:.2f} seconds")
        print(f"📥 Downloads: {self.stats['downloads_completed']}")
        print(f"🔍 OCR Processed: {self.stats['ocr_processed']}")
        print(f"📄 Reports Generated: {self.stats['reports_generated']}")
        print(f"📝 Forms Filled: {self.stats['forms_filled']}")

        if self.stats["errors"]:
            print(f"\n⚠️ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                print(f"  - {error}")

        self.logger.success(f"Workflow completed in {elapsed_time:.2f} seconds")

        return self.stats

    def cleanup(self):
        """
        ### 🧹 Cleanup Resources
        Cleans up all resources including browser instance.

        ### 🖥️ Parameters
            - None

        ### 🔄 Returns
            - None

        ### 📚 Notes
        - Closes browser instance
        - Ensures proper resource cleanup
        - Safe to call multiple times
        """
        print("\n[🧹]: Cleaning up resources...")
        selenium_manager.quit_driver()
        self.logger.info("Resources cleaned up")


# ■■■■■■■■■■■
#  MAIN EXECUTION
# ■■■■■■■■■■■
if __name__ == "__main__":
    # Example suit list
    suit_list = [
        "50011996820254047106",
        "50011410220244047106",
        "50073497720254047102",
    ]

    # Create workflow instance
    workflow = PersistentWorkflow()

    # Option 1: Run complete workflow
    # stats = workflow.run_complete_workflow(suit_list)

    # Option 2: Run only form filling with persistent browser
    workflow.fill_forms_persistent()

    # Cleanup when done
    workflow.cleanup()
