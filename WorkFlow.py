import os
import shutil
from Models.models import  Generate_Final_Report
from Browsing.EPROC import EPROC_Download
import yaml
import os
from cloud_ocr.recognizer import Recognize
from openai import OpenAI
from Models import Gemini_PDF_Report, GeminiReport

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
spmja_1= data["SPMJA_1.0"]
spmja_2= data["SPMJA_2.0"]
if Recognize():
    for file in os.listdir("Output"):
        if file.endswith("txt"):
            GeminiReport(name = file, model_name="gemini-2.5-pro", system_instruction=spmja_1)


from run_one_at_time import run_processes_sequentially
run_processes_sequentially()

