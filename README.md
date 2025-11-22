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

## Discord Bot

You can run a discord bot to generate tickets in discord
You will need to seet a token. Example: $env:DISCORD_BOT_TOKEN = 'MTQzODMyNDAy'




## Done List

    - Nov 25 - added Syncro CSV Template Output
        - added discord_bot.py connector
        - added cli pref files saves
        - probability profiles

    - 3.29.25 created API Branch

    - 3.18.25 added api_interface.py
    - added in config variables for conversations csv data

    - 3.16.25 Updated conversation output to include the Customer Name
    - 3.16.25 Updated the results output for tickets and conversations to have the Customer name as the first column
    - 3.16.25 Updated README file and some other formating
    - 3.16.25 removed to-do-list.txt file

    - Before 3.16 - added in converstations generator


## To-Do List 3.16.25
    - add in labor time generator
    - converestation csv result does not include the customer name   

## Discord Bot Integration
Trigger ticket generation directly from a Discord channel using the included bot:

1. Install the project requirements (the bot depends on `discord.py`):
   ```
   pip install -r requirements.txt
   ```
2. Create a Discord application/bot on the Developer Portal, invite it to your server, and enable the **Message Content Intent**.
3. Set the following environment variables before launching the bot:
   - `DISCORD_BOT_TOKEN` (required): the bot token from the Developer Portal.
   - `DISCORD_ALLOWED_CHANNELS` (optional): comma-separated channel IDs the bot is allowed to respond in. Leave unset to allow every channel.
   - `DISCORD_COMMAND_PREFIX` (optional): defaults to `!`.
   - `DISCORD_MAX_TICKETS` (optional): maximum number of tickets the `ticket` command will generate per request (default `3`).
4. Run the bot:
   ```
   python discord_bot.py
   ```

In Discord, type `!ticket` (or your custom prefix) to generate a ticket. Provide a number to request multiple tickets (e.g., `!ticket 2`), up to the configured maximum. Each response contains the ticket summary, recent conversation messages, and the generated time entries.  
