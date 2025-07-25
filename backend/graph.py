from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from .nodes import (
    parse_input, 
    retrieve_documents_for_items, 
    analyze_product_match, 
    prepare_final_output,
    AgentState
)

# Define the path for the SQLite database for checkpointer
SQLITE_CHECKPOINT_PATH = r"backend\db.sqlite"

def create_agent_graph():
    """
    Creates and compiles the LangGraph agent workflow.

    The graph defines the sequence of operations for processing product queries:
    1. Parse user input to extract product items.
    2. Retrieve relevant documents for all extracted product items from the vector database.
    3. Analyze each product item to determine if it's listed and requires a certificate.
    4. Prepare a final, comprehensive output for the user.

    Returns:
        CompiledGraph: The compiled LangGraph agent ready to be invoked.
    """
    # Initialize the StateGraph with the defined AgentState
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("parse_input", parse_input)
    graph.add_node("retrieve_documents", retrieve_documents_for_items)
    graph.add_node("analyze_products", analyze_product_match)
    graph.add_node("prepare_final_output", prepare_final_output)

    # Set the entry point
    graph.set_entry_point("parse_input")

    # Define the edges (transitions between nodes) (The flow is sequential)
    graph.add_edge("parse_input", "retrieve_documents")
    graph.add_edge("retrieve_documents", "analyze_products")
    graph.add_edge("analyze_products", "prepare_final_output")
    graph.add_edge("prepare_final_output", END)

    # Configure the checkpointer for state persistence
    memory = SqliteSaver.from_conn_string(SQLITE_CHECKPOINT_PATH)

    # Create connection and memory
    sqlite_conn = sqlite3.connect(SQLITE_CHECKPOINT_PATH, check_same_thread=False)
    memory = SqliteSaver(conn=sqlite_conn)

    # Compile the graph
    return graph.compile(checkpointer=memory)
