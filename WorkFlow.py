
import os
import time
from Models.models import Generate_Final_Report
from Browsing.EPROC import EPROC_Download
import yaml
from cloud_ocr.recognizer import Recognize
from run_one_at_time import run_processes_sequentially


def load_PROMPT() -> dict | None:
    """
    ### 📝 load_PROMPT
    Loads the prompt instructions from a YAML file located at 'Prompts/instructions.yaml'. This function is responsible for reading
    and parsing the YAML file containing prompt templates or instructions required for the workflow.

    ### 🖥️ Parameters
        - None

    ### 🔄 Returns
        - `dict`: A dictionary containing the parsed YAML data with prompt instructions. The structure depends on the YAML file content.

    ### 💡 Example

    >>> data = load_PROMPT()
    >>> print(data["legacy_prompt"])
    Some legacy prompt text

    ### 📚 Notes
    - The function expects the file 'Prompts/instructions.yaml' to exist and be properly formatted.
    - Raises `FileNotFoundError` if the file does not exist.
    - Raises `yaml.YAMLError` if the YAML file is malformed.
    - The returned dictionary is used to access specific prompts by key.
    """
    try:
        data = None
        if not os.path.exists("Prompts/instructions.yaml"):
            raise FileNotFoundError(
                "Prompts/instructions.yaml not found. The file is required to load the prompts."
            )
        with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        return data
    except Exception as e:
        print(f"[❌]: Error: {e}")
        return data


def run_autofill_processing() -> dict | None:
    """
    ### 🤖 run_autofill_processing
    Executes the autofill processing system using either the enhanced version or legacy fallback.
    This function handles the sequential processing of generated reports for form filling automation.

    ### 🔄 Returns
        - `dict`: Processing statistics including completed, failed, and total processes.
        - `None`: If processing fails or no system is available.

    ### ⚠️ Raises
        - `Exception`: If critical errors occur during processing execution.

    ### 💡 Example

        >>> stats = run_autofill_processing()
        >>> print(f"Completed: {stats['completed']}/{stats['total']}")

    ### 📚 Notes
        - Automatically selects enhanced system if available, otherwise uses legacy version
        - Provides comprehensive error handling and logging
        - Returns detailed processing statistics for monitoring
    """
    print("[🤖]: starting autofill processing system")

    try:
        if True:
            print("[🚀]: using enhanced sequential processing system")
            print("Starting enhanced autofill processing")

            # Execute enhanced processing
            stats = run_processes_sequentially()

            if stats:
                print(f"Enhanced processing completed: {stats}")
                print(f"[📊]: enhanced processing completed")
                print(
                    f"[✅]: {stats.get('completed', 0)} processes completed successfully"
                )
                print(f"[❌]: {stats.get('failed', 0)} processes failed")
                print(f"[📈]: {stats.get('total', 0)} total processes")
                return stats
            else:
                print("Enhanced processing returned no statistics")
                print("[⚠️]: enhanced processing completed but returned no statistics")
                return None

        else:
            print("[🔄]: using legacy sequential processing system")
            print("Starting legacy autofill processing")

            # Execute legacy processing
            run_processes_sequentially()

            print("Legacy processing completed")
            print("[✅]: legacy processing completed")

            # Legacy doesn't return stats, so we return a basic structure
            return {"status": "completed", "system": "legacy"}

    except Exception as e:
        error_msg = f"Autofill processing failed: {str(e)}"
        print(error_msg)
        print(f"[💥]: {error_msg}")
        raise


