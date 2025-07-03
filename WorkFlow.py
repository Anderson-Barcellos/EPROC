import os
import shutil
from Models.models import  Generate_Final_Report
from cloud_ocr.recognizer import Recognize
#rom Autofill.run_one_at_time import run_processes_sequentially
from Browsing.EPROC import EPROC_Download
import yaml
import os
from Tools import check_presence

# Implementation of the check_presence of files already OCRed and processed
def check(number, path):
    internal_path = os.path.join(path, "Processed")
    if path == "Reports":
        for file in os.listdir(internal_path):
            if file.endswith(".md"):
                file = file.split("_")[0]
                if file == number:
                    return True
    elif path == "Output":
        for file in os.listdir(internal_path):
            if file.endswith(".txt"):
                file = file.split(".")[0]
                if file == number:
                    return True
    return False

# Parsing the instructions from the YAML file
data = None
with open("instructions.yaml", "r", encoding="utf-8") as file:
    data = yaml.load(file, Loader=yaml.FullLoader)

advanced_prompt = data["Advanced_Prompt"]
legacy_prompt = data["Legacy_Prompt"]


#List of Suit Numbers
suit_numbers = [

 "50107640520244047102",
 "50006463320254047102",
 "50003926020254047102",
 "50052117420244047102",
 "50108301920234047102",
 "50070348320244047102",
 "50112023120244047102",
 "50035338720254047102",
 "50035347220254047102",
 "50035770920254047102",
 "50035988220254047102",
 "50036082920254047102",
 "50036464120254047102",
 "50034308020254047102",
 "50031293620254047102",
 "50044561620254047102",
 "50044613820254047102",
 "50043237120254047102",
 "50044328520254047102",
 "50025352220254047102",
 "50034689220254047102",
 "50034637020254047102"
 
]
# List of numbers obtained from the Downloaed pdf files on Processos folder
in_place_suits = [processo for processo in os.listdir("Processos") if processo.endswith(".PDF") or processo.endswith(".pdf")]


# Rudimentary implementation of the Downoad of the PDF files
for file in os.listdir("Processos"):
    if file.endswith(".PDF") or file.endswith(".pdf"):
        #EPROC_Download(file)
        print(file)

# Check if the suit numbers are already processed and if not, run the Recognize function
for number in suit_numbers:
    if check_presence(number):
        print(f"Processo {number} já foi processado")
    else:
        Recognize()

# Check if the suit numbers are already processed and if not, run the Recognize function
for file in os.listdir("Output"):
    if file.endswith(".txt"):
        print(file)
        Generate_Final_Report("gpt-4.1", legacy_prompt)