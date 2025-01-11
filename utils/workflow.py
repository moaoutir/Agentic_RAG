
import json
import re
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from typing_extensions import TypedDict
from typing import List
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from .embedding_utils import retriever
from .llm_utils import llm
from .web_search_tool import spoonacular_search


def format_docs(docs):
    formatted_docs = [
        "metadata: " + str(doc.metadata) + " name_recipe:" + doc.page_content
        for doc in docs
    ]
    print(formatted_docs)
    return formatted_docs

# Retrieval Grader
prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are a grader assessing relevance
    of a retrieved document to a user question. If the document contains keywords related to the user question,
    grade it as relevant. It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explaination.
     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Here is the retrieved document: \n\n {document} \n\n
    Here is the user question: {question} \n <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question", "document"],
)

retrieval_grader = prompt | llm | JsonOutputParser()

# Answer question
prompt = PromptTemplate(
        template = """You are an expert chef specializing in creating and refining recipes with precise ingredient measurements.
    Context and Content Guidelines: Use the provided context as the primary reference to craft a recipe. If any ingredient units or measurements are missing in the context, use your own knowledge and expertise to assign the most appropriate unit and quantity, ensuring accuracy and consistency.
    Restrictions: Do not introduce instructions, or nutritional details not mentioned in or directly derivable from the context.
    Output Requirements: Provide:
    A recipe title in bold.
    A description of the recipe.
    A detailed ingredients list with precise quantities and units (e.g., grams, kilograms, cups, tablespoons, teaspoons, etc.).
    Step-by-step instructions that are clear and easy to follow.
    nutritional details if provided in the context
    Ensure the recipe is clear, precise, and concise, adhering to a character limit of 4000.
    Focus on correctness, particularly in ingredient units, even if those details are not specified in the context.
    Use strengthening language such as "Mandatory" or "Imperative" to highlight critical instructions.
    Write all titles in bold for emphasis.
    Question: {question}
    Context: {context}
    """,
    input_variables=["question", "document"],
)

rag_chain = prompt | llm | StrOutputParser()


### State
class GraphState(TypedDict):
    question : str
    generation : str
    web_search : str
    documents : List[str]


def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Chain
    retriever_chain = (retriever | format_docs)

    # Retrieval
    documents = retriever_chain.invoke(question)
    # print(documents)
    return {"documents": documents, "question": question}

def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]

    documents = state["documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question
    If any document is not relevant, we will set a flag to run web search

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Filtered out irrelevant documents and updated web_search state
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    # Score each doc
    filtered_docs = []
    web_search = "No"
    for d in documents:
        name_recipe = re.search(r'name_recipe:\s*(\S.*)', d).group(1)
        score = retrieval_grader.invoke({"question": question, "document": name_recipe})
        grade = score['score']
        # Document relevant
        if grade.lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        # Document not relevant
    if len(filtered_docs) == 0:
      print("---GRADE: DOCUMENT NOT RELEVANT---")
      # We do not include the document in filtered_docs
      # We set a flag to indicate that we want to run web search
      web_search = "Yes"
    return {"documents": filtered_docs, "question": question, "web_search": web_search}

def web_search(state):
    """
    Web search based based on the question

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Appended web results to documents
    """

    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    # Web search
    docs = spoonacular_search(question)
    web_results = "\n".join([d for d in docs])
    web_results = Document(page_content=web_results)
    if documents is not None:
        documents.append(web_results)
    else:
        documents = [web_results]
    return {"documents": documents, "question": question}


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or add web search

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    question = state["question"]
    web_search = state["web_search"]
    filtered_documents = state["documents"]

    if web_search == "Yes":
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, INCLUDE WEB SEARCH---")
        return "websearch"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"

workflow = StateGraph(GraphState)

workflow.add_node("websearch", web_search)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "websearch": "websearch",
        "generate": "generate",
    },
)
workflow.add_edge("websearch", "generate")
workflow.add_edge("generate", END)


app = workflow.compile()