import asyncio
import streamlit as st
from logger import logger
from file_extraction_service import PreProcessingService

class ProcessingService:
    def __init__(self):
        self.preprocessing_Service = PreProcessingService()

    async def process_file(self,documents):
        try:
            logger.info(f"Processing employee data documents.")

            census_data_config, mol_data_config = await self.preprocessing_Service.segregate_data(documents)

            # Create tasks with explicit mapping
            tasks = []
            task_mapping = []
            
            # Add required documents first
            tasks.append(self.preprocessing_Service.process_document(  # census extraction
                documents=census_data_config["uploaded_files"],
                text_input=census_data_config["text_input"],
                user_prompt=census_data_config["user_prompt"],
                system_prompt=census_data_config["system_prompt"],
                document_name=census_data_config["document_name"],
            ))
            task_mapping.append("census")
            
            tasks.append(self.preprocessing_Service.process_document(  # mol extraction
                documents=mol_data_config["uploaded_files"],
                text_input=mol_data_config["text_input"],
                user_prompt=mol_data_config["user_prompt"],
                system_prompt=mol_data_config["system_prompt"],
                document_name=mol_data_config["document_name"],
            ))
            task_mapping.append("mol")

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            result_map = dict(zip(task_mapping, results))

            census_extraction_resp = result_map.get("census")
            mol_extraction_resp = result_map.get("mol")

            return census_extraction_resp, mol_extraction_resp

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {"ERROR": str(e)}

