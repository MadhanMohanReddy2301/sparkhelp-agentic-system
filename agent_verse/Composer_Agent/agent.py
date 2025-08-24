"""
Defines the CalculatorAgent to perform and validate mathematical calculations.
"""
from datetime import datetime
from semantic_kernel.functions import KernelArguments
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from ai_model.agent_llm_factory import AgentLLMFactory
from utils.logger import log
from .prompt.prompt_factory import PromptFactory
from agent_plugins_verse.agent_email_plugin.plugin import EmailPlugin
from semantic_kernel.connectors.mcp import MCPSsePlugin

# Agent name cannot contain spaces,  String should match pattern '^[0-9A-Za-z_-]+$'
AGENT_NAME = "Composer_Agent"


class ComposerAgent:
    """
        Agent for performing mathematical calculations using remote MCP plugins.
    """
    def extract_consumed_token_count(self, result):
        """
        Extracts the total number of tokens consumed from an LLM response object.
        """

        if result and hasattr(result, "metadata"):
            usage_info = result.metadata['usage']
            if hasattr(usage_info, "total_tokens"):
                total_tokens = usage_info.total_tokens
                return total_tokens
            if hasattr(usage_info, "prompt_tokens") and hasattr(usage_info, "completion_tokens"):
                total_tokens = usage_info.prompt_tokens + usage_info.completion_tokens
                return total_tokens

            log.debug("The 'usage' object does not have a 'total_tokens' or 'prompt_tokens' or 'completion_tokens' attribute.")
        else:
            log.debug("The result list is empty or missing the 'usage' attribute.")

        return 0

    async def get_agent(self):
        """
            Initializes and returns a ChatCompletionAgent configured for calculation.
        """
        # Initialize the Kernel
        agent_kernel = Kernel()

        log.debug(f"Initializing [🤖] : {AGENT_NAME}")
        # create a service - basically llm ( refer to llm config for getting completion llm )
        chat_completion_service = AgentLLMFactory.get_chat_completion()
        if chat_completion_service is None:
            raise RuntimeError("Failed to create chat completion service. Check configuration and credentials.")

        agent_kernel.add_service(chat_completion_service)
        agent_kernel.add_plugin(EmailPlugin(), plugin_name="send_email")
        # Get the AI Service settings
        settings = agent_kernel.get_prompt_execution_settings_from_service_id(chat_completion_service.service_id)

        # Configure the function choice behavior to auto invoke kernel functions
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        agent_prompt = PromptFactory().get_agent_prompt()

        # Create the agent
        agent = ChatCompletionAgent(
            kernel=agent_kernel,
            name=AGENT_NAME,
            description="Agent is responsible for writing the final email.",
            instructions=agent_prompt,
            arguments=KernelArguments(settings=settings),
        )

        return agent

    async def run(self):
        """
            Runs the calculation agent in an interactive loop.
        """
        simple_agent = await self.get_agent()

        # Create Chat History

        thread: ChatHistoryAgentThread = None

        total_tokens_consumed = 0

        # while development keep in mind this is a while true loop.
        # ensure you implement the right logic for exit and only for testing
        while True:
            user_input = input("Enter something (type 'q' or 'quit' to exit): ")
            if user_input.lower() in ['q', 'quit']:
                print("Exiting...")
                break

            arguments = KernelArguments(
                now=datetime.now().strftime("%Y-%m-%d %H:%M")
            )

            result = None

            async for response in simple_agent.invoke(messages=user_input, thread=thread, arguments=arguments):
                result = response
                thread = response.thread

            assistant_response = result.content
            current_token_consumed = self.extract_consumed_token_count(result)
            total_tokens_consumed = total_tokens_consumed + current_token_consumed
            # Print the results
            log.debug("Assistant > " + str(assistant_response))
            log.debug("Current Token Consumed : " + str(current_token_consumed))
            log.debug("Total Token Consumed : " + str(total_tokens_consumed))


if __name__ == "__main__":
    import asyncio

    asyncio.run(ComposerAgent().run())
