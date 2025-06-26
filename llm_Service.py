from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from prompt import system_prompt, user_prompt  # Make sure prompt.py defines these
# Set local embedding model
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

MODEL_PATH = r"D:\Llama models\Llama-3.2-1B-Instruct-HF"

class LlamaExtractionService:
    def __init__(self, model_path=MODEL_PATH, data_dir="data"):
        self.llm = HuggingFaceLLM(
            model_name=model_path,
            tokenizer_name=model_path,  # <-- Force tokenizer path
            context_window=4096,
            max_new_tokens=256,
            generate_kwargs={
                "temperature": 0.7,
                "do_sample": True,
            },
            device_map="auto",
            tokenizer_kwargs={"max_length": 4096},
        )
        self.prompt_template = PromptTemplate(system_prompt + "\n" + user_prompt)
        self.documents = SimpleDirectoryReader(data_dir).load_data()
        self.index = VectorStoreIndex.from_documents(self.documents)

    def chat_with_engine(self, user_input):
        chat_engine = self.index.as_chat_engine(
            llm=self.llm,
            chat_mode="condense_question",
            text_qa_template=self.prompt_template,
            verbose=True,
        )
        return chat_engine.chat(user_input)

    def query_with_engine(self, query_text=""):
        query_engine = self.index.as_query_engine(
            llm=self.llm,
            text_qa_template=self.prompt_template,
        )
        return query_engine.query(query_text)




# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from llama_index.llms.huggingface import HuggingFaceLLM

# llm = HuggingFaceLLM(model_name="path_to_Llama-3.2-1B-Instruct-HF")
# documents = SimpleDirectoryReader("data").load_data()
# index = VectorStoreIndex.from_documents(documents)
# query_engine = index.as_query_engine(llm=llm)
# response = query_engine.query("Extract main topics from the document.")
# print(response)

#################################################

# # Path to your downloaded model directory
# MODEL_PATH = "Llama-3.2-3B-Instruct-HF"

# # 1. Set up the LLM with advanced parameters
# llm = HuggingFaceLLM(
#     model_name=MODEL_PATH,
#     context_window=4096,               # Adjust as needed
#     max_new_tokens=256,                # Output token limit
#     generate_kwargs={
#         "temperature": 0.7,            # Controls randomness
#         "do_sample": True,
#     },
#     device_map="auto",                 # Use GPU if available
#     tokenizer_kwargs={"max_length": 4096},
# )

# # 2. Set up system and user prompt templates
# system_prompt = (
#     "You are a helpful assistant that extracts information from documents. "
#     "Always return your answer in JSON format."
# )
# user_prompt = (
#     "Extract the main topics from the following document and return as a JSON object with the key 'topics':\n{document_text}"
# )
# prompt_template = PromptTemplate(system_prompt + "\n" + user_prompt)

# # 3. Load your documents (place your files in the 'data' folder)
# documents = SimpleDirectoryReader("data").load_data()
# index = VectorStoreIndex.from_documents(documents)

# # 4. Create a chat engine for multi-turn conversation
# chat_engine = index.as_chat_engine(
#     llm=llm,
#     chat_mode="condense_question",
#     text_qa_template=prompt_template,
#     verbose=True,
# )

# # 5. Simple chat loop
# print("Chat with your document-augmented Llama 3.2 3B model! Type 'exit' to quit.")
# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ["exit", "quit"]:
#         break
#     response = chat_engine.chat(user_input)
#     print(f"Assistant: {response}")

##########################################################
# # 1. Set up the LLM with advanced parameters
# llm = HuggingFaceLLM(
#     model_name="Llama-3.2-3B-Instruct-HF",  # Path to your downloaded model
#     context_window=4096,                     # Adjust as needed
#     max_new_tokens=256,                      # Limit output tokens
#     generate_kwargs={
#         "temperature": 0.7,                  # Control randomness: 0.0=deterministic, 1.0=random
#         "do_sample": True,
#     },
#     device_map="auto",                       # Automatically use GPU if available
#     tokenizer_kwargs={"max_length": 4096},   # Set tokenizer max length
# )

# # 2. Set up system and user prompt templates
# system_prompt = """
# You are a helpful assistant that extracts information from documents and returns it in JSON format.
# """
# user_prompt = """
# Extract the main topics from the following document and return them as a JSON object with the key "topics":
# {document_text}
# """
# prompt_template = PromptTemplate(system_prompt + "\n" + user_prompt)

# # 3. Load documents (for context, but prompts are used for control)
# documents = SimpleDirectoryReader("data").load_data()
# index = VectorStoreIndex.from_documents(documents)

# # 4. Customize the query engine with prompt and LLM
# query_engine = index.as_query_engine(
#     llm=llm,
#     text_qa_template=prompt_template,
# )

# # 5. Query the engine (the prompt will use the document as context)
# response = query_engine.query("")
# print(response)


