
import csv
import tracery
from tracery.modifiers import base_english
import random
from .config import MAX_CONVERSATION_ROUNDS, get_logger, BASE_DIR,INITIAL_COMPLAINT,CUSTOMER_FOLLOWUP,HELPDESK_RESPONSE
from datetime import datetime, timedelta

logger = get_logger(__name__)

# Helper function to load CSV elements (assumes one phrase per row)
def load_csv_elements(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader if row]

# Load the CSV content into grammar rules
grammar_rules = {
    "initial_complaint": load_csv_elements(INITIAL_COMPLAINT),
    "customer_followup": load_csv_elements(CUSTOMER_FOLLOWUP),
    "helpdesk_response": load_csv_elements(HELPDESK_RESPONSE),
    "greeting": ["HELP", "URGENT", "Attention"]
}
def generate_ticket_conversation():
    """
    Generates a helpdesk ticket conversation as a single string with newline-separated messages.
    """
    grammar = tracery.Grammar(grammar_rules)
    grammar.add_modifiers(base_english)
    
    conversation_lines = []
    random_rounds = random.randint(1, MAX_CONVERSATION_ROUNDS)
    
    # Generate initial customer complaint
    greeting = random.choice(grammar.flatten("#greeting#").split())
    initial_complaint = grammar.flatten("#initial_complaint#")
    conversation_lines.append("Customer: " + f"{greeting}: {initial_complaint}")
    
    # Generate back-and-forth conversation based on num_rounds
    for i in range(random_rounds):
        helpdesk_msg = grammar.flatten("#helpdesk_response#")
        conversation_lines.append("Helpdesk: " + helpdesk_msg)
        if i < random_rounds - 1:
            customer_msg = grammar.flatten("#customer_followup#")
            conversation_lines.append("Customer: " + customer_msg)
    
    return "\n".join(conversation_lines)
def generate_ticket_conversation_structured():
    """
    Generates a structured helpdesk ticket conversation as a list of dictionaries.
    
    Each dictionary contains:
      - 'speaker': Either "Customer" or "Helpdesk"
      - 'message': The content of the message
      
    Returns:
        Tuple[List[Dict[str, str]], int]: Conversation list and number of rounds
    """
    random_rounds = random.randint(1, MAX_CONVERSATION_ROUNDS)
    logger.info(f"Generating ticket conversation with {random_rounds} rounds.")

    grammar = tracery.Grammar(grammar_rules)
    grammar.add_modifiers(base_english)
    logger.info("Grammar initialized with modifiers.")

    conversation = []

    # Generate initial customer complaint
    greeting = random.choice(grammar.flatten("#greeting#").split())
    initial_complaint = grammar.flatten("#initial_complaint#")
    first_message = f"{greeting}: {initial_complaint}"
    conversation.append({"speaker": "Customer", "message": first_message})
    logger.info(f"Added initial customer complaint: {first_message}")

    # Generate back-and-forth conversation based on random_rounds
    for i in range(random_rounds):
        helpdesk_msg = grammar.flatten("#helpdesk_response#")
        conversation.append({"speaker": "Helpdesk", "message": helpdesk_msg})
        logger.info(f"Round {i+1}: Added helpdesk response: {helpdesk_msg}")

        if i < random_rounds - 1:
            customer_msg = grammar.flatten("#customer_followup#")
            conversation.append({"speaker": "Customer", "message": customer_msg})
            logger.info(f"Round {i+1}: Added customer follow-up: {customer_msg}")

    logger.info(f"Generated structured conversation with {len(conversation)} messages.")
    return conversation

