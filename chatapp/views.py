import os
import warnings
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain_community.llms import Ollama
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import DocArrayInMemorySearch
from operator import itemgetter
from django.core.cache import cache
from django.conf import settings





# Suppress the pydantic warning
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Use the environment variable for the API key
OPENAI_API_KEY = settings.OPENAI_API_KEY
MODEL = "gpt-4-turbo"

# Initialize the model and embeddings
model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=MODEL)
embeddings = OpenAIEmbeddings()
parser = StrOutputParser()

# Define the prompt template
template = """
Answer the question based on the context below. If you can't 
answer the question, reply "It is not within my Scope".

Context: {context}

Question: {question}
"""

prompt = PromptTemplate.from_template(template)
prompt.format(context="Here is some context", question="Here is a question")
chain = prompt | model | parser

# Load and split the PDF
pdf_files = ["User_Guide.pdf", "User Guide - Marine V1.1 (1).pdf", "User Guide - Operations V1.1.pdf"]

all_pages = []
for pdf_file in pdf_files:
    loader = PyPDFLoader(pdf_file)
    pages = loader.load_and_split()
    all_pages.extend(pages)

# Create the vector store from the document
vectorstore = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = vectorstore.as_retriever()

chain = (
    {
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
    }
    | prompt
    | model
    | parser
)

# Function for generating LLM response
def format_answer(answer):
    
    steps = answer.split('. ')
    formatted_answer = '<ol>'
    for step in steps:
        if step:
            formatted_answer += f'<li>{step.strip()}</li>'
    formatted_answer += '</ol>'
    return formatted_answer

def generate_response(input):
    result = chain.invoke({'question': input})
    answer = result.split("Answer: ")[-1].strip() if "Answer: " in result else result.strip()
    return format_answer(answer)

@csrf_exempt
def index(request):
    messages = cache.get('messages', [{"role": "assistant", "content": "Welcome To AVP "}])
    return render(request, 'chat/index.html', {'messages': messages})

@csrf_exempt
def chat(request):
  
    if request.method == 'POST':
        user_input = request.POST.get('message')
        if not user_input:
            return JsonResponse({"error": "No input provided"}, status=400)

        # Preprocess the user input: strip whitespace and convert to lowercase
        user_input = user_input.strip().lower()

        messages = cache.get('messages', [])

        try:
            messages.append({"role": "user", "content": user_input})
            response = generate_response(user_input)
            messages.append({"role": "assistant", "content": response})
            cache.set('messages', messages)
            logging.debug(f"User input: {user_input}, Response: {response}")
            return JsonResponse({"message": response})
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

