from .workflow import workflow
from pprint import pprint


app = workflow.compile()

def langGraph_function(question: str):
    """
    Runs the compiled workflow with the given question.
    
    Args:
        question (str): The input question for the workflow.
    
    Returns:
        str: The generation result from the workflow.
    """
    print(f"Running workflow with question: {question}")
    inputs = {"question": question}
    value = None
    for output in app.stream(inputs):
        for key, value in output.items():
            pprint(f"Finished running: {key}:")
    if value is not None:
        return value["generation"]
    else:
        raise ValueError("No generation result returned from workflow.")

#if __name__ == "__main__":
#    langGraph_function("pizza")
