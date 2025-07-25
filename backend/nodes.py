from .state import AgentState, Items, Analyze
from .config import llm, retrievers_by_lang
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Literal
from langchain_core.documents import Document

# --- Node 1: Parse User Input ---
def parse_input(state: AgentState) -> AgentState:
    """
    Parses the last human message to extract a list of product items
    and determine their language, solely using the LLM.
    Uses an LLM with PydanticOutputParser for structured output.
    Combines input bar text with file content if available in additional_kwargs.
    """
    last_message = state['messages'][-1]

    # Initialize the query for the LLM
    query_for_llm = last_message.content # Start with the text from the input bar

    # Check for file content in additional_kwargs if the message is a HumanMessage
    if isinstance(last_message, HumanMessage) and last_message.additional_kwargs:
        file_content = last_message.additional_kwargs.get("file_content")
        
        if file_content:
            # Combine the input bar text with the file content for LLM processing
            if query_for_llm:
                query_for_llm = f"{query_for_llm}\n{file_content}"
            else:
                query_for_llm = f"\n{file_content}"

    # Initialize PydanticOutputParser for the Items model
    parser = PydanticOutputParser(pydantic_object=Items)

    # Prompt template for extracting product names and their languages
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert assistant designed to extract a list of product names from user queries and determine their language. "
                     "Your goal is to identify all distinct product mentions, regardless of quantity or phrasing. "
                     "**Crucially, treat any text enclosed within double quotes (\") or single quotes (') as a single, indivisible product item, even if it contains words like 'or' or 'and'.** "
                     "For each extracted product, identify its dominant language as 'en' (English) or 'ar' (Arabic). "
                     "You must rely solely on the linguistic characteristics of the product name itself to determine its language. "
                     "If the product name contains a mix of English and Arabic characters, or is ambiguous, default to 'en'. "
                     "Return the extracted product names and their languages as a JSON array of objects, strictly following the provided schema. "
                     "If no product names are explicitly mentioned, return an empty list."),
        ("human", "User query: {query}\n\n{format_instructions}")
    ])

    # Create the parsing chain
    parsing_chain = prompt | llm.with_structured_output(Items)

    product_items_dict: Dict[str, Literal["en", "ar"]] = {}

    try:
        # Invoke the chain to parse the combined input message
        parsed_items: Items = parsing_chain.invoke({"query": query_for_llm, "format_instructions": parser.get_format_instructions()})
        for item_with_lang in parsed_items.products:
            product_items_dict[item_with_lang.name] = item_with_lang.language

    except Exception as e:
        pass

    return {
        'product_items': product_items_dict, # This will be empty if LLM parsing failed
        'items_retrieved_docs': {},
        'items_decisions': {}
    }

# --- Node 2: Retrieve Documents for All Items ---
def retrieve_documents_for_items(state: AgentState) -> AgentState:
    """
    Retrieves relevant documents for ALL product items in the 'product_items' dictionary
    from the appropriate language-specific vector database.
    Stores the retrieved documents in items_retrieved_docs.
    """
    product_items_dict = state['product_items']
    items_retrieved_docs = state['items_retrieved_docs']

    if not product_items_dict:
        return state

    for item, lang in product_items_dict.items(): # Iterate over dict items

        # Select the correct retriever based on detected language
        current_retriever = retrievers_by_lang.get(lang)

        if current_retriever is None:
            items_retrieved_docs[item] = []
            continue

        # Perform retrieval for the current item using the correct language retriever
        semantic_docs: List[Document] = current_retriever.invoke(item)
        items_retrieved_docs[item] = semantic_docs

    return {
        'items_retrieved_docs': items_retrieved_docs
    }

