import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import (
    VectorizedQuery
)
from langchain_openai import AzureOpenAIEmbeddings

app = FastAPI()

load_dotenv()

class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    true_or_false = "true_or_false"
    popular_choice = "popular_choice"
    estimation = "estimation"

class Ask(BaseModel):
    question: str | None = None
    type: QuestionType
    correlationToken: str | None = None

class Answer(BaseModel):
    answer: str
    correlationToken: str | None = None
    promptTokensUsed: int | None = None
    completionTokensUsed: int | None = None

client: AzureOpenAI

if "AZURE_OPENAI_API_KEY" in os.environ:
    client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_OPENAI_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )
else:
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        azure_ad_token_provider=token_provider,
        api_version = os.getenv("AZURE_OPENAI_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

deployment_name = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME")
index_name = "movies-semantic-index"
service_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")

credential = None
if "AZURE_AI_SEARCH_KEY" in os.environ:
    credential = AzureKeyCredential(os.environ["AZURE_AI_SEARCH_KEY"])
else:
    credential = DefaultAzureCredential()

search_client = SearchClient(
    service_endpoint, 
    index_name, 
    credential
)

# use an embeddingsmodel to create embeddings
embeddings_model = AzureOpenAIEmbeddings(    
    azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
    openai_api_version = os.getenv("OPENAI_EMBEDDING_API_VERSION"),
    model= os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
)

@app.get("/")
async def root():
    return {"message": "Hello Smorgs"}

@app.get("/healthz", summary="Health check", operation_id="healthz")
async def get_products(query: str = None):
    """
    Returns a status of the app
    """

@app.post("/ask", summary="Ask a question", operation_id="ask") 
async def ask_question(ask: Ask):
    """
    Ask a question
    """

    # This is not using a semantic search, but a simple search
    results = list(search_client.search(
        search_text=ask.question,
        query_type="simple",
        include_total_count=True,
        top=5
    ))

    print('Search results:')
    print(results)

    # Send a completion call to generate an answer
    print('Sending a request to openai')
    start_phrase = ask.question
    response = client.chat.completions.create(
        model = deployment_name,
        messages = [{"role" : "assistant", "content" : start_phrase}],
    )

    print(response.choices[0].message.content)
    print(response)
    answer = Answer(answer=response.choices[0].message.content)
    answer.correlationToken = ask.correlationToken
    answer.promptTokensUsed = response.usage.prompt_tokens
    answer.completionTokensUsed = response.usage.completion_tokens

    return answer
