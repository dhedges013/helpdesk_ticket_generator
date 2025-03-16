## helpdesk_ticket_generator
Simulates nonsense IT Helpdesk Tickets and conversations 

Control the date range and possible number of back and forth communication in the config.py file variables:

- Default Values:

    - DAYS_AGO = 365
    - MAX_CONVERSATION_ROUNDS = 7

The content for the Tickets and Conversations are pulled from CSV data located here /data/generatorData/
Each CSV holds the data set that is randomlly pulled from when generating the helpdesk ticket
Change or add to the data as desired:

- customer_followups.csv
- helpdesk_responses.csv
- helpdesk_words.csv
- initial_complaints.csv
- ticketContacts.csv
- ticketCustomer.csv
- ticketDescription.csv
- ticketIssueTypes.csv
- ticketPriorities.csv
- ticketStatus.csv
- ticketSubject.csv
- ticketTech.csv

Blank Templates files are in the generateorData_templates folder

Application logs generate a new file each run in logs folder.

Created Tickets and Conversations will be output to the results folder in their own csv files

## Done List
    - 3.16.25 Updated conversation output to include the Customer Name
    - 3.16.25 Updated the results output for tickets and conversations to have the Customer name as the first column
    - 3.16.25 Updated README file and some other same formating
    - 3.16.25 removed to-do-list.txt file

    - Before 3.16 - added in converstations generator


## To-Do List 3.16.25
    - add in labor time generator
    - converestation csv result does not include the customer name   
