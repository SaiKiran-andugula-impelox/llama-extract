import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

import streamlit as st
from service import ProcessingService
from logger import logger
import asyncio

def main():
    try:
        logger.info("processing file...")
        st.subheader("Document Extraction with Llama/HuggingFace")

        # Use a container for the input section to visually group it
        with st.container(border=True):  # Container for visual grouping
            col1, col2 = st.columns([1.3, 1.3], gap="large")

            with col1:
                st.markdown("#### MOL Document(s) 📂*")  # Main header
                mol_files = st.file_uploader(
                    label=" ",
                    type=["xlsx", "pdf"],  # "png", "jpg"
                    accept_multiple_files=True,
                    key="mol_uploader",
                    label_visibility="collapsed"
                )

            with col2:
                st.markdown("#### Census Document(s) 📂*")  # Main header
                census_files = st.file_uploader(
                    label=" ",
                    type=["xlsx", "pdf"],   # "png", "jpg"
                    accept_multiple_files=True,
                    key="census_uploader",
                    label_visibility="collapsed"
                )

            execute_disabled = not (census_files or mol_files)
            service = ProcessingService()
            if st.button("🚀 Execute", disabled=execute_disabled, key="execute_button"):
                documents = {
                    "mol": mol_files,
                    "census": census_files,
                }
                with st.spinner("Extracting..."):
                    try:
                        # Ensure process_file is synchronous or use asyncio.run
                        census_result, mol_result = asyncio.run(service.process_file(documents))
                        if census_result:
                            st.subheader("Census Extraction Result (JSON):")
                            st.json(census_result)
                        if mol_result:
                            st.subheader("MOL Extraction Result (JSON):")
                            st.json(mol_result)
                    except Exception as e:
                        logger.error(f"Error processing file: {e}")
                        st.error(f"An error occurred: {e}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()




# from llama_index.core import VectorStoreIndex, Document, Settings
# from llama_index.llms.huggingface import HuggingFaceLLM
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# # Set local embedding model
# Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

# # Set up LLM with your local model
# llm = HuggingFaceLLM(
#     model_name=r"D:\Llama_models\Llama-3.2-1B-Instruct-HF",
#     tokenizer_name=r"D:\Llama_models\Llama-3.2-1B-Instruct-HF",  # <-- Force tokenizer path
#     context_window=100000,         # <-- This is the context window (input tokens + system prompt + user prompt)
#     max_new_tokens=50000,          # <-- This is the maximum output tokens
#     generate_kwargs={"temperature": 0.7, "do_sample": True},
#     device_map="auto"
# )

# # Create a small in-memory context
# documents = [
#     Document(text="Llama 3.2 is a large language model developed by Meta. It supports both text and image inputs.")
# ]

# # Build the index and query engine
# index = VectorStoreIndex.from_documents(documents)
# query_engine = index.as_query_engine(llm=llm)

# # Test queries
# questions = [
#     "What is Llama 3.2?",
#     "What kind of inputs does Llama 3.2 support?",
#     "Who developed Llama 3.2?",
#     "who is mark zuckerberg?",
# ]

# for question in questions:
#     print(f"\nQuestion: {question}")
#     response = query_engine.query(question)
#     print(f"Answer: {response}\n")
