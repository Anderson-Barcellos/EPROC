import os
from Models.models import Generate_Final_Report
from cloud_ocr.recognizer import Recognize
from Browsing.EPROC import EPROC_Download
from run_one_at_time import run_processes_sequentially
from Tools import WorkflowLogger
import yaml



logger = WorkflowLogger("WorkFlow")

def load_PROMPT():
    data = None
    with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data

data = load_PROMPT()
# Load the prompts

legacy_prompt = data["legacy_prompt"]

suit_list = [

"50066508620254047102",
"50067070720254047102",
"50077065720254047102",

]



run_processes_sequentially()