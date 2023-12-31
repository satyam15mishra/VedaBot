# -*- coding: utf-8 -*-

!pip install chromadb

!pip install langchain

from langchain.vectorstores import Chroma
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import pipeline
from langchain.llms import HuggingFacePipeline
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = DirectoryLoader(
    "/content/",
    glob = "./*.pdf",
    loader_cls = PyPDFLoader
)

# PyPdf is a dependancy for DirectoryLoader
!pip install pypdf

docs = loader.load()

# initialize the text splitter variable and then split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
text = text_splitter.split_documents(docs)

# this is a prerequisite for sentence transformer embeddings
!pip install sentence_transformers

# Initialize SentenceTransformerEmbeddings with a pre-trained model
embeddings = SentenceTransformerEmbeddings(model_name="multi-qa-mpnet-base-dot-v1")

# Create a Chroma vector database from the text chunks
persist_directory = "/content/"

db = Chroma.from_documents(text, embeddings, persist_directory=persist_directory)

# To save and load the saved vector db (if needed in the future)
# db.persist()
# db = Chroma(persist_directory="db", embedding_function=embeddings)

import torch

# Specify the checkpoint for the language model
checkpoint = "SATMISH/LaMini-Flan-T5-783M"

# Initialize the tokenizer and base model for text generation
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
base_model = AutoModelForSeq2SeqLM.from_pretrained(
    checkpoint,
    device_map="auto",
    torch_dtype=torch.float32
)

# Create a text generation pipeline
pipe = pipeline(
    'text2text-generation',
    model = base_model,
    tokenizer = tokenizer,
    max_length = 512,
    do_sample = True,
    temperature = 0.3,
    top_p= 0.95
)

# Initialize a local language model pipeline
local_llm = HuggingFacePipeline(pipeline=pipe)
# Create a RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=local_llm,
    chain_type='stuff',
    retriever=db.as_retriever(search_type="similarity", search_kwargs={"k": 2}),
    return_source_documents=True,
)

# Prompt the user for a query
input_query = str(input("Enter your query:"))

# Execute the query using the QA chain
llm_response = qa_chain({"query": input_query})

# Print the response
print(llm_response['result'])
