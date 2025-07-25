from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Sequence, List, Dict, Literal # Added Literal
from langgraph.graph.message import add_messages
from langchain_core.documents import Document

# Define the overall state for the LangGraph agent
class AgentState(TypedDict):
    """
    Represents the state of the AI agent throughout its execution.

    Attributes:
        messages (Annotated[Sequence, add_messages]): A sequence of messages forming the chat history.
                                                      Includes user inputs, agent thoughts, and final responses.
        product_items (Dict[str, Literal["en", "ar"]]): A dictionary mapping each product name
                                                           to its detected language ("en" for English, "ar" for Arabic).
                                                           This guides which ChromaDB to query.
        items_retrieved_docs (Dict[str, List[Document]]): A dictionary mapping each product item
                                                          to a list of relevant documents retrieved
                                                          from the vector database.
        items_decisions (Dict[str, 'Analyze']): A dictionary mapping each product item
                                                to its analysis result, structured by the Analyze BaseModel.
                                                This includes whether it's listed and if a Local Content Certificate
                                                is required.
    """
    messages: Annotated[Sequence, add_messages]
    product_items: Dict[str, Literal["en", "ar"]] # Changed to Dict[str, Literal["en", "ar"]]
    items_retrieved_docs: Dict[str, List[Document]]
    items_decisions: Dict[str, 'Analyze']


# Pydantic model for parsing user input into a structured list of product names and their languages
class ProductItemWithLanguage(BaseModel):
    name: str = Field(description="The distinct product name extracted.")
    language: Literal["en", "ar"] = Field(description="Detected language of the product name: 'en' for English, 'ar' for Arabic.")

class Items(BaseModel):
    """
    Represents a list of product names extracted from user input, along with their detected languages.
    This model is used to guide the LLM in parsing natural language queries.
    """
    products: List[ProductItemWithLanguage] = Field(
        description="A list of distinct product names mentioned by the user, each with its detected language. "
                    "Each element in the list should be a single product name and its language ('en' or 'ar'). "
                    "Extract all product names, even if they are similar or belong to the same category. "
                    "**Crucially, treat any text enclosed within double quotes (\") or single quotes (') as a single, indivisible product item.** "
                    "Determine the language of each product item based on the characters used (e.g., Arabic script implies 'ar', Latin script implies 'en')."
    )

# Pydantic model for structuring the LLM's analysis output for each product
class Analyze(BaseModel):
    """
    Represents the analysis result for a single product item.
    This model guides the LLM to output structured data regarding product listing
    and Local Content Certificate requirements.
    """
    item: str = Field(
        description="The exact name of the product item being analyzed, as provided in the input list."
    )
    Listed: bool = Field(
        description="True if the product item is found in the mandatory list based on the provided documents. "
                    "False if the product item is not found or cannot be definitively identified in the list."
    )
    Content_Certificate: bool = Field(
        description="True if the product is listed AND explicitly mandates a 'Local Content Certificate (baseline)' "
                    "according to the retrieved documents. "
                    "If 'Listed' is False, then 'Content_Certificate' MUST also be False, as a certificate "
                    "is only relevant for listed products. "
                    "If 'Listed' is True, extract the value from 'Manufacturer Local Content Minimum Baseline' "
                    "field in the retrieved document. If this field indicates a requirement (e.g., 'يشترط', 'نعم', 'Required', 'Yes', or a specific percentage), set to True. "
                    "Otherwise, if it indicates 'لا يوجد', 'لا يشترط', 'No', 'Not Required', or is empty/null, set to False."
    )
    reasoning: str = Field(
        description="A brief explanation for the 'Listed' and 'Content_Certificate' decisions. "
                    "If listed, mention the matching product name from the document and the "
                    "exact value of 'Manufacturer Local Content Minimum Baseline'. "
                    "If not listed, explain why (e.g., 'no clear match found in the mandatory list')."
    )