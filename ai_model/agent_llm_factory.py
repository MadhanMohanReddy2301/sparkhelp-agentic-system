"""
Defines AgentLLMFactory for loading LLM configurations and instantiating
the appropriate ChatCompletion service (Azure, Ollama, or OpenAI)
based on a JSON configuration file.
"""

import json
import os

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.services.kernel_services_extension import DEFAULT_SERVICE_NAME
from config import credential_manager
from dotenv import load_dotenv
load_dotenv()

class AgentLLMFactory:
    """
    Provides configurations for different LLMs based on a JSON configuration file.
    """

    @staticmethod
    def load_config():
        """
        Loads the JSON configuration file.

        Returns:
            list: A list of LLM configurations.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            json.JSONDecodeError: If the configuration file is not a valid JSON.
        """
        llm_config_file = credential_manager.get_key("LLM_CONFIG_FILE")
        try:
            with open(llm_config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as exception:
            raise FileNotFoundError(f"Configuration file '{llm_config_file}' not found.") from exception
        except json.JSONDecodeError as exception:
            raise ValueError(f"Invalid JSON in configuration file: {exception}") from exception

    @staticmethod
    def get_llm_config(agent_llm_model):
        """
            Retrieves the configuration for a specified LLM model.
        """

        config_list = AgentLLMFactory.load_config()

        # Search for the LLM configuration in the JSON
        for agent_llm_config in config_list:
            if agent_llm_model in agent_llm_config:
                agent_llm_model_configuration = agent_llm_config[agent_llm_model]
                # log.debug(f"Configuration for agent '{agent_llm_model}' found in the configuration file.")
                # log.debug(agent_llm_model_configuration)
                agent_llm_model_configuration['api_key'] = credential_manager.get_key \
                    (agent_llm_model_configuration['api_key'])

                return agent_llm_model_configuration

        raise Exception(f"Invalid llm model provided: {agent_llm_model}")

    @staticmethod
    def get_chat_completion(agent_llm_model=credential_manager.get_key('AGENT_LLM_MODEL')):
        """
            Creates and returns a ChatCompletion service instance based on the LLM configuration.
        """
        chat_completion = None
        llm_config = AgentLLMFactory.get_llm_config(agent_llm_model)
        if str(llm_config["api_type"]).lower() == "azure":
            chat_completion = AzureChatCompletion(
                deployment_name=llm_config["model"],
                api_key=llm_config["api_key"],
                endpoint=llm_config["endpoint"],
                service_id=DEFAULT_SERVICE_NAME,  # Optional; for targeting specific services within Semantic Kernel
            )
        elif str(llm_config["api_type"]).lower() == "ollama":
            chat_completion = OllamaChatCompletion(
                ai_model_id=llm_config["model"],
                host=llm_config["base_url"],
                service_id=DEFAULT_SERVICE_NAME,  # Optional; for targeting specific services within Semantic Kernel
            )
        elif str(llm_config["api_type"]).lower() == "openai":
            chat_completion = OpenAIChatCompletion(
                ai_model_id=llm_config["model"],
                api_key=llm_config["api_key"],
                service_id=DEFAULT_SERVICE_NAME,  # Optional; for targeting specific services within Semantic Kernel
            )
        elif str(llm_config["api_type"]).lower() == "gemini":
            chat_completion = GoogleAIChatCompletion(
                gemini_model_id="gemma-3-27b-it",
                api_key=os.getenv("GEMINI_API_KEY"),
                service_id=DEFAULT_SERVICE_NAME,  # Optional; for targeting specific services within Semantic Kernel
            )
            print("llm_config:", llm_config)
            print("chat_completion:", chat_completion)

        return chat_completion
