"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Arquivo com o prompt otimizado e o nome do repositório no Hub.
V2_FILE = "prompts/bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"
REPO_NAME = "bug_to_user_story_v2"  # publicado como {username}/bug_to_user_story_v2


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")

    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    user_prompt = (prompt_data.get("user_prompt") or "").strip()
    if "{bug_report}" not in (system_prompt + user_prompt):
        errors.append(
            "A variável {bug_report} não foi encontrada no prompt "
            "(necessária para a avaliação contra o dataset)"
        )

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas em 'techniques_applied', "
            f"encontradas: {len(techniques)}"
        )

    return (len(errors) == 0, errors)


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """
    Monta um ChatPromptTemplate a partir do system_prompt e user_prompt.

    O system_prompt tem suas chaves literais escapadas ({ -> {{) para que
    exemplos few-shot não sejam interpretados como variáveis de template.
    A única variável real ({bug_report}) fica na mensagem humana (user_prompt).

    Args:
        prompt_data: Dados do prompt lidos do YAML.

    Returns:
        Instância de ChatPromptTemplate com input_variable 'bug_report'.
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    # Escapa quaisquer chaves literais no system_prompt (few-shot, JSON, etc.).
    safe_system = system_prompt.replace("{", "{{").replace("}", "}}")

    return ChatPromptTemplate.from_messages(
        [
            ("system", safe_system),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do repositório do prompt (ex: bug_to_user_story_v2)
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        chat_prompt = build_chat_prompt(prompt_data)
    except Exception as e:  # noqa: BLE001
        print(f"❌ Erro ao montar o ChatPromptTemplate: {e}")
        return False

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get(
        "description", "Prompt otimizado para converter bugs em User Stories"
    )
    # Tags incluem as técnicas de prompt engineering aplicadas (metadados).
    tags = list(prompt_data.get("tags", []))
    tags += [t.lower().replace(" ", "-") for t in techniques]
    tags = sorted(set(tags))

    readme = (
        f"# {prompt_name}\n\n"
        f"{description}\n\n"
        f"**Técnicas de Prompt Engineering aplicadas:**\n"
        + "\n".join(f"- {t}" for t in techniques)
        + f"\n\n**Variável de entrada:** `{{bug_report}}`\n"
    )

    print(f"📤 Fazendo push (público) do prompt: {prompt_name}")
    print(f"   Técnicas: {', '.join(techniques)}")

    try:
        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=chat_prompt,
            is_public=True,
            description=description,
            readme=readme,
            tags=tags,
        )
        print("   ✓ Push concluído com sucesso!")
        print(f"   🔗 URL: {url}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Erro ao fazer push do prompt '{prompt_name}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- Você tem permissão de escrita no seu workspace do LangSmith")
        return False


def main():
    """Função principal."""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    data = load_yaml(V2_FILE)
    if not data:
        print(f"❌ Não foi possível carregar {V2_FILE}")
        return 1

    prompt_data = data.get(V2_KEY, data)

    print("🔍 Validando prompt...")
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for err in errors:
            print(f"   - {err}")
        return 1
    print("   ✓ Prompt válido")

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    if push_prompt_to_langsmith(REPO_NAME, prompt_data):
        published_as = f"{username}/{REPO_NAME}" if username else REPO_NAME
        print(f"\n✅ Push concluído! Prompt publicado como: {published_as}")
        print("\nPróximos passos:")
        print("1. Confirme a publicação em: https://smith.langchain.com/prompts")
        print("2. Deixe o prompt PÚBLICO no dashboard (se ainda não estiver)")
        print("3. Execute a avaliação: python src/evaluate.py")
        return 0

    print("\n❌ Push falhou. Corrija os erros acima e tente novamente.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
