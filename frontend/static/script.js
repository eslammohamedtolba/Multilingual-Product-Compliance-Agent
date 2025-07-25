document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const fileUpload = document.getElementById('file-upload');
    const fileNameSpan = document.getElementById('file-name');
    const clearHistoryButton = document.getElementById('clear-history-button');

    let selectedFile = null;
    let isSending = false; // Flag to prevent multiple sends
    let typingIndicatorElement = null; // To keep track of the typing indicator

    // Function to format text with basic markdown-like formatting
    function formatText(text) {
        if (!text) return '';
        
        // Convert the text to HTML with formatting
        let formattedText = text
            // Convert multiple *** to horizontal separators (3 or more asterisks)
            .replace(/^\*{3,}$/gm, '<hr class="text-separator">')
            // Convert ---+ to horizontal rule
            .replace(/^-{3,}$/gm, '<hr class="text-separator">')
            // Convert ### Header to h3 (handle spaces around ###)
            .replace(/^###\s*(.*?)\s*$/gm, '<h3 class="message-header">$1</h3>')
            // Convert ## Header to h2
            .replace(/^##\s*(.*?)\s*$/gm, '<h2 class="message-header">$1</h2>')
            // Convert # Header to h1
            .replace(/^#\s*(.*?)\s*$/gm, '<h1 class="message-header">$1</h1>')
            // Convert **text** to <strong>text</strong> (more flexible)
            .replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>')
            // Convert *text* to <em>text</em> (avoid conflicts with **)
            .replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em>$1</em>')
            // Convert standalone *** on lines to separators
            .replace(/^(.*)(\*{3,})(.*)$/gm, function(match, before, stars, after) {
                if (before.trim() === '' && after.trim() === '') {
                    return '<hr class="text-separator">';
                }
                return match; // Keep original if not standalone
            })
            // Convert bullet points starting with ***
            .replace(/^\*{3,}\s*([^*].+)$/gm, '<div class="bullet-point">• $1</div>')
            // Convert regular bullet points (lines starting with * or -)
            .replace(/^[\*\-]\s+(.+)$/gm, '<div class="bullet-point">• $1</div>')
            // Convert numbered lists (lines starting with numbers)
            .replace(/^(\d+)\.\s+(.+)$/gm, '<div class="numbered-point">$1. $2</div>')
            // Convert line breaks to <br> tags (do this last)
            .replace(/\n/g, '<br>');

        return formattedText;
    }

    // Function to add a message to the chat display
    function addMessage(type, content, fileInfo = null) { // Added fileInfo parameter
        const messageWrapper = document.createElement('div'); // Create a wrapper for message + file info
        messageWrapper.classList.add('message-wrapper'); // Add a class for styling

        // If it's a human message and has file information, add the file name above the bubble
        if (type.toLowerCase() === 'human' && fileInfo && fileInfo.file_name) {
            const fileNameDisplay = document.createElement('div');
            fileNameDisplay.classList.add('file-name-display'); // Class for styling
            // Use innerHTML to include the SVG icon
            fileNameDisplay.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16px" height="16px">
                    <path d="M0 0h24v24H0z" fill="none"/>
                    <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                </svg>
                ${fileInfo.file_name}
            `;
            messageWrapper.appendChild(fileNameDisplay); // Append to the wrapper
        }

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message-bubble');
       
        // Ensure type is always lowercase for class name consistency
        const messageClass = `${type.toLowerCase()}-message`;
        messageBubble.classList.add(messageClass);
        
        // Use innerHTML instead of textContent to render formatted HTML
        // Only format AI messages, keep human messages as plain text for security
        if (type.toLowerCase() === 'ai') {
            messageBubble.innerHTML = formatText(content);
        } else {
            messageBubble.textContent = content;
        }
        
        messageWrapper.appendChild(messageBubble); // Append bubble to wrapper

        chatContainer.appendChild(messageWrapper); // Append wrapper to container

        // Explicitly apply alignment style after appending (fallback for stubborn CSS issues)
        if (type.toLowerCase() === 'human') {
            messageWrapper.style.alignSelf = 'flex-end';
            messageWrapper.style.marginLeft = 'auto'; // Ensures it pushes to the right
            messageWrapper.style.marginRight = '0'; // Ensures no extra right margin
        } else if (type.toLowerCase() === 'ai') {
            messageWrapper.style.alignSelf = 'flex-start';
            messageWrapper.style.marginRight = 'auto'; // Ensures it pushes to the left
            messageWrapper.style.marginLeft = '0'; // Ensures no extra left margin
        }
       
        // Scroll to the bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return messageBubble; // Return the created element
    }

    // Function to add a system message (e.g., "History cleared")
    function addSystemMessage(content) {
        const systemMessage = document.createElement('div');
        systemMessage.classList.add('system-message');
        systemMessage.textContent = content;
        chatContainer.appendChild(systemMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // New function to add a typing indicator
    function addTypingIndicator() {
        if (typingIndicatorElement) {
            // If an indicator already exists, don't add another
            return;
        }
        typingIndicatorElement = document.createElement('div');
        typingIndicatorElement.classList.add('message-bubble', 'ai-message', 'typing-indicator'); // Add 'typing-indicator' class for specific styling
        typingIndicatorElement.innerHTML = '<div class="spinner"></div> Agent is processing your request...'; // Add a spinner div and optional text
        chatContainer.appendChild(typingIndicatorElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // New function to remove the typing indicator
    function removeTypingIndicator() {
        if (typingIndicatorElement && chatContainer.contains(typingIndicatorElement)) {
            chatContainer.removeChild(typingIndicatorElement);
            typingIndicatorElement = null; // Clear the reference
        }
    }

    // Function to toggle input and button states
    function toggleInputState(disabled) {
        // Only disable send and clear buttons when agent is responding
        sendButton.disabled = disabled || (!userInput.value.trim() && !selectedFile); // Re-evaluate send button state
        clearHistoryButton.disabled = disabled;
       
        // Allow typing and file selection even when agent is responding
        // userInput.disabled = disabled; // NO LONGER DISABLES TEXT INPUT
        // fileUpload.disabled = disabled; // NO LONGER DISABLES FILE INPUT

        // Removed opacity/pointer-events changes on input container
    }

    // Function to toggle send button active state based on input/file
    function toggleSendButton() {
        const hasTextInput = userInput.value.trim().length > 0;
        const hasFile = selectedFile !== null;
        sendButton.disabled = isSending || (!hasTextInput && !hasFile);
    }

    // Load chat history on page load
    async function loadChatHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            // Clear existing messages before adding history to prevent duplicates
            chatContainer.innerHTML = '';
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    // Pass the fileInfo to addMessage if it exists
                    addMessage(msg.type, msg.content, msg.file_info);
                });
            } else {
                addSystemMessage("Welcome! Start your conversation.");
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            addSystemMessage("Error loading chat history. Please try again.");
        }
    }

    // Send message function
    async function sendMessage() {
        if (isSending) return; // Prevent sending if already in progress

        const messageText = userInput.value.trim();
        if (!messageText && !selectedFile) {
            alert('Please enter a message or upload a file.');
            return;
        }

        isSending = true;
        toggleInputState(true); // Disable send and clear buttons

        // Display user's message immediately
        addMessage('human', messageText, selectedFile ? { file_name: selectedFile.name } : null);

        // Add typing indicator
        addTypingIndicator();

        const formData = new FormData();
        formData.append('message', messageText);
        if (selectedFile) {
            formData.append('file', selectedFile);
        }

        try {
            const response = await fetch('/api/send_message', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            // Display AI response directly
            addMessage('ai', data.ai_response);

            // Clear input and file after successful send
            userInput.value = '';
            fileUpload.value = ''; // Clear file input
            selectedFile = null;
            fileNameSpan.textContent = '';
            toggleSendButton(); // Re-evaluate send button state

        } catch (error) {
            console.error('Error sending message:', error);
            addSystemMessage(`Error: ${error.message || "Failed to get response from AI."}`);
        } finally {
            removeTypingIndicator(); // Always remove the indicator
            isSending = false;
            toggleInputState(false); // Re-enable send and clear buttons
            // DO NOT CALL loadChatHistory() here, it will re-add messages.
            // We are directly adding human and AI messages.
        }
    }

    // Clear history function
    async function clearChatHistory() {
        if (isSending) return; // Prevent clearing if agent is responding

        if (!confirm("Are you sure you want to clear the entire chat history? This action cannot be undone.")) {
            return;
        }

        isSending = true; // Temporarily block input while clearing
        toggleInputState(true); // Disable send and clear buttons

        try {
            const response = await fetch('/api/clear_history', {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                chatContainer.innerHTML = ''; // Clear frontend chat display
                addSystemMessage("Chat history cleared successfully. Start a new conversation!");
            } else {
                addSystemMessage(data.message || "Failed to clear history.");
            }
        } catch (error) {
            console.error('Error clearing history:', error);
            addSystemMessage(`Error clearing history: ${error.message || "Please try again."}`);
        } finally {
            isSending = false;
            toggleInputState(false); // Re-enable send and clear buttons
        }
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter' && !sendButton.disabled) {
            sendMessage();
        }
        toggleSendButton(); // Update button state on every keyup
    });

    fileUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            // Check file type
            const allowedTypes = ['text/plain', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
            if (!allowedTypes.includes(file.type)) {
                alert('Only .txt, .xlsx, and .xls files are allowed.');
                fileUpload.value = ''; // Clear the file input
                selectedFile = null;
                fileNameSpan.textContent = '';
                toggleSendButton();
                return;
            }
            selectedFile = file;
            fileNameSpan.textContent = file.name;
        } else {
            selectedFile = null;
            fileNameSpan.textContent = '';
        }
        toggleSendButton(); // Update button state
    });

    clearHistoryButton.addEventListener('click', clearChatHistory);

    // Initial load
    loadChatHistory(); // This will load any existing history only once on page load
    toggleSendButton(); // Set initial state of send button
});