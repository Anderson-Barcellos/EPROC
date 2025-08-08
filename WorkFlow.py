import os
import shutil
from Models.models import Generate_Final_Report
from cloud_ocr.recognizer import Recognize
import yaml
import os
from Browsing.EPROC import EPROC_Download
from run_one_at_time import run_processes_sequentially
from Tools.tools import SimplePushbullet

bullet = SimplePushbullet()

def load_PROMPT():
    data = None
    with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data

data = load_PROMPT()
# Load the prompts

legacy_prompt = data["Legacy_Prompt"]

suit_list = [
    "50066638520254047102",
    "50066395720254047102",
    "50066309520254047102",
    "50058782620254047102",
    "50062021620254047102",
    "50067417920254047102",
    "50067590320254047102",
    "50067799120254047102",
    "50067539320254047102",
    "50067989720254047102",
    "50045878820254047102",
    "50066525620254047102",
    "50068352720254047102",
    "50068396420254047102",
    "50067426420254047102",
    "50068222820254047102",
    "50068587020254047102",
    "50068769120254047102",
    "50068777620254047102",
    "50068708420254047102",
    "50018570720254047102",
    "50069427120254047102",
    "50069444120254047102",
    "50069756120254047102",
]


run_processes_sequentially()
