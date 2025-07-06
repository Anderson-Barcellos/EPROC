import os
import shutil
from Models.models import  Generate_Final_Report
from cloud_ocr.recognizer import Recognize
from Autofill.run_one_at_time import run_processes_sequentially
from Browsing.EPROC import EPROC_Download
import yaml
import os
from Tools import check_presence
from openai import OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)


def check(number):
    internal_path = os.path.join("Reports")
    for file in os.listdir(internal_path):
        if file.endswith(".md"):
            if number in file:
                print(f"Processo {number} já foi processado")
                return True
    return False

def load_PROMPT():
    data = None
    with open("Prompts/instructions.yaml", "r", encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data

data = load_PROMPT()
#Load the prompts
advanced_prompt = data["Advanced_Prompt"]
legacy_prompt = data["Legacy_Prompt"]
middle_prompt = data["Middle_Prompt"]
ultimate_prompt = data["Ultimate_Prompt"]




#List of Suit Numbers
suit_numbers = []

#Load the suits in the Processos folder
in_place_suits = [processo[3:23] for processo in os.listdir("Processos") if processo.endswith(".PDF") or processo.endswith(".pdf")]
