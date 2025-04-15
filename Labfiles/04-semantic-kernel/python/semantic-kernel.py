import os
import asyncio

# Add references
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function
from typing import Annotated




async def main():
    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    # Create expense claim data
    data = """date,description,amount
              07-Mar-2025,taxi,24.00
              07-Mar-2025,dinner,65.50
              07-Mar-2025,hotel,125.90"""

    # Run the async agent code
    await create_expense_claim(data)

async def create_expense_claim(expenses_data):

    # Get configuration settings
    load_dotenv()
    ai_agent_settings = AzureAIAgentSettings.create()



    # Connect to the Azure AI Foundry project
    async with (
        DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True) as creds,
        AzureAIAgent.create_client(
            credential=creds
        ) as project_client,
    ):


        
        # Define an Azure AI agent that sends an expense claim email
        expenses_agent_def = await project_client.agents.create_agent(
            model= ai_agent_settings.model_deployment_name,
            name="expenses_agent",
            instructions="""You are an AI assistant for expense claim submission.
                            When a user submits expenses data and requests an expense claim, use the plug-in function to send an email to expenses@contoso.com with the subject 'Expense Claim`and a body that contains itemized expenses with a total.
                            Then confirm to the user that you've done so."""
        )



        # Create a semantic kernel agent
        expenses_agent = AzureAIAgent(
            client=project_client,
            definition=expenses_agent_def,
            plugins=[EmailPlugin()]
        )



        # Use the agent to generate an expense claim email
        thread: AzureAIAgentThread = AzureAIAgentThread(client=project_client)
        try:
            # Add the input prompt to a list of messages to be submitted
            prompt_messages = [f"Create an expense claim for the following expenses: {expenses_data}"]
            # Invoke the agent for the specified thread with the messages
            response = await expenses_agent.get_response(thread_id=thread.id, messages=prompt_messages)
            # Display the response
            print(f"\n# {response.name}:\n{response}")
        except Exception as e:
            # Something went wrong
            print (e)
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await project_client.agents.delete_agent(expenses_agent.id)




# Create a Plugin for the email functionality
class EmailPlugin:
    """A Plugin to simulate email functionality."""
    
    @kernel_function(description="Sends an email.")
    def send_email(self,
                   to: Annotated[str, "Who to send the email to"],
                   subject: Annotated[str, "The subject of the email."],
                   body: Annotated[str, "The text body of the email."]):
        print("\nTo:", to)
        print("Subject:", subject)
        print(body, "\n")




if __name__ == "__main__":
    asyncio.run(main())
