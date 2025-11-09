from src.generate_ticket_data import generate_ticket
from src.conversations import create_complete_ticket_conversation
from src.time_entries import generate_time_entries

def generate_single_ticket():
    """Generate a single ticket with conversation and time entry data."""
    ticket = generate_ticket()
    if ticket is None:
        return None, "Failed to generate ticket"

    conversation = create_complete_ticket_conversation(ticket)
    if not conversation:
        return None, "Failed to generate conversation"

    time_entries = generate_time_entries(ticket) or []

    return {
        "ticket": ticket,
        "conversation": conversation,
        "time_entries": time_entries,
    }, None