def execute_complete_workflow(model: str = "gemini-2.5-pro") -> bool:
    """
    ### 🎯 execute_complete_workflow
    Executes the complete EPROC workflow: report generation followed by automated form filling.
    This function orchestrates the entire process from AI report generation to browser automation.

    ### 🖥️ Parameters
        - `model` (`str`, optional): AI model to use for report generation. Defaults to "gemini-2.5-pro".

    ### 🔄 Returns
        - `bool`: True if complete workflow executed successfully, False otherwise.

    ### ⚠️ Raises
        - `Exception`: If critical errors occur during workflow execution.

    ### 💡 Example

        >>> success = execute_complete_workflow("gemini-2.5-flash")
        >>> if success:
        >>>     print("Complete workflow executed successfully")

    ### 📚 Notes
        - Automatically loads prompts from instructions.yaml
        - Executes report generation first, then autofill processing
        - Provides comprehensive logging and error handling throughout
        - Returns execution status for monitoring and error handling
    """
    print("\n" + "=" * 80)
    print("🎯 EPROC COMPLETE WORKFLOW EXECUTION")
    print("=" * 80)

    workflow_start_time = time.time()

    try:
        # ■■■■■■■■■■■
        # STEP 1: LOAD PROMPTS
        # ■■■■■■■■■■■

        print("[📝]: loading prompts and configuration")
        print("Starting complete EPROC workflow")

        data = load_PROMPT()
        if not data:
            raise Exception("Failed to load prompt data from instructions.yaml")

        if "legacy_prompt" not in data:
            raise Exception("legacy_prompt not found in instructions.yaml")

        legacy_prompt = data["legacy_prompt"]
        print("[✅]: prompts loaded successfully")

        # ■■■■■■■■■■■
        # STEP 2: GENERATE REPORTS
        # ■■■■■■■■■■■

        print(f"\n[🧠]: starting AI report generation with model: {model}")
        print(f"Starting report generation with model: {model}")

        report_start_time = time.time()
        Generate_Final_Report(model, legacy_prompt)
        report_end_time = time.time()

        report_duration = report_end_time - report_start_time
        print(f"[✅]: report generation completed in {report_duration:.2f} seconds")
        print(f"Report generation completed in {report_duration:.2f} seconds")

        # Brief pause between phases
        print("[⏳]: waiting 3 seconds before starting autofill processing...")
        time.sleep(3)

        # ■■■■■■■■■■■
        # STEP 3: AUTOFILL PROCESSING
        # ■■■■■■■■■■■

        print(f"\n[🤖]: starting automated form filling")
        print("Starting autofill processing phase")

        autofill_start_time = time.time()
        processing_stats = run_autofill_processing()
        autofill_end_time = time.time()

        autofill_duration = autofill_end_time - autofill_start_time
        print(f"[✅]: autofill processing completed in {autofill_duration:.2f} seconds")
        print(f"Autofill processing completed in {autofill_duration:.2f} seconds")

        # ■■■■■■■■■■■
        # STEP 4: FINAL SUMMARY
        # ■■■■■■■■■■■

        total_duration = time.time() - workflow_start_time

        print(f"\n{'='*80}")
        print("🎊 COMPLETE WORKFLOW EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"[🧠]: Report generation time: {report_duration:.2f} seconds")
        print(f"[🤖]: Autofill processing time: {autofill_duration:.2f} seconds")
        print(f"[⏱️]: Total workflow time: {total_duration:.2f} seconds")
        print(f"[🎯]: AI Model used: {model}")

        if processing_stats and isinstance(processing_stats, dict):
            if "completed" in processing_stats:
                print(
                    f"[✅]: Processes completed: {processing_stats.get('completed', 0)}"
                )
                print(f"[❌]: Processes failed: {processing_stats.get('failed', 0)}")
                print(f"[📊]: Total processes: {processing_stats.get('total', 0)}")
            else:
                print(
                    f"[ℹ️]: Processing system: {processing_stats.get('system', 'unknown')}"
                )

        print(f"{'='*80}")

        print(
            f"Complete workflow finished successfully in {total_duration:.2f} seconds"
        )
        return True

    except Exception as e:
        total_duration = time.time() - workflow_start_time
        error_msg = (
            f"Complete workflow failed after {total_duration:.2f} seconds: {str(e)}"
        )
        print(error_msg)
        print(f"\n[💥]: {error_msg}")
        print(f"{'='*80}")
        return False


data = load_PROMPT()


legacy_prompt = data["legacy_prompt"]

lista_processos = [
    "50085259120254047102",
    "50091615720254047102",
    "50083907920254047102",
    "50084236920254047102",
    "50092109820254047102",
    "50092602720254047102",
    "50092577220254047102",
    "50092187520254047102",
    "50092542020254047102",
    "50094274420254047102",
    "50092854020254047102",
    "50094282920254047102",
    "50094326620254047102",
    "50094387320254047102",
    "50093876220254047102",
    "50090438120254047102",
    "50091295220254047102",
    "50094058320254047102",
    "50089927020254047102",
    "50093096820254047102",
    "50094967620254047102",
    "50094863220254047102",
    "50095166720254047102",
]
Recognize()
Generate_Final_Report("gemini-2.5-pro", legacy_prompt)
