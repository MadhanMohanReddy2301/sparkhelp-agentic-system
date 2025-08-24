
import os
from typing import Union
import logging as log
from dotenv import load_dotenv

# Load the environment variables from the specified file
load_dotenv()

keys = [
    'ENVIRONMENT',
    'AGENT_LLM_MODEL',
    'AZURE_GPT_4O_API_KEY',
    'LLM_CONFIG_FILE',
    'LOGGING_LEVEL',
    'LOGGING_FOLDER_PATH',
    'LOGGING_FILE_NAME',
    'PLUGINS_CONFIG_FILE',
    'GEMINI_API_KEY',
    'OPENAI_API_KEY'
]

KEYS_DICTIONARY = {}


def get_key(key: str) -> Union[str | None]:
    """
        Retrieves the value of a specified key from local environment variables or Azure Key Vault.
    """
    if key not in keys:
        raise ValueError(
            f'Key {key} is not registered in the list of credential manager keys. Register key to fetch its value')

    if os.getenv('ENVIRONMENT') == 'local':
        # Get key from local environment variable

        if key in KEYS_DICTIONARY:
            return KEYS_DICTIONARY[key]

        key_value = os.getenv(key)
        if key_value is None:
            raise ValueError(f'{key} environment variable is not set.')
        KEYS_DICTIONARY[key] = key_value
        return key_value

    raise Exception(f"Environment '{os.getenv('ENVIRONMENT')}' is currently not supported by credentials manager")


def validate_all_keys() -> None:
    """
        Check if all keys are created
    """

    for key in keys:
        # Validating if all variables exist
        log.debug('Validating Key: %s', key)
        _ = get_key(key)

    log.info('All keys exist in Env Variables/ Key Vault')


validate_all_keys()
