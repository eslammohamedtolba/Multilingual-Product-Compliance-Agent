import sqlite3

SQLITE_CHECKPOINT_PATH = r"backend\db.sqlite"



def get_db_connection():

    """Establishes a connection to the SQLite database."""

    return sqlite3.connect(SQLITE_CHECKPOINT_PATH, check_same_thread=False)



def delete_conversation(thread_id: str) -> bool:
    """
    Deletes a conversation from its associated LangGraph checkpoint.
    """
    with get_db_connection() as conn:

        cursor = conn.cursor()

        # Delete from LangGraph's checkpoints
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))

        rows_deleted = cursor.rowcount
        conn.commit()

        return rows_deleted > 0