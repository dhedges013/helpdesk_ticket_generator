from src.generate_ticket_data import generate_ticket
from src.conversations import create_complete_ticket_conversation

def generate_single_ticket():
    """Generate a single ticket with a conversation."""
    ticket = generate_ticket()
    if ticket is None:
        return None, "Failed to generate ticket"

    conversation = create_complete_ticket_conversation(ticket)
    if not conversation:
        return None, "Failed to generate conversation"

    return {"ticket": ticket, "conversation": conversation}, None
