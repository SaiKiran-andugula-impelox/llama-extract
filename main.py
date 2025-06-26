from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Set local embedding model
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

# Set up LLM with your local model
llm = HuggingFaceLLM(
    model_name=r"D:\Llama_models\Llama-3.2-1B-Instruct-HF",
    tokenizer_name=r"D:\Llama_models\Llama-3.2-1B-Instruct-HF",  # <-- Force tokenizer path
    context_window=4096,
    max_new_tokens=256,
    generate_kwargs={"temperature": 0.7, "do_sample": True},
    device_map="auto"
)

# Create a small in-memory context
documents = [
    Document(text="Llama 3.2 is a large language model developed by Meta. It supports both text and image inputs.")
]

# Build the index and query engine
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(llm=llm)

# Test queries
questions = [
    "What is Llama 3.2?",
    "What kind of inputs does Llama 3.2 support?",
    "Who developed Llama 3.2?"
]

for question in questions:
    print(f"\nQuestion: {question}")
    response = query_engine.query(question)
    print(f"Answer: {response}\n")


# service = LlamaExtractionService()
# response = service.query_with_engine("Extract main topics from the document.")
# print(response)



