# # orchestrator.py
# import asyncio
# from queue import Queue
#
# from semantic_kernel.agents import HandoffOrchestration, OrchestrationHandoffs
# from semantic_kernel.agents.runtime import InProcessRuntime
# from semantic_kernel.contents import ChatMessageContent
#
# from agent_verse.Triage_Agent.agent import TriageAgent
# from agent_verse.Retriever_Agent.agent import RetrieverAgent
# from agent_verse.Composer_Agent.agent import ComposerAgent
#
# async def get_agents():
#     """
#     Await and return instantiated Agent objects.
#     Using asyncio.gather to initialize them in parallel if supported.
#     """
#     intake_agent = await TriageAgent().get_agent()
#     retriever_agent = await RetrieverAgent().get_agent()
#     composer_agent = await ComposerAgent().get_agent()
#
#     return intake_agent, retriever_agent, composer_agent
#
# def build_handoffs(intake_agent, retriever_agent, composer_agent):
#     return (
#         OrchestrationHandoffs()
#         .add(source_agent=intake_agent.name, target_agent=retriever_agent.name,
#              description="Ticket triaged, handing off to Retriever")
#         .add(source_agent=retriever_agent.name, target_agent=composer_agent.name,
#              description="Context retrieved, handing off to Composer")
#         .add(source_agent=composer_agent.name, target_agent=intake_agent.name,
#              description="Need human clarification or re-triage")
#     )
#
# def agent_response_callback(message: ChatMessageContent):
#     # logging / audit hook
#     print(f"[{message.name}] {message.content}")
#
# def human_response_function_factory(human_queue: Queue):
#     def _fn():
#         return human_queue.get() if not human_queue.empty() else None
#     return _fn
#
# async def main():
#     # 1) get agent instances (await the coroutines)
#     intake_agent, retriever_agent, composer_agent = await get_agents()
#
#     # 2) create handoffs & members
#     handoffs = build_handoffs(intake_agent, retriever_agent, composer_agent)
#     members = [intake_agent, retriever_agent, composer_agent]
#
#     # 3) prepare human queue and orchestration callbacks
#     human_queue = Queue()
#     human_fn = human_response_function_factory(human_queue)
#
#     orchestration = HandoffOrchestration(
#         members=members,
#         handoffs=handoffs,
#         agent_response_callback=agent_response_callback,
#         human_response_function=human_fn
#     )
#
#     # 4) start runtime
#     runtime = InProcessRuntime()
#     runtime.start()
#
#     # 5) seed the human queue with the initial ticket payload
#     initial_ticket = {
#         "ticket_uid": "TICKET-123",
#         "subject": "Issue with Data Encryption",
#         "body": "I experience a failure after the latest patch..."
#     }
#     human_queue.put(initial_ticket)
#
#     task_description = "Process this support ticket through triage, retrieval, and composition."
#
#     try:
#         # orchestration.invoke is async; await its result
#         result_future = await orchestration.invoke(task=task_description, runtime=runtime)
#         final_value = await result_future.get()
#         print("Orchestration finished. Final output:", final_value)
#     finally:
#         # graceful shutdown
#         await runtime.stop_when_idle()
#
# if __name__ == "__main__":
#     asyncio.run(main())
