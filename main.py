from src import preferences
from src.generate_ticket_data import generate_ticket
from src.utils import append_dict_to_csv
from src.config import get_logger
from src.conversations import create_complete_ticket_conversation
from src.time_entries import generate_time_entries
from src.ticket_review import prompt_for_ticket_review
from src.generation_context import GenerationContext

logger = get_logger(__name__)

def main():

    try:
        stored_tickets = preferences.get_int("num_tickets")
        if stored_tickets and stored_tickets > 0:
            num_tickets = stored_tickets
            print(f"Enter the number of tickets to generate: {num_tickets} (remembered).")
        else:
            num_tickets_input = input("Enter the number of tickets to generate: ").strip()
            if not num_tickets_input.isdigit() or int(num_tickets_input) <= 0:
                print("Invalid input. Please enter a positive integer.")
                return
            num_tickets = int(num_tickets_input)
            preferences.remember_int("num_tickets", num_tickets)
        context = GenerationContext()
        tickets_list = []
        conversations_list = []
        time_entries_list = []

        for _ in range(num_tickets):
            try:
                ticket = generate_ticket(context)
                if ticket is None:
                    logger.error("Failed to generate a ticket. Skipping...")
                    continue  # Skip instead of stopping

                logger.info(f"Generated ticket: {ticket}")
                ticket = context.validate_ticket(ticket)
                tickets_list.append(ticket)

                conversation = create_complete_ticket_conversation(ticket)
                if not conversation:
                    logger.error(f"Failed to generate a conversation for Ticket #{ticket.get('Ticket Number', 'Unknown')}. Skipping...")
                    continue  # Skip instead of stopping

                logger.info(f"For ticket {ticket['Ticket Number']} Generated conversation: {conversation}")
                conversations_list.extend(conversation)  # Flatten list

                time_entries = generate_time_entries(ticket)
                time_entries = context.validate_time_entries(ticket, time_entries)
                if time_entries:
                    logger.info(
                        "Generated %s time entries for Ticket #%s",
                        len(time_entries),
                        ticket.get('Ticket Number', 'Unknown'),
                    )
                    time_entries_list.extend(time_entries)
                else:
                    logger.info(
                        "No time entries created for Ticket #%s based on configuration.",
                        ticket.get('Ticket Number', 'Unknown'),
                    )

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
            ticket_dict = {key: [ticket.get(key, "") for ticket in tickets_list] for key in tickets_list[0].keys()}
            logger.info("Converted tickets to dictionary format.")

            # Handle conversations properly
            if isinstance(conversations_list, list) and all(isinstance(item, dict) for item in conversations_list):
                conversations_dict = {key: [conversation.get(key, "") for conversation in conversations_list] for key in conversations_list[0].keys()}
                logger.info("Converted conversations to dictionary format.")
            else:
                logger.error("Unexpected structure in conversations_list.")
                return

            time_entries_dict = None
            if time_entries_list:
                if all(isinstance(item, dict) for item in time_entries_list):
                    time_entries_dict = {
                        key: [entry.get(key, "") for entry in time_entries_list]
                        for key in time_entries_list[0].keys()
                    }
                    logger.info("Converted time entries to dictionary format.")
                else:
                    logger.error("Unexpected structure in time_entries_list.")
                    return

            # Save to CSV
            append_dict_to_csv(ticket_dict, conversations_dict, time_entries_dict)
            print(f"{len(tickets_list)} tickets successfully saved")
            if time_entries_list:
                print(f"{len(time_entries_list)} time entries successfully saved")

            prompt_for_ticket_review()

        except Exception as e:
            logger.error(f"Error processing dictionaries: {e}", exc_info=True)
            return

    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}", exc_info=True)
        print(f"Error during ticket generation: {e}")

    logger.info("Application finished.")

if __name__ == "__main__":
    main()