# --- Node 3: Analyze Product Match for All Items ---
def analyze_product_match(state: AgentState) -> AgentState:
    """
    Analyzes whether each product item is listed and if it requires
    a Local Content Certificate, using an LLM and structured output.
    This node processes all items in 'product_items'.
    """
    product_items_dict = state['product_items'] # Still iterating over the dictionary keys
    items_retrieved_docs = state['items_retrieved_docs']
    items_decisions = state['items_decisions'] # Will be populated in this node

    if not product_items_dict:
        return state

    # Initialize PydanticOutputParser for the Analyze model
    parser = PydanticOutputParser(pydantic_object=Analyze)

    # Prompt template for analyzing product match and certificate requirement
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert AI agent tasked with determining if a product is listed in a mandatory list "
         "and if it requires a Local Content Certificate, based on provided documents. "
         "Follow these strict rules:\n"
         "1. **Listing Determination**: Carefully examine the 'Document Content' and 'Metadata' of the provided documents. "
         "   Set 'Listed' to True ONLY if the 'item' (product name) is clearly and explicitly mentioned or a perfect semantic match is found "
         "   in the 'Commodity Title (Arabic)' or 'Commodity Title (English)' from the documents. "
         "   If there's no clear match or the product is not found, set 'Listed' to False.\n"
         "2. **Local Content Certificate Determination**: "
         "   - If 'Listed' is False, then 'Content_Certificate' MUST be False. A certificate is irrelevant if the product isn't listed.\n"
         "   - If 'Listed' is True, then check the 'Manufacturer Local Content Minimum Baseline' field within the metadata of the matching document. "
         "     Set 'Content_Certificate' to True if this field explicitly indicates a requirement (e.g. 'يشترط', 'نعم', 'Required', 'Yes', or a specific percentage value like '30%', '15%'). "
         "     Set 'Content_Certificate' to False if the field indicates no requirement (e.g., 'لا يوجد', 'لا يشترط', 'No', 'Not Required', or is empty/null).\n"
         "3. **Reasoning**: Provide a concise but clear explanation for both decisions. "
         "   If 'Listed' is True, mention the exact matching commodity title from the document and the value of 'Manufacturer Local Content Minimum Baseline'. "
         "   If 'Listed' is False, explain why (e.g., 'no clear match found').\n"
         "4. **Output Format**: Strictly adhere to the JSON schema for the 'Analyze' model provided below. "
         "   Ensure the 'item' field in your output exactly matches the input product item."
        ),
        ("human",
         "Analyze the following product using the provided documents:\n"
         "Product Item: {item}\n\n"
         "Retrieved Documents:\n{documents}\n\n"
         "{format_instructions}"
        )
    ])

    # Create the analysis chain
    analysis_chain = prompt | llm.with_structured_output(Analyze)

    for item, lang in product_items_dict.items(): # Iterate over dict items. Lang is available but not used here.
        current_item = item
        retrieved_docs_for_item = items_retrieved_docs.get(current_item, [])

        # Format retrieved documents for the LLM prompt
        formatted_docs = "\n---\n".join([
            f"Document Content: {doc.page_content}\nMetadata: {doc.metadata}"
            for doc in retrieved_docs_for_item
        ])
        if not formatted_docs:
            formatted_docs = "No relevant documents were found for this product in the mandatory list."

        try:
            # Invoke the chain to analyze the current item
            analysis_result: Analyze = analysis_chain.invoke({
                "item": current_item,
                "documents": formatted_docs,
                "format_instructions": parser.get_format_instructions()
            })

            # Enforce the Content_Certificate logic explicitly after LLM generation
            if not analysis_result.Listed:
                analysis_result.Content_Certificate = False
                analysis_result.reasoning += " (Content Certificate set to False because product is not listed)."

            items_decisions[current_item] = analysis_result
            
        except Exception as e:
            # Store a default/error analysis if LLM fails
            items_decisions[current_item] = Analyze(
                item=current_item,
                Listed=False,
                Content_Certificate=False,
                reasoning=f"Analysis failed due to an internal error: {e}. Could not determine listing or certificate requirement."
            )

    return {
        'items_decisions': items_decisions
    }

# --- Node 4: Prepare Final Output ---
def prepare_final_output(state: AgentState) -> AgentState:
    """
    Aggregates all item decisions into a single, comprehensive, and user-friendly final answer.
    """
    items_decisions = state['items_decisions']
    
    # Format the decisions into a clear string for the LLM
    decisions_summary = []
    for item, decision in items_decisions.items():
        listed_status = "Listed in Mandatory List" if decision.Listed else "NOT Listed in Mandatory List"
        certificate_status = "REQUIRES Local Content Certificate" if decision.Content_Certificate else "DOES NOT require Local Content Certificate"
        decisions_summary.append(
            f"- Product: '{decision.item}'\n"
            f"  Status: {listed_status}.\n"
            f"  Certificate: {certificate_status}.\n"
            f"  Reasoning: {decision.reasoning}\n"
        )
    
    formatted_decisions = "\n".join(decisions_summary)
    if not formatted_decisions:
        formatted_decisions = "No products were analyzed or processed."

    # Prompt template for generating the final answer
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an AI assistant providing a final summary of product analysis. "
         "Present the results clearly and concisely. For each product, state whether it's listed "
         "in the mandatory list and if it requires a Local Content Certificate. "
         "Include the reasoning provided for each decision. "
         "Ensure the output is easy to read and understand for the user."
        ),
        ("human", 
         "Here are the analysis results for the requested products:\n\n{decisions_summary}\n\n"
         "Please provide a final, comprehensive summary for the user."
        )
    ])

    # Create the final answer generation chain
    final_answer_chain = prompt | llm

    try:
        final_answer_message = final_answer_chain.invoke({"decisions_summary": formatted_decisions})
        final_answer = final_answer_message.content
    except Exception as e:
        final_answer = "An error occurred while compiling the final report."

    return {
        'messages': [AIMessage(content=final_answer)]
    }