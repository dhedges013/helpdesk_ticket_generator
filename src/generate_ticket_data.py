import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from . import config
from .generation_context import GenerationContext
from .probability import get_registry, ProbabilityProfile
from .utils import (
    get_random_contact,
    get_random_customer,
    get_random_description,
    get_random_issue_type,
    get_random_priority,
    get_random_status,
    get_random_subject,
    get_random_tech,
)
from .models import Ticket

logger = config.get_logger(__name__)
PROFILE_REGISTRY = get_registry()

# Generate a random datetime within the past week
def generate_random_datetime():
    try:
        now = datetime.now()
        past_time = now - timedelta(days=config.DAYS_AGO)
        random_datetime = past_time + (now - past_time) * random.random()
        logging.debug(f"Generated random datetime: {random_datetime}")
        return random_datetime
    except Exception as e:
        logging.error(f"Error generating random datetime: {e}")
        return None



def generate_random_ticket_number() -> Optional[int]:
    try:
        logging.debug("Generating random ticket number.")
        return random.randint(1000, 9999)
    except Exception as e:
        logging.error(f"Error generating random ticket number: {e}")
        return None
    
def generate_ticket(context: Optional[GenerationContext] = None) -> Optional[Ticket]:
    # Ticket class or function to generate a ticket
    logging.debug("Starting ticket generation.")
    try:
        profile_registry = context.probability_registry if context else PROFILE_REGISTRY

        ticket_number = generate_random_ticket_number()
        # Ensure all fields are generated correctly
        contact = get_random_contact()
        if not contact:
            logging.warning("No contact generated. Setting default.")
            contact = "Unknown Contact"

        customer = get_random_customer()
        if not customer:
            logging.warning("No customer generated. Setting default.")
            customer = "Unknown Customer"

        tech = get_random_tech()
        if not tech:
            logging.warning("No tech generated. Setting default.")
            tech = "Unassigned"

        description = get_random_description()
        if not description:
            logging.warning("No description generated. Setting default.")
            description = "No description provided."

        tech_profile = (
            context.resolve_tech_profile(tech) if context else profile_registry.resolve_tech_profile(tech)
        )
        customer_profile = (
            context.resolve_customer_profile(customer)
            if context
            else profile_registry.resolve_customer_profile(customer)
        )

        issue_type = get_random_issue_type(tech_profile)
        if not issue_type:
            logging.warning("No issue type generated. Setting default.")
            issue_type = "General Inquiry"

        priority = get_random_priority(customer_profile)
        if not priority:
            logging.warning("No priority generated. Setting default.")
            priority = "Low"

        status = get_random_status(customer_profile)
        if not status:
            logging.warning("No status generated. Setting default.")
            status = "Open"

        subject = get_random_subject(tech_profile)
        if not subject:
            logging.warning("No subject generated. Setting default.")
            subject = "General Issue"

        start_time = generate_random_datetime()
        end_time = generate_random_datetime()

        # Ensure the end time is after the start time
        if end_time < start_time:
            logging.warning(f"End time {end_time} is before start time {start_time}. Adjusting end time.")
            end_time = start_time + timedelta(hours=1)

        ticket: Ticket = {
            "Customer": customer,
            "Ticket Number": ticket_number,
            "Contact": contact,
            "Subject": subject,
            "Status": status,         
            "Description": description,
            "Issue Type": issue_type,
            "Assigned Tech": tech,
            "Priority": priority,                        
            "Start Time": start_time,
            "End Time": end_time
        }

        logging.info(f"Ticket generated successfully: {ticket}")
        return ticket
    except Exception as e:
        logging.error(f"Error generating ticket: {e}")
        return None

