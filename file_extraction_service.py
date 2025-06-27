from logger import logger
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime
import math
from prompt import (census_user_prompt, mol_user_prompt, mol_prompt, census_text_prompt)
from llm_Service import LlamaExtractionService
import pandas as pd
import fitz
import os
import asyncio
import json
import re
import streamlit as st



DOCUMENT_CENSUS = "census"
DOCUMENT_MOL = "mol"

class PreProcessingService:
    def __init__(self):
        self.llm_service = LlamaExtractionService()

    async def segregate_data(self, documents):
        try:
            logger.info(f"seggregating mol and census files.")            
            # Get mol and census documents from the input
            mol_documents = documents.get(DOCUMENT_MOL, [])
            census_documents = documents.get(DOCUMENT_CENSUS, [])
            
            # Handle documents by type (Excel -> parse, others -> store as is)
            mol_text_input, mol_files = await self.document_handler(mol_documents)
            census_text_input, census_files = await self.document_handler(census_documents)

            # Format the data for census and mol
            census_data = {
                "document_name": DOCUMENT_CENSUS,"uploaded_files": census_files,"text_input": census_text_input,
                "user_prompt": census_user_prompt,"system_prompt": census_text_prompt}

            mol_data = {
                "document_name": DOCUMENT_MOL,"uploaded_files": mol_files,"text_input": mol_text_input,
                "user_prompt": mol_user_prompt,"system_prompt": mol_prompt}
        
            return census_data, mol_data
        except Exception as e:
            logger.error(f"EVS-002: Error in segregating data: {str(e)}")
            st.error(f"Internal server error during file processing.")


    async def document_handler(self, documents):
        text_input = []
        files = []

        for document in documents:
            file_name = document.name
            file_extension = os.path.splitext(file_name)[1].lower()  # Get the file extension
            document.seek(0)
            if file_extension == ".xlsx":  # Handle Excel file
                logger.info(document)
                parsed = await self.parse_excel_data(document)
                text_input.append(parsed)
            else:
                files.append(document)

        return text_input,files



    async def parse_excel_data(self,uploaded_file):
        """
        Parses an Excel file and returns a dict of sheet_name: list of lists,
        where the first row is headers (with 'Row' as the first column),
        and each subsequent row is [row_index, ...cell values...].
        Handles datetime columns by converting them to ISO strings.
        """
        try:
            logger.info(f"Processing Excel extraction as list of lists..")
            wb = openpyxl.load_workbook(uploaded_file, data_only=True)
            extracted_data = {}

            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                if sheet.sheet_state in ['hidden', 'veryHidden']:
                    continue

                # Get visible rows and columns
                visible_rows = [row[0].row for row in sheet.iter_rows() if not all(cell.value is None for cell in row)]
                visible_cols = [col_idx for col_idx in range(1, sheet.max_column + 1)
                                if any(sheet.cell(row=row_idx, column=col_idx).value is not None for row_idx in visible_rows)]

                if not visible_rows or not visible_cols:
                    continue

                # Prepare headers: "Row" + Excel column letters
                headers = ['Row'] + [get_column_letter(col) for col in visible_cols]
                sheet_data = [headers]

                # Data rows
                for row_idx in visible_rows:
                    row_data = [row_idx]
                    for col_idx in visible_cols:
                        value = sheet.cell(row=row_idx, column=col_idx).value
                        if isinstance(value, float):
                            value = math.ceil(value) if value is not None else 0
                        elif isinstance(value, str):
                            value = value.replace('\n', ' ')
                        elif isinstance(value, datetime):
                            value = value.isoformat()
                        row_data.append(value if value is not None else None)
                    sheet_data.append(row_data)

                extracted_data[sheet_name] = sheet_data

            return extracted_data

        except Exception as e:
            logger.error(f"PED-001: Error extracting visible data from Excel file: {e}")
            return {"ERROR": str(e)}


    async def process_document(self, documents, text_input, user_prompt, system_prompt, document_name):

        file_image_content_list, file_text_content_list= await self.pre_process_documents_and_input_text(
                    uploaded_files=documents, document_name=document_name)
        

        result = await self.llm_service.query_with_engine(file_image_content_list, file_text_content_list, text_input, document_name, user_prompt, system_prompt)

        return result




    async def pre_process_documents_and_input_text(self, uploaded_files, document_name):
        try:
            file_image_content_list = []
            file_text_content_list = []

            if uploaded_files:
                logger.info("Processing uploaded files...")

                tasks = [self.process_uploaded_file(uploaded_file, document_name) for uploaded_file in uploaded_files]
                results = await asyncio.gather(*tasks)

                for uploaded_file, uploaded_file_result in zip(uploaded_files, results):
                    file_content, file_extension = uploaded_file_result  # Unpack the tuple

                    if isinstance(file_content, bytes) or (isinstance(file_content, list) and isinstance(file_content[0], bytes)):
                        file_image_content_list.append({"file_content": file_content, "file_extension": file_extension})
                        logger.info(f"Image content extracted from {uploaded_file.name}.")
                        
                    elif isinstance(file_content, dict) or isinstance(file_content[0], dict):
                        file_text_content_list.append({"file_content": json.dumps(file_content), "file_extension": file_extension})
                        logger.info(f"Text content extracted from {uploaded_file.name}.")

            return file_image_content_list, file_text_content_list

        except Exception as e:
            logger.error(f"GDP-001: Unexpected error in {__file__}, function pre_process_uploaded_files_and_input_text: {str(e)}")
            st.error("Internal server error during file processing.")
        

        
    async def process_uploaded_file(self,uploaded_file, document_name):
        try:
            logger.info(f"Determining file type for uploaded file: {uploaded_file.name}")
            
            if uploaded_file.type == "application/pdf":
                logger.info(f"uploaded file {uploaded_file.name} is in pdf format.")
            
                if await self.check_for_images_in_pdf(uploaded_file):
                    logger.info("Images found in PDF.")
                    file_image_content = await self.extract_images_from_pdf(uploaded_file, document_name)
                    return file_image_content, "pdf"  # Return content and type
                else:
                    logger.info("Text found in PDF.")
                    file_text_content = await self.extract_text_from_pdf(uploaded_file)
                    return file_text_content, "text"  # Return content and type

            elif "image" in uploaded_file.type:
                logger.info("Processing image.")
                file_image_content = await self.process_image(uploaded_file)
                return file_image_content, "image"  # Return content and type
            else:
                logger.info(f"GDP-002: Error processing uploaded file: Unsupported file type: {uploaded_file.type}.")
                st.error(f"Inetrnal Server error during file processing")

        except Exception as e:
            logger.error(f"GDP-003: Error processing uploaded file in {__file__}, function process_uploaded_file: {str(e)}")
            st.error("Internal server error during file processing.")


    async def extract_census_text_input(self, text_input):
        chunk_size = 30
        try:
            logger.info("Starting extraction of census text input.")
            try:
                text_input_list = json.loads(text_input)  # Assuming text_input is a JSON string
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {str(e)}. Invalid JSON input.")
                st.error("Internal server error during file processing.")

            chunks = [text_input_list[i:i + chunk_size] for i in range(0, len(text_input_list), chunk_size)]

            chunk_bytes_list = [json.dumps(chunk, ensure_ascii=False).encode('utf-8') for chunk in chunks]

            logger.info(f"Split text input into {len(chunks)} chunks of {chunk_size} entities each.")
            return chunk_bytes_list

        except Exception as e:
            logger.error(f"GDP-005: Unexpected error in extract_census_text_input: {str(e)}")
            st.error("Internal server error during file processing.")


    async def check_for_images_in_pdf(self,uploaded_file): 
        try:
            uploaded_file.seek(0) # Reset the file pointer to the beginning of the file.
            logger.info("Checking for images in PDF.")
            file_content = uploaded_file.read()

            text_threshold = 100000  # Text content threshold
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            text_content = "".join(page.get_text() for page in pdf_document)

            uploaded_file.seek(0)
            if len(text_content) > text_threshold:
                logger.info(f"uploaded_file {uploaded_file.name} contains text content greater than threshold characters, likely to be text file.")
                return False 

            logger.info(f"Uploaded_file {uploaded_file.name} contains text content less text than threshold, likely to be image file.")
            return True 

        except Exception as e:
            logger.error(f"GDP-006: An error occurred in check_for_images_in_pdf: {str(e)}")
            st.error("Internal server error during file processing.")



    async def extract_images_from_pdf(self,uploaded_file,document_name):
        try:
            logger.info(f"Extracting images from uploaded_file {uploaded_file.name}")
            
            file_content = uploaded_file.read()
            doc = fitz.open(stream=file_content, filetype="pdf")
            image_bytes_list = []

            tasks = [self.process_image_from_pdf_page(doc, page_num, image_bytes_list, document_name) for page_num in range(len(doc))]
            await asyncio.gather(*tasks)
            
            doc.close()
            if not image_bytes_list:
                logger.warning("No images could be processed from the PDF.")
                return None

            return image_bytes_list
        except Exception as e:
            logger.error(f"GDP-007: An error occured during extract_images_from_pdf: {str(e)}")
            st.error("Internal server error during file processing.")


    async def process_image_from_pdf_page(self,doc, page_num, image_bytes_list, document_name):
        try:
            logger.info(f"processing pdf image document for gcs..")
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            # Save the new single-page document to bytes
            chunk_bytes = new_doc.tobytes(garbage=4, deflate=True)
            image_bytes_list.append(chunk_bytes) # Append PDF bytes

        except Exception as e:
            logger.error(f"GDP-008: Image encoding failed for page {page_num + 1}: {str(e)}.")
            st.error("Internal server error during file processing.")


    async def extract_text_from_pdf(self,uploaded_file):
        try:
            if isinstance(uploaded_file, list):
                logger.info("text & table data extraction..")
                file_content, file_name = uploaded_file[0], uploaded_file[-1] 
            else:
                uploaded_file.seek(0)
                file_content, file_name = uploaded_file.read(), uploaded_file.name

            all_text_content = []  
            all_tables_data = []
            
            logger.info(f"PDF text & table data extraction..{file_name}.")
            
            with fitz.open(stream=file_content, filetype="pdf") as doc:
                for page in doc:
                    non_table_text = ""
                    try:
                        table_rects = [cell for table in page.find_tables() for cell in table.cells]

                        for block in page.get_text("blocks"):
                            block_rect = fitz.Rect(block[:4])
                            if not any(block_rect.intersects(table_rect) for table_rect in table_rects):
                                non_table_text += block[4] + "\n"
                        all_text_content.append({"page_number": page.number + 1, "text": non_table_text.strip()})
                    except Exception as e:
                        logger.error(f"Error processing text on page {page.number + 1}: {str(e)}")
                        

                    try:
                        for table in page.find_tables():
                            try:
                                df = table.to_pandas()
                                table_data = df.to_dict(orient="split")
                                table_data["page_number"] = page.number + 1
                                all_tables_data.append(table_data)
                            except Exception as e:
                                logger.error(f"Error processing table on page {page.number + 1}: {str(e)}")
                                
                    except Exception as e:
                        logger.error(f"Error detecting tables on page {page.number + 1}: {str(e)}")
                        st.error("Internal server error during file processing.")
            
            cleaned_data = await self.clean_table_data(all_tables_data)        
            pdf_data = [{"text_data": all_text_content}, {"tabular_data": cleaned_data} ]
            return pdf_data

        except Exception as e:
            logger.error(f"GDP-009: Error during PDF data extraction: {str(e)}")
            st.error("Internal server error during file processing.")
            


    async def clean_table_data(self,tables_data):
        try:
            for table in tables_data:
                if "index" in table:
                    del table["index"]
                table["data"].insert(0, table["columns"])
                del table["columns"]

                table["data"] = [
                    [
                        re.sub(r'\n', '. ', str(cell)).strip()  
                        .replace('•', '-')                    
                        .replace('*', '')                    
                        if isinstance(cell, str) else cell
                        for cell in row
                    ]
                    for row in table["data"]]

            logger.info(f"Removed of new line charactrs in Pre-processed Tabular data.")
            return tables_data

        except Exception as e:
            logger.error(f"GDP-010: Error in clean_table_data: {str(e)}")
            st.error("Internal server error during file processing.")



    async def process_image(self,uploaded_file, api_logs_id):
        try:
            logger.info(f"Processing image: {uploaded_file.name}.")
            uploaded_file.seek(0)  # Reset the file pointer to the beginning of the file.

            file_content = uploaded_file.read()
            
            return file_content

        except Exception as e:
            logger.error(f"GDP-011: Error processing image in {__file__}, function process_image: {str(e)}")
            st.error("Internal server error during file processing.")
