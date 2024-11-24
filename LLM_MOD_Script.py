import openai
import os
from dotenv import load_dotenv
from openai import Client
from openai import OpenAI
import time

# Load environment variables
load_dotenv()
### ENVIRONMENT SETUP ###
openai.api_key = os.getenv("OPENAI_API_KEY")

##CHATGPT ASSISTANT
client = OpenAI()
assistant_id=None
assistant_thread_id=None

# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Json Format")
 
# Ready the files for upload to OpenAI
file_paths = [r"C:\Users\muham\Downloads\schema - category and details - shortened.json"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

purpose = "Your job is to extract the data from PDF and fill the provided JSON format with only the information in the PDF provided. \nNo invention and elaboration of data is acceptable.\n\n1. First, classify each datasheet into high-level categories (buildingSystem and productCategory) as per the schema to make sure it's relevant to the schema.\n2. Ensure accuracy by adhering strictly to the schema and PDF content only.\n"

assistant = client.beta.assistants.create(
        name=f"mod test 1",
        instructions=purpose,
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}})
assistant_id=assistant.id

new_thread = client.beta.threads.create()
assistant_thread_id = new_thread.id

# Upload the user provided file to OpenAI
message_file = client.files.create(
  file=open(r"C:\Users\muham\Downloads\bele_doppelwand_2015.pdf", "rb"), purpose="assistants"
)
JsonFormat = client.files.create(
  file=open(r"C:\Users\muham\Downloads\schema - category and details - shortened.json", "rb"), purpose="assistants"
)

instructions = "process the data in the attached PDF and add it to the attached JSON Format, please stick to the same data types and schema of the json format and to the data that's in the PDF,your output should be JSON only with no additional text, and please translate all the values to english if it's not English,for the ID please use an online UUID generator to fill it"

# Add the comment ID as the first message (system role)
client.beta.threads.messages.create(
     thread_id=assistant_thread_id,
     role="user",  # System message role
     content=instructions,
     attachments=[
                        {
                            "file_id": message_file.id,
                            "tools": [{"type": "file_search"}]
                        },
                        {
                            "file_id": JsonFormat.id,
                            "tools": [{"type": "file_search"}]   
                        }
                    ]
 )

run= client.beta.threads.runs.create(thread_id=assistant_thread_id,
                                   assistant_id=assistant_id ) 
run=client.beta.threads.runs.retrieve(
        thread_id=assistant_thread_id,
            run_id=run.id)
# Poll the run status until it's done
while run.status not in ["completed", "failed", "canceled"]:
    time.sleep(5)  # Wait for 5 seconds before checking again
    run =  client.beta.threads.runs.retrieve(
        thread_id=assistant_thread_id,
        run_id=run.id
    )

messages=client.beta.threads.messages.list(thread_id=assistant_thread_id)

for message in reversed(messages.data):
    print(message.role + ": " + message.content[0].text.value)

answer = messages.data[0].content[0].text.value