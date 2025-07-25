from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import Optional
import pandas as pd
from io import BytesIO

# Import your existing modules
from .graph import create_agent_graph
from .state import AgentState
from langchain_core.messages import HumanMessage
from .db_utils import delete_conversation

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Create uploads directory if it doesn't exist (though not strictly used for saving here)
os.makedirs("uploads", exist_ok=True)

# Initialize the agent
agent_app = create_agent_graph()

# Configuration for the agent
invoke_config = {
    "configurable": {
        "thread_id": 1,
        "recursion_limit": 50
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/history")
async def get_chat_history():
    """Get chat history from the agent"""
    try:
        # Get the current state/history
        history = agent_app.get_state(invoke_config)

        # Check if there are messages in history
        if not history or not history.values:
            return {"messages": []}

        messages = history.values.get('messages', [])

        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, 'content'):
                message_type = "human" if msg.__class__.__name__ == "HumanMessage" else "ai"
                
                # Extract file metadata if it exists for HumanMessage
                file_info = None
                if message_type == "human" and hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                    if "file_name" in msg.additional_kwargs:
                        file_info = {
                            "file_name": msg.additional_kwargs["file_name"]
                        }

                formatted_messages.append({
                    "type": message_type,
                    "content": msg.content,
                    "file_info": file_info # Include file info for frontend display
                })

        return {"messages": formatted_messages}
    except Exception as e:
        return {"messages": []}

@app.post("/api/send_message")
async def send_message(message: str = Form(...), file: Optional[UploadFile] = File(None)):
    """Process user message and file upload, storing file content in additional_kwargs."""
    try:
        user_input_message = message.strip() # This is the text from the input bar
        
        additional_kwargs = {}
        file_processing_note = ""

        if file:
            file_name = file.filename if file.filename else "uploaded file"
            additional_kwargs["file_name"] = file_name
            
            try:
                file_content = await file.read()
                
                # Determine file type and process accordingly
                if file_name.lower().endswith('.txt'):
                    # Handle text files
                    file_text = file_content.decode('utf-8')
                    additional_kwargs["file_content"] = file_text
                    
                elif file_name.lower().endswith(('.xlsx', '.xls')):

                    # Read Excel file into DataFrame
                    df = pd.read_excel(BytesIO(file_content))
                    
                    # Convert DataFrame to readable text format
                    file_text = df.to_string(index=False)  # or df.to_csv(index=False)
                    additional_kwargs["file_content"] = file_text
                    
                else:
                    file_processing_note = f"[Note: File type not supported for '{file_name}']"
                    additional_kwargs["file_content"] = file_processing_note
                
            except Exception as file_read_e:
                file_processing_note = f"[Note: Error reading uploaded file '{file_name}']"
                additional_kwargs["file_content"] = file_processing_note

        # If only a file was uploaded and no message, or if message is empty and file failed processing
        if not user_input_message and not additional_kwargs.get("file_content"):
            raise HTTPException(status_code=400, detail="Cannot send empty message or unreadable file.")
        
        # Create the HumanMessage with content only from the input bar, and file details in kwargs
        current_state: AgentState = {
            "messages": HumanMessage(content=user_input_message, additional_kwargs=additional_kwargs),
            "product_items": [],
            "items_retrieved_docs": {},
            "items_decisions": {}
        }
        
        # Process with the agent
        final_state = agent_app.invoke(current_state, config=invoke_config)
        
        # Get the AI response
        ai_response = final_state['messages'][-1].content
        
        # The user_message returned to the frontend will only be the text from the input bar
        # plus any file processing notes for immediate feedback to the user if needed.
        display_user_message = user_input_message
        if file_processing_note:
            if display_user_message:
                display_user_message = f"{display_user_message}\n\n{file_processing_note}"
            else:
                display_user_message = file_processing_note

        return {
            "success": True,
            "user_message": display_user_message,
            "ai_response": ai_response,
            "file_info": {"file_name": additional_kwargs.get("file_name")} if "file_name" in additional_kwargs else None
        }
        
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/api/clear_history")
async def clear_history():
    """Clear chat history from the database."""
    try:
        thread_id_to_clear = str(invoke_config['configurable']['thread_id'])
        deleted = delete_conversation(thread_id_to_clear)
        if deleted:
            return {"success": True, "message": f"History for thread_id {thread_id_to_clear} cleared successfully."}
        else:
            return {"success": False, "message": f"No history found or nothing to clear for thread_id {thread_id_to_clear}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


