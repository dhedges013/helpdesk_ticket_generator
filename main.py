from src.generate_ticket_data import generate_ticket
from src.utils import append_dict_to_csv
from src.config import get_logger
from src.conversations import create_complete_ticket_conversation

logger = get_logger(__name__)

def main():   
    try:
        num_tickets = input("Enter the number of tickets to generate: ")
        if not num_tickets.isdigit() or int(num_tickets) <= 0:
            print("Invalid input. Please enter a positive integer.")
            return        

        num_tickets = int(num_tickets)
        tickets_list = []
        conversations_list = []

        for _ in range(num_tickets):
            try:
                ticket = generate_ticket()
                if ticket is None:
                    logger.error("Failed to generate a ticket. Skipping...")
                    continue  # Skip instead of stopping

                logger.info(f"Generated ticket: {ticket}")
                tickets_list.append(ticket)

                conversation = create_complete_ticket_conversation(ticket)
                if not conversation:
                    logger.error(f"Failed to generate a conversation for Ticket #{ticket.get('Ticket Number', 'Unknown')}. Skipping...")
                    continue  # Skip instead of stopping

                logger.info(f"For ticket {ticket['Ticket Number']} Generated conversation: {conversation}")            
                conversations_list.extend(conversation)  # Flatten list

            except Exception as e:
                logger.error(f"Error processing ticket: {e}", exc_info=True)
                continue  # Skip to next ticket instead of failing everything

        if not tickets_list or not conversations_list:
            logger.error("No valid tickets or conversations generated. Exiting.")
            return

        logger.info(f"Completed generating data for {len(tickets_list)} tickets")
        logger.info(f"Tickets list type: {type(tickets_list)}, Conversations list type: {type(conversations_list)}")

        # Debug ticket data
        logger.info(f"First ticket: {tickets_list[0] if tickets_list else 'No tickets generated'}")
        logger.info(f"First conversation: {conversations_list[0] if conversations_list else 'No conversations generated'}")

        # Convert lists to dictionaries
        try:
            ticket_dict = {key: [ticket[key] for ticket in tickets_list] for key in tickets_list[0].keys()}
            logger.info("Converted tickets to dictionary format.")

            # Handle conversations properly
            if isinstance(conversations_list, list) and all(isinstance(item, dict) for item in conversations_list):
                conversations_dict = {key: [conversation[key] for conversation in conversations_list] for key in conversations_list[0].keys()}
                logger.info("Converted conversations to dictionary format.")
            else:
                logger.error("Unexpected structure in conversations_list.")
                return

            # Save to CSV
            append_dict_to_csv(ticket_dict, conversations_dict)
            print(f"{len(tickets_list)} tickets successfully saved")

        except Exception as e:
            logger.error(f"Error processing dictionaries: {e}", exc_info=True)
            return

    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}", exc_info=True)
        print(f"Error during ticket generation: {e}")

    logger.info("Application finished.")

if __name__ == "__main__":
    main()
