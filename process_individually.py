import os
import time
from Models.models import Generate_Final_Report
from Browsing.EPROC import EPROC_Download
import yaml
from cloud_ocr.recognizer import Recognize



def load_PROMPT() -> dict | None:
    """
    ### 📝 load_PROMPT
    Loads the prompt instructions from a YAML file located at 'Prompts/instructions.yaml'. This function is responsible for reading
    and parsing the YAML file containing prompt templates or instructions required for the workflow.
    """

    return yaml.load(open('Prompts/instructions.yaml', 'r'), Loader=yaml.FullLoader)


data = load_PROMPT()

legacy_prompt = data["legacy_prompt"]
Generate_Final_Report("gemini-2.5-flash", legacy_prompt)