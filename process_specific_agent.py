"""
Defines a FastAPI application to orchestrate group chat among AI agents using Semantic Kernel.
"""

import os
import asyncio
import threading
from fastapi import FastAPI
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from semantic_kernel.agents import GroupChatOrchestration, BooleanResult, StringResult, MessageResult
from semantic_kernel.agents import GroupChatManager
from semantic_kernel.contents import ChatMessageContent, ChatHistory
from semantic_kernel.agents.runtime import InProcessRuntime
from pydantic import BaseModel
from agent_verse.calculator_agent.agent import CalculatorAgent
from utils.logger import log
from utils.metrics import log_token_usage

app = FastAPI(
    title="Agentic AI Base Code",
    openapi_url=None,
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*"),
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


class GroupChatInputModel(BaseModel):
    """
        Pydantic model for incoming group chat requests.
    """
    user_message: str
    user_email_id: str


GROUP_CHAT_ORCHESTRATION = None
STARTING_AGENT = None
TERMINATION_KEYWORD = None


class ProcessGroupChatManager(GroupChatManager):
    """
    Custom GroupChatManager for orchestrating multi-agent conversations.
    """
    async def filter_results(self, _: ChatHistory) -> MessageResult:
        """
        Produces a summary of the conversation when filtering results.
        """
        summary = "Summary of the discussion."
        return MessageResult(result=ChatMessageContent(role="assistant", content=summary), reason="Custom summary logic.")

    async def select_next_agent(self, chat_history: ChatHistory, participant_descriptions: dict[str, str]) -> StringResult:
        """
        Chooses which agent should speak next based on chat history and participant names.
        """

        if len(chat_history.messages) == 1:
            for agent_name in participant_descriptions:
                if agent_name.lower() == STARTING_AGENT.name.lower():
                    print("=====================================================================")
                    print(f"[🤖] AGENT SELECTED: {agent_name}")
                    print("=====================================================================")
                    return StringResult(result=agent_name, reason="Custom selection logic.")

            raise Exception("Starting Agent is not part of the Group Chat. Please add the Starting Agent to the member agents")

        try:
            last_message_content = chat_history.messages[-1].content.lower()
        except Exception:
            log.debug("Empty response from agent")
            last_message_content = ""

        for agent in participant_descriptions:
            if agent.lower() in last_message_content.lower():
                print("=====================================================================")
                print(f"[🤖] AGENT SELECTED: {agent.upper()}")
                print("=====================================================================")
                return StringResult(result=agent, reason="Custom selection logic.")

        chat_history.messages[-1].content = chat_history.messages[-1].content + " Please mention the AGENT name which needs to execute the instruction."
        last_agent_name = chat_history.messages[-1].name
        log.error("No Agent Name found in message (%s): %s", last_agent_name, last_message_content)
        log.error("Retrying with same agent")

        return StringResult(result=chat_history.messages[-1].name, reason="Custom selection logic.")

    async def should_request_user_input(self, _: ChatHistory) -> BooleanResult:
        """
        Determines whether the orchestration should request user input.
        """
        # Custom logic to decide if user input is needed
        return BooleanResult(result=False, reason="No user input required.")

    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """
        Decides whether the multi-agent conversation should end.
        """

        last_message_content = chat_history.messages[-1].content.lower()

        if TERMINATION_KEYWORD.lower() in last_message_content:
            return BooleanResult(result=True, reason="Custom termination logic.")

        base_result = await super().should_terminate(chat_history)
        if base_result.result:
            return base_result

        return BooleanResult(result=False, reason="Custom termination logic.")


class ProcessAgent:
    """
        Drives the execution of a group chat orchestration.
    """
    total_tokens_consumed = 0
    total_prompt_tokens_consumed = 0
    total_completion_tokens_consumed = 0

    def agent_response_callback(self, response: ChatMessageContent) -> None:
        """
                Callback invoked for each agent response in the orchestration.
        """

        if response.content.strip() != "":
            print("=====================================================================")
            print(f"[AUTO-REPLY] [🤖] Agent Speaker: {response.name.upper()}")
            print("=====================================================================")
            print(f"\nAGENT RESPONSE [💬] : {response.content}\n")
            print("=====================================================================")
            current_prompt_tokens, current_completion_tokens, current_total_token_consumed = log_token_usage(response)
            self.total_prompt_tokens_consumed += current_prompt_tokens
            self.total_completion_tokens_consumed += current_completion_tokens
            self.total_tokens_consumed += current_total_token_consumed
            print("[💬] > [🪙] > [🔥] Total Input Tokens Consumed : " + str(self.total_prompt_tokens_consumed))
            print("[💬] > [🪙] > [🔥] Total Completion Tokens Consumed : " + str(self.total_completion_tokens_consumed))
            print("[💬] > [🪙] > [🔥] Total Tokens Consumed : " + str(self.total_tokens_consumed))
            print("=====================================================================")

    async def get_group_chat_orchestration(self):
        """
            Initializes (if needed) and returns the shared GroupChatOrchestration instance.
        """
        global STARTING_AGENT
        global TERMINATION_KEYWORD
        global GROUP_CHAT_ORCHESTRATION

        if not GROUP_CHAT_ORCHESTRATION:
            calculator_agent = await CalculatorAgent().get_agent()

            STARTING_AGENT = calculator_agent
            TERMINATION_KEYWORD = "Done"

            # Create list of allowed agents
            allowed_agents = [calculator_agent]

            GROUP_CHAT_ORCHESTRATION = GroupChatOrchestration(
                members=allowed_agents,
                manager=ProcessGroupChatManager(max_rounds=5),
                agent_response_callback=self.agent_response_callback,
            )

        return GROUP_CHAT_ORCHESTRATION

    async def run(self):
        """
            Runs an interactive loop for the group chat orchestration.
        """
        runtime = InProcessRuntime()
        runtime.start()

        group_chat_orchestration = await self.get_group_chat_orchestration()

        log.info(
            "Ready! Type your input, or 'exit' to quit, 'reset' to restart the conversation. "
        )

        is_complete = False

        while not is_complete:

            user_input = input("User > ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                is_complete = True
                break

            if user_input.lower() == "reset":
                await runtime.close()
                runtime = InProcessRuntime()
                runtime.start()
                print("[Conversation has been reset]")
                continue

            orchestration_result = await group_chat_orchestration.invoke(
                task=user_input,
                runtime=runtime,
            )

            await orchestration_result.get()

            # value = await orchestration_result.get()
            # print(f"***** Final Result *****\n{value}")

            log.info("Group Chat Over")


# Global lock to ensure one group chat runs at a time.
GROUP_CHAT_LOCK = threading.Lock()


def run_thread(input_data: GroupChatInputModel):
    """
    Thread entry point for processing a group chat request synchronously.
    """
    # The lock is acquired here so that this thread executes exclusively.
    with GROUP_CHAT_LOCK:
        # Run the async processing function in this thread.
        asyncio.run(process_group_chat(input_data))


async def process_group_chat(input_data: GroupChatInputModel):
    """
        Async function to handle a GroupChatInputModel request.
    """
    runtime = InProcessRuntime()

    runtime.start()

    process_agent = ProcessAgent()
    group_chat_orchestration = await process_agent.get_group_chat_orchestration()

    message = input_data.user_email_id + ": " + input_data.user_message

    log.info(message)

    orchestration_result = await group_chat_orchestration.invoke(
        task=message,
        runtime=runtime,
    )

    await orchestration_result.get()

    # value = await orchestration_result.get()
    # print(f"***** Final Result *****\n{value}")

    log.info("Group Chat Over")


@app.post("/")
async def process_run(group_chat_input: GroupChatInputModel):
    """
        HTTP endpoint to start processing a group chat.
    """

    # Check if the lock is already held. If so, inform the caller that a session is in progress.
    if GROUP_CHAT_LOCK.locked():
        response = {
            'status': 'failed',
            'message': 'Previous Request is in process.'
        }
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=response)

    # Start the group chat processing in a new thread.
    t = threading.Thread(target=run_thread, args=(group_chat_input,))
    t.start()

    response = {
        'status': 'success',
        'message': 'Processing started'
    }

    # Immediately return a response to the user.
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


if __name__ == "__main__":

    asyncio.run(ProcessAgent().run())