def generate_conversation_timestamps(start_time, end_time, number_of_messages):
    """
    Generates a list of timestamps for a ticket conversation.
    
    - Ensures timestamps are within start_time and end_time.
    - Uses 5-minute increments.
    - Generates `random_rounds - 2` timestamps (excluding start and end).
    
    Args:
        start_time (datetime): The start time of the conversation.
        end_time (datetime): The end time of the conversation.
        random_rounds (int): The total number of messages in the conversation.

    Returns:
        List[datetime]: A sorted list of timestamps including start and end.
    """
    logger.info(f"for generate_conversation_timestamps the passed in variables are {start_time} {end_time} {number_of_messages}")
    try:
        logger.info(f"Generating timestamps for conversation. Start: {start_time}, End: {end_time}, Messages: {number_of_messages}")

        if number_of_messages < 2:
            logger.warning("Random rounds less than 2. Returning only start and end timestamps.")
            return [start_time, end_time]  # Minimum start and end timestamps
        
        total_duration = (end_time - start_time).total_seconds() // 60  # Total minutes
        max_possible_intervals = total_duration // 1  # Max 5-min intervals available

        logger.info(f"Total duration: {total_duration} minutes. Max possible 5-min intervals: {max_possible_intervals}")

        if max_possible_intervals < number_of_messages - 2:
            error_msg = f"Not enough time for the requested number of rounds ({number_of_messages}) with 5-minute intervals."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Generate random offsets in 5-minute increments
        random_offsets = sorted(random.sample(range(5, int(total_duration), 5), number_of_messages - 2))
        logger.info(f"Generated random offsets (minutes): {random_offsets}")

        # Convert to timestamps
        conversation_timestamps = [start_time + timedelta(minutes=offset) for offset in random_offsets]

        # Ensure start_time and end_time are included
        conversation_timestamps.insert(0, start_time)
        conversation_timestamps.append(end_time)

        logger.info(f"Generated {len(conversation_timestamps)} timestamps for conversation.")

        return conversation_timestamps

    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
    except Exception as e:
        logger.error(f"Unexpected error in generate_conversation_timestamps: {e}", exc_info=True)

    return [start_time, end_time] 

def create_complete_ticket_conversation(ticket):
    """
    Generates a structured ticket conversation with timestamps.

    Args:
        ticket (dict): Ticket details containing ticket number, assigned tech, contact, start time, and end time.

    Returns:
        List[dict]: Structured conversation with timestamps, or an empty list if an error occurs.
    """
    structured_conversation = []
    
    try:
        # Validate required fields
        required_fields = ["Customer","Ticket Number", "Assigned Tech", "Contact", "Start Time", "End Time"]
        for field in required_fields:
            if field not in ticket or ticket[field] is None:
                raise ValueError(f"Missing or invalid ticket field: {field}")

        customer = ticket["Customer"]
        ticket_number = ticket["Ticket Number"]
        tech = ticket["Assigned Tech"]
        contact = ticket["Contact"]
        start_time = ticket["Start Time"]
        end_time = ticket["End Time"]
        
        logger.info(f"Creating conversation for Ticket #{ticket_number}")
        logger.info(f"Ticket details: Tech - {tech}, Contact - {contact}, Start - {start_time}, End - {end_time}")

        # Generate conversation and timestamps
        conversation = generate_ticket_conversation_structured()
        
        number_of_messages = len(conversation)
        logger.info(f"Generated conversation with {number_of_messages} rounds.")
        logger.info(f"passing {start_time} {end_time} with the number of messages: {number_of_messages}")
        conversation_timestamps = generate_conversation_timestamps(start_time, end_time, number_of_messages)        

        # Ensure timestamps and conversation lengths match
        if len(conversation) != len(conversation_timestamps):
            logger.error(f"number  of conversation  rounds is {len(conversation)/2}, but there are {len(conversation_timestamps)} timestamps.")
            raise ValueError("Mismatch between conversation messages and timestamps.")       
        logger.info(f" the type of variable conversation is {type(conversation)}")
        for index, message in enumerate(conversation):

            logger.info(f"Processing message {index+1}/{len(conversation)}")

            speaker = contact if message["speaker"] == "Customer" else tech
            individual_message = {
                "Customer": customer,
                "Ticket Number": ticket_number,
                "speaker": speaker,
                "message": message["message"],  
                "timestamp": conversation_timestamps[index]  # Assign correct timestamp
            }

            structured_conversation.append(individual_message)
            logger.info(f"Added message {index+1}/{len(conversation)} - Speaker: {individual_message['speaker']}, Timestamp: {individual_message['timestamp']}")

        logger.info(f"Completed structured conversation for Ticket #{ticket_number}. Total messages: {len(structured_conversation)}")

    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
    except KeyError as ke:
        logger.error(f"KeyError: Missing key in ticket data - {ke}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)  # Logs traceback for debugging

    return structured_conversation

# Example usage:
if __name__ == '__main__':
    print("this file is not meant to run directly")
    start_time = datetime(2025, 3, 1, 10, 0)  # 10:00 AM
    end_time = datetime(2025, 3, 7, 12, 30)   # 12:30 PM
    random_rounds = 5  # 5 messages in total

    timestamps = generate_conversation_timestamps(start_time, end_time, random_rounds)
    for ts in timestamps:
        print(ts)