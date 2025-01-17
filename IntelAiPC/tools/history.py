import uuid
import json

class History:
    """
    Manages LLM chat history with user tracking using UUID.
    
    Chat history follows the structure:
    [{"role": "system", "content": "message"}, {"role": "user", "content": "message"}]
    """

    def __init__(self):
        """
        Initializes the History with an empty dictionary for user chat history.
        """
        self.user_histories = {}

    def generate_conversation_id(self) -> str:
        """
        Generates a unique user ID using UUID.

        Returns:
            str: A unique UUID string for the user.
        """
        return str(uuid.uuid4())

    def add_message(self, conversation_id: str, role: str, content: str):
        """
        Adds a message to the user's chat history.

        Args:
            conversation_id (str): The unique identifier for the user.
            role (str): The message sender's role ("system", "user", "genisys").
            content (str): The message content.

        Raises:
            ValueError: If an invalid role is provided.
        """
        allowed_roles = {"system", "user", "genisys"}
        if role not in allowed_roles:
            raise ValueError(f"Invalid role '{role}'. Allowed roles are: {allowed_roles}")

        if conversation_id not in self.user_histories:
            self.user_histories[conversation_id] = []

        self.user_histories[conversation_id].append({"role": role, "content": content})

        self.log_message(conversation_id, {"role": role, "content": content})

    def log_message(self, user_id, chat_data):
        """
        Appends the chat log data to the specified log file, using user ID and path.
        
        Args:
            user_id (str): The user ID (used as the file name).
            chat_data (dict): Dictionary containing 'role' and 'content' of the chat log.
        """
        if user_id and chat_data:
            # Ensure we have the necessary data in the chat_data
            chat_entry = {
                "role": chat_data.get("role", ""),
                "content": chat_data.get("content", "")
            }
            
            # Define the file path using user_id as the file name
            file_path = f"logs/chat/{user_id}.json"
            
            # Append the chat log as a new entry in the JSON file
            try:
                with open(file_path, "a") as log_file:
                    log_file.write(json.dumps(chat_entry) + '\n')
            except Exception as e:
                print(f"Error appending to the log file: {e}")
                
    def get_history(self, conversation_id: str) -> list:
        """
        Retrieves the complete chat history for a user.

        Args:
            conversation_id (str): The unique user ID.

        Returns:
            list: The user's chat history.
        """
        return self.user_histories.get(conversation_id, [])

    def clear_history(self, conversation_id: str):
        """
        Clears the chat history for a specified user.

        Args:
            conversation_id (str): The unique user ID.
        """
        self.user_histories.pop(conversation_id, None)

    def format_history(self, conversation_id: str) -> str:
        """
        Formats the chat history as a readable string for logging or output.

        Args:
            conversation_id (str): The unique user ID.

        Returns:
            str: The formatted chat history.
        """
        history = self.get_history(conversation_id)
        return "\n".join([f"{entry['role']}: {entry['content']}" for entry in history])
