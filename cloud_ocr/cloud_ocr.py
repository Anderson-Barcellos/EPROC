import threading
from google.cloud import vision
import fitz
from PIL import Image
from google.cloud import vision
from google.oauth2 import service_account
import json
import os
from pathlib import Path



#GLOBAL VARIABLES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
key = {}

try:
    key_path = "D:/OneDrive/Área de Trabalho/Complementares/cloud_ocr/key.json"
    with open(key_path, "r") as file:
        key = json.load(file)
except Exception as e:
    print(f"Error loading key.json: {str(e)}")
    raise

credentials = service_account.Credentials.from_service_account_info(key)
client = vision.ImageAnnotatorClient(credentials=credentials)

def OCR(page: fitz.Page, page_num: int, thread: bool = False) -> str:
    """
    ### 📝 OCR
    Processes a PDF page to extract text using the Google Cloud Vision API.

    ### 🖥️ Parameters
    - `page` (`fitz.Page`): The PDF page to be processed.
    - `page_num` (`int`): The page number, used for naming the temporary image file.
    - `thread` (`bool`, optional): If `True`, the OCR process runs in a separate thread. Defaults to `False`.

    ### 🔄 Returns
    - `str`: The detected text from the page, formatted with page start and end markers.

    #### ⚠️ Raises
    - `Exception`: Raised if there is an error during image processing or text detection.

    ### 📌 Notes
    - The function temporarily saves the page as a PNG image for text detection.
    - The temporary image file is deleted after processing.
    - Ensure that the Google Cloud Vision API credentials are correctly configured.

    ### 💡 Example

    >>> OCR(page, 1)
    'Detected text from page 1...'
    """

    def _OCR(page: fitz.Page, page_num: int) -> str:
        pix = page.get_pixmap(matrix=fitz.Identity)  # type: ignore
        img = Image.frombuffer(
            "RGB", (pix.width, pix.height), pix.samples, "raw", "RGB", 0, 1)
        temp_image_path = Path(__file__).parent / f"page{page_num}.png"
        img.save(temp_image_path)
        # Lê o arquivo da imagem
        try:
            content = None
            with open(temp_image_path, 'rb') as image_file:
                content = image_file.read()
            os.remove(temp_image_path)
            # Realiza a detecção de texto
            response = client.text_detection(  # type: ignore[attr-defined]
                image=vision.Image(content=content))

            # Verifica se há erro
            if response.error.message:
                raise Exception(
                    '{}\nPara mais detalhes: {}'.format(
                        response.error.message,
                        response.error.details
                    )
                )
            # Retorna o texto completo (primeira anotação contém todo o texto)
            if response.text_annotations:
                return f"\n\n------------ Inicio da pagina {page_num} ------------\n\n{response.text_annotations[0].description}\n\n------------ Fim da pagina {page_num} ------------\n\n"
            else:
                return "Não foi possivel detectar texto"
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            raise
    if thread:
        threading.Thread(target=_OCR, args=(page, page_num)).start()
    else:
        return _OCR(page, page_num)


def OCR_Single_Image(path: str) -> str:
    """
    OCRs a single image using Google Cloud Vision API.
    """
    try:
        img = Image.open(path)
        temp_image_path = os.path.join("Temp",f"page.png")
        img.save(temp_image_path)
        content = None
        with open(temp_image_path, 'rb') as image_file:
            content = image_file.read()
        os.remove(temp_image_path)
        response = client.text_detection(image=vision.Image(content=content))  # type: ignore[attr-defined]
        return   response.text_annotations[0].description
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise


# print(__file__)
