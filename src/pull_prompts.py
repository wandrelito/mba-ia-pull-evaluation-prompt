
"""
Realiza o pull do prompt inicial do LangSmith Prompt Hub
e salva sua estrutura em um arquivo YAML local.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"


def pull_prompts_from_langsmith():
    """Recupera o prompt original e salva em formato YAML."""

    print_section_header("Pull de Prompt - LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    try:
        client = Client()

        print(f"Recuperando prompt: {PROMPT_NAME}")

        prompt = client.pull_prompt(
            PROMPT_NAME,
            dangerously_pull_public_prompt=True,
        )

        if not hasattr(prompt, "messages"):
            raise ValueError(
                "O prompt recebido não é um ChatPromptTemplate."
            )

        system_parts = []
        user_parts = []

        for message in prompt.messages:
            template = getattr(
                getattr(message, "prompt", None),
                "template",
                None,
            )

            if not isinstance(template, str):
                raise ValueError(
                    "Mensagem com formato não suportado."
                )

            if isinstance(message, SystemMessagePromptTemplate):
                system_parts.append(template)

            elif isinstance(message, HumanMessagePromptTemplate):
                user_parts.append(template)

            else:
                raise ValueError(
                    f"Tipo de mensagem não suportado: "
                    f"{type(message).__name__}"
                )

        prompt_data = {
            "name": "bug_to_user_story_v1",
            "version": "v1",
            "description": "Prompt original do desafio Full Cycle",
            "source": PROMPT_NAME,
            "system_prompt": "\n\n".join(system_parts),
            "user_prompt": "\n\n".join(user_parts),
            "techniques_applied": [],
        }

        if not save_yaml(prompt_data, str(OUTPUT_FILE)):
            return False

        print(f"Prompt salvo em: {OUTPUT_FILE}")
        return True

    except Exception as error:
        print(f"Erro ao recuperar o prompt: {error}")
        return False


def main():
    """Ponto de entrada da aplicação."""
    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
