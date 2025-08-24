"""
Defines a FastAPI application to orchestrate group chat among AI agents using Semantic Kernel.
"""

import asyncio
from semantic_kernel.agents import GroupChatOrchestration, BooleanResult, StringResult, MessageResult
from semantic_kernel.agents import GroupChatManager
from semantic_kernel.contents import ChatMessageContent, ChatHistory
from semantic_kernel.agents.runtime import InProcessRuntime
from utils.logger import log
from utils.metrics import log_token_usage

from agent_verse.Triage_Agent.agent import TriageAgent
from agent_verse.Retriever_Agent.agent import RetrieverAgent
from agent_verse.Composer_Agent.agent import ComposerAgent

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
        return MessageResult(result=ChatMessageContent(role="assistant", content=summary, choice_index=0), reason="Custom summary logic.")

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
            intake_agent = await TriageAgent().get_agent()
            retriever_agent = await RetrieverAgent().get_agent()
            composer_agent = await ComposerAgent().get_agent()

            STARTING_AGENT = intake_agent
            TERMINATION_KEYWORD = "Done"

            # Create list of allowed agents
            allowed_agents = [intake_agent,retriever_agent,composer_agent]

            GROUP_CHAT_ORCHESTRATION = GroupChatOrchestration(
                members=allowed_agents,
                manager=ProcessGroupChatManager(max_rounds=5),
                agent_response_callback=self.agent_response_callback,
            )

        return GROUP_CHAT_ORCHESTRATION

    async def run(self):
        runtime = InProcessRuntime()
        runtime.start()
        try:
            group_chat_orchestration = await self.get_group_chat_orchestration()
            log.info("Ready! Type your input, or 'exit' to quit, 'reset' to restart the conversation.")

            while True:
                user_input = input("User > ").strip()
                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    break

                if user_input.lower() == "reset":
                    # Close and restart the runtime in this same task
                    await runtime.close()
                    runtime = InProcessRuntime()
                    runtime.start()
                    print("[Conversation has been reset]")
                    continue

                orchestration_result = await group_chat_orchestration.invoke(
                    task=user_input,
                    runtime=runtime,
                )

                # ensure we await the result so any spawned tasks settle
                await orchestration_result.get()

                log.info("Group Chat Over")
                break
        finally:
            # close in same task to avoid cancel-scope cross-task error
            await runtime.close()


if __name__ == "__main__":

    asyncio.run(ProcessAgent().run())
