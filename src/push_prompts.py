
"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print("\nErro: o prompt não passou na validação.")
        for error in errors:
            print(f"  - {error}")
        return False

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    if not username:
        print("Erro: USERNAME_LANGSMITH_HUB não configurado.")
        return False

    prompt_identifier = f"{username}/{prompt_name}"

    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data["user_prompt"]

    techniques = prompt_data["techniques_applied"]
    tags = prompt_data.get("tags", [])

    description = prompt_data.get(
        "description",
        "Prompt otimizado para geração de User Stories."
    )

    # Metadados das técnicas aplicadas.
    metadata_tags = list(dict.fromkeys(
        list(tags) + list(techniques)
    ))

    description = (
        f"{description}\n"
        f"Técnicas aplicadas: {', '.join(techniques)}"
    )

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt),
        ])

        if set(prompt.input_variables) != {"bug_report"}:
            raise ValueError(
                "O template deve utilizar somente {bug_report}. "
                f"Variáveis encontradas: {prompt.input_variables}"
            )

        client = Client()

        print(f"\nPublicando prompt: {prompt_identifier}")

        url = client.push_prompt(
            prompt_identifier,
            object=prompt,
            is_public=True,
            description=description,
            tags=metadata_tags,
        )

        print("\nPrompt publicado com sucesso!")
        print(f"Identificador: {prompt_identifier}")
        print(f"URL: {url}")

        return True

    except Exception as error:
        print(f"\nErro ao publicar prompt: {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["O conteúdo do prompt deve ser um dicionário."]

    required_fields = [
        "system_prompt",
        "user_prompt",
        "techniques_applied",
    ]

    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório ausente: {field}")

    system_prompt = prompt_data.get("system_prompt")
    user_prompt = prompt_data.get("user_prompt")
    techniques = prompt_data.get("techniques_applied")

    if not isinstance(system_prompt, str) or not system_prompt.strip():
        errors.append("system_prompt deve conter instruções.")

    if not isinstance(user_prompt, str) or not user_prompt.strip():
        errors.append("user_prompt deve conter instruções.")

    if isinstance(user_prompt, str):
        if "{bug_report}" not in user_prompt:
            errors.append(
                "user_prompt deve conter a variável {bug_report}."
            )

    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append(
            "É obrigatório declarar pelo menos duas técnicas."
        )
    elif not all(
        isinstance(technique, str) and technique.strip()
        for technique in techniques
    ):
        errors.append("As técnicas devem ser strings não vazias.")
    elif not any(
        technique.lower().replace("_", "-")
        in ("few-shot", "few-shot-learning")
        for technique in techniques
    ):
        errors.append("Few-shot Learning é obrigatório.")

    tags = prompt_data.get("tags", [])
    if not isinstance(tags, list) or not all(
        isinstance(tag, str) for tag in tags
    ):
        errors.append("tags deve ser uma lista de strings.")

    for field in ("system_prompt", "user_prompt"):
        value = prompt_data.get(field, "")
        if isinstance(value, str) and "[TODO]" in value.upper():
            errors.append(f"Marcador [TODO] encontrado em {field}.")

    return len(errors) == 0, errors


def main():
    """Função principal"""

    print_section_header("Push de Prompts - LangSmith")

    if not check_env_vars([
        "LANGSMITH_API_KEY",
        "USERNAME_LANGSMITH_HUB",
    ]):
        return 1

    prompt_file = (
        PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
    )

    if not prompt_file.is_file():
        print(f"Erro: arquivo não encontrado: {prompt_file}")
        return 1

    try:
        data = load_yaml(str(prompt_file))

        if not isinstance(data, dict):
            print("Erro: YAML inválido ou vazio.")
            return 1

        prompt_name = "bug_to_user_story_v2"

        # Aceita o formato com chave principal e o formato plano.
        if prompt_name in data:
            prompt_data = data[prompt_name]
        else:
            prompt_data = data

        success = push_prompt_to_langsmith(
            prompt_name,
            prompt_data,
        )

        return 0 if success else 1

    except Exception as error:
        print(f"Erro durante a execução: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
