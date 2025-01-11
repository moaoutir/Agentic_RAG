
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
from .macro_calculator_utils import macro_nutrition
from .sql_alchemy_utils import  get_user_data, initialize_database


def format_docs(docs):
    formatted_docs = [
        "metadata: " + str(doc.metadata) + " name_recipe:" + doc.page_content
        for doc in docs
    ]
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
    user_id : str
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


    # Retrieval
    documents = retriever.invoke(question)
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
        # name_recipe = re.search(r'name_recipe:\s*(\S.*)', d).group(1)
        score = retrieval_grader.invoke({"question": question, "document": d.page_content})
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



def recipe_recommendation(state):
    """
    Recipe recommendation based on user macro nutrition requirements
    """

    print("---RECIPE RECOMMENDATION---")
    initialize_database()
    user_id = state["user_id"]
    documents = state["documents"]
    
    user_data = get_user_data(user_id)
    if user_data:
        calories, calories_in_protein, calories_in_carbs, calories_in_fat = macro_nutrition(user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6])
        
        if calories > documents[0].metadata['Calories'] and calories_in_protein > documents[0].metadata['ProteinContent'] and \
        calories_in_carbs > documents[0].metadata['CarbohydrateContent'] and calories_in_fat > documents[0].metadata['FatContent']:
            print("Recipe is suitable for user")
        else:
            print("Recipe is not suitable for user")    

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
workflow.add_node("recipe_recommendation", recipe_recommendation)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "websearch": "websearch",
        "generate": "recipe_recommendation",
    },
)
workflow.add_edge("websearch", "recipe_recommendation")
workflow.add_edge("recipe_recommendation", "generate")
workflow.add_edge("generate", END)


app = workflow.compile()