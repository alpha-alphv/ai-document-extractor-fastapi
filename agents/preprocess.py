import pymupdf  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import os
import shutil

from utils import logger

# Set OCR languages (English + Malay)
OCR_LANG = "eng+msa"

# Extract text from text-based PDF
def extract_text_pdf(file_bytes: bytes) -> str:
    text = ""
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Extract text using OCR from image-based PDF (multi-language)
def extract_text_ocr(file_bytes: bytes) -> str:
    text = ""
    images = convert_from_bytes(file_bytes)
    # Log Total Pages
    print(f"Total pages to process: {len(images)}")

    for image in images:
        # Log Loop Iteration
        print(f"Processing image {images.index(image) + 1} of {len(images)}")
        text += pytesseract.image_to_string(image, lang=OCR_LANG)
    return text

# Convert each pages into images and store in directory ./pages
def pdf_to_images(file_bytes: bytes, output_dir='./pages'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    num_images = 0

    # Use Matrix for zoom (increasing DPI)
    zoom_matrix = pymupdf.Matrix(4.0, 4.0)
    for page_num in range(len(doc)):
        print(f"Processing page {num_images + 1} of {len(doc)}")
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=zoom_matrix)
        pix.save(f"{output_dir}/page_{page_num + 1}.png")
        num_images += 1
    doc.close()
    return num_images

def filter_bank_copy(output_dir='./pages'):
    images = [f for f in os.listdir(output_dir) if f.lower().endswith('.png')]
    images.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    print(f"Total images to process: {len(images)}")
    for img_name in images:
        print(f"Processing image: {img_name}")
        img_path = os.path.join(output_dir, img_name)
        try:
            page_num = int(img_name.split('_')[1].split('.')[0])
            
            pix = pymupdf.Pixmap(img_path)
            if pix.colorspace != pymupdf.csRGB:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:
                pix = pymupdf.Pixmap(pix, 0)
            
            pdf_bytes = pix.pdfocr_tobytes()
            doc = pymupdf.open('pdf', pdf_bytes)
            page = doc[0]
            
            if (page.search_for('we are pleased') or
                page.search_for('strictly private and highly confidential') or
                page.search_for('private & confidential') or
                page.search_for('private and confidential')):
                new_name = 'bank_copy.png'
                new_path = os.path.join(output_dir, new_name)
                os.rename(img_path, new_path)
                print(f"Renamed {img_name} to {new_name}")
                break
                
            doc.close()
            pix = None
            
        except Exception as e:
            print(f"Error processing {img_name}: {str(e)}")

# Filter page and rename page name using PYMUPDF OCR
def filter_and_rename_pages(bank_name: str, output_dir='./pages'):
    print(f"Filtering pages for bank: {bank_name}")
    filtered_dir = os.path.join(output_dir, 'filtered')
    if not os.path.exists(filtered_dir):
        os.makedirs(filtered_dir)
    
    images = [f for f in os.listdir(output_dir) if f.lower().endswith(('.png'))]
    # Sort images by numerical part of filename
    images.sort(key=lambda x: int(x.split('_')[1].split('.')[0]) if x != 'bank_copy.png' else 0)    

    print(f"Total images to process: {len(images)}")
    pending_subject_fa = False
    pending_gurantor_details = False
    pending_property_details = False

    for img_name in images:
        print(f"Processing image: {img_name}")
        img_path = os.path.join(output_dir, img_name)
        try:
            # Convert image to Pixmap
            pix = pymupdf.Pixmap(img_path)
            if pix.colorspace != pymupdf.csRGB:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:
                pix = pymupdf.Pixmap(pix, 0)  # Remove alpha channel
            
            # Convert Pixmap to PDF with OCR
            pdf_bytes = pix.pdfocr_tobytes()
            doc = pymupdf.open('pdf', pdf_bytes)
            page = doc[0]
            
            # Collect all matching names
            new_names = []

            # To check if the contents continue to next page
            if pending_subject_fa:
                new_names.append('subject_of_fa_2.png')
                pending_subject_fa = False

            if pending_gurantor_details:
                new_names.append('gurantor_details_2.png')
                pending_gurantor_details = False

            if pending_property_details:
                new_names.append('property_details_2.png')
                pending_property_details = False

            if bank_name.upper() == 'CIMB BANK BERHAD' or bank_name.upper() == 'CIMB ISLAMIC BANK BERHAD':
                if (page.search_for('we are pleased to inform you that') or
                    page.search_for('strictly private and highly confidential')):
                    new_names.append(f'bank_copy.png')

                if (page.search_for('form of facility') or
                    page.search_for('facility amount is an amount which is equal') or
                    page.search_for('type of facility') or 
                    page.search_for('payment amount (RM per payment)')):
                    # check if the content contain total
                    if (page.search_for('total')):
                        new_names.append(f'subject_of_fa.png')
                    else:
                        # To check if the contents continue to next page
                        # Add current page as 'subject_of_fa_1'
                        # Add the next page as 'subject_of_fa_2
                        new_names.append('subject_of_fa_1.png')
                        pending_subject_fa = True
                if (page.search_for('pengiraan duit yang dikenakan') or
                    page.search_for('salinan kepada')):
                    new_names.append(f'law_firm_details.png')
                if (page.search_for('to finance the purchase of the property described below') or page.search_for('execution of open charge under')
                 or page.search_for('a letter of undertaking from registered owner')):
                    if(page.search_for('if there is a disrepancy in the property details stated above') or page.search_for('individual title') or 
                    page.search_for('strava title')):
                        new_names.append(f'property_details.png')
                    else:
                        pending_property_details = True
                        new_names.append(f'property_details_1.png')

                if (page.search_for('all of the following documents (the "Security Documents") must be executed and perfected, in form and content acceptable to the Bank.') or
                    page.search_for('the following security which shall be in such form') or
                    page.search_for('execution of joint and several guarantee in favour of the bank')):
                    if (page.search_for('joint and several guarantee in favour of the bank') or
                        page.search_for('corporate guarantee in favour of the bank') or
                        page.search_for('individual guarantee in favour of the bank')):
                        new_names.append(f'guarantor_details.png')
                    elif (page.search_for('property with')):
                        new_names.append(f'property_details.png')
                    else:
                        # To check if the contents continue to next page
                        # Add current page as 'gurantor_details_1'
                        # Add the next page as 'gurantor_details_2'
                        new_names.append('gurantor_details_1.png')
                        pending_gurantor_details = True
            doc.close()
            pix = None
            
            # Copy image for each matching name
            for new_name in new_names:
                dest_path = os.path.join(filtered_dir, new_name)
                shutil.copy(img_path, dest_path)
                print(f"Saved {img_name} as {new_name}")
            
            if not new_names:
                print(f"{img_name} does not match any criteria.")
                
        except Exception as e:
            print(f"Error processing {img_name}: {str(e)}")
            pending_subject_fa = False  # Reset on error
            pending_gurantor_details = True

