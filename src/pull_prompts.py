"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt de baixa qualidade publicado no LangSmith Hub que deve ser otimizado.
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"

# Onde o prompt será salvo localmente.
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"


def _extract_messages(prompt_object) -> dict:
    """
    Extrai system_prompt e user_prompt de um objeto de prompt do LangChain.

    Suporta ChatPromptTemplate (lista de mensagens) e PromptTemplate simples.

    Args:
        prompt_object: Objeto retornado por hub.pull()

    Returns:
        Dicionário com 'system_prompt' e 'user_prompt' (strings).
    """
    system_parts = []
    user_parts = []

    # ChatPromptTemplate: possui atributo .messages
    messages = getattr(prompt_object, "messages", None)
    if messages:
        for message in messages:
            # Cada item é um *MessagePromptTemplate; o texto fica em .prompt.template
            inner = getattr(message, "prompt", None)
            template = getattr(inner, "template", None)
            if template is None:
                # Fallback: mensagem literal já formatada
                template = getattr(message, "content", "")

            role = message.__class__.__name__.lower()
            if "system" in role:
                system_parts.append(template)
            else:
                # Human / User / AI e quaisquer outros vão para o user_prompt
                user_parts.append(template)
    else:
        # PromptTemplate simples (sem papéis) -> trata tudo como system_prompt
        template = getattr(prompt_object, "template", None)
        if template is not None:
            system_parts.append(template)

    return {
        "system_prompt": "\n\n".join(p for p in system_parts if p).strip(),
        "user_prompt": "\n\n".join(p for p in user_parts if p).strip(),
    }


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt de baixa qualidade do LangSmith Hub e salva localmente.

    Returns:
        True se sucesso, False caso contrário.
    """
    print(f"📥 Fazendo pull do prompt: {SOURCE_PROMPT}")

    try:
        prompt_object = hub.pull(SOURCE_PROMPT)
    except Exception as e:  # noqa: BLE001 - queremos reportar qualquer falha de rede/API
        print(f"❌ Erro ao fazer pull do prompt '{SOURCE_PROMPT}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- Sua conexão com a internet está funcionando")
        print(f"- O prompt '{SOURCE_PROMPT}' é público e existe no Hub")
        return False

    print("   ✓ Prompt carregado do Hub")

    extracted = _extract_messages(prompt_object)

    if not extracted["system_prompt"] and not extracted["user_prompt"]:
        print("❌ Não foi possível extrair o conteúdo do prompt.")
        return False

    # Se não houver mensagem de usuário, garante que a variável do dataset exista.
    if not extracted["user_prompt"]:
        extracted["user_prompt"] = "{bug_report}"

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt (baixa qualidade) para converter relatos de bugs em User Stories",
            "system_prompt": extracted["system_prompt"],
            "user_prompt": extracted["user_prompt"],
            "version": "v1",
            "source": SOURCE_PROMPT,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if save_yaml(prompt_data, OUTPUT_FILE):
        print(f"   ✓ Prompt salvo em: {OUTPUT_FILE}")
        print("\n📄 Conteúdo extraído (system_prompt):")
        print("-" * 50)
        preview = extracted["system_prompt"] or extracted["user_prompt"]
        print(preview[:500] + ("..." if len(preview) > 500 else ""))
        print("-" * 50)
        return True

    print("❌ Falha ao salvar o prompt localmente.")
    return False


def main():
    """Função principal."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        print("\nPróximos passos:")
        print(f"1. Analise o prompt em {OUTPUT_FILE}")
        print("2. Crie a versão otimizada em prompts/bug_to_user_story_v2.yml")
        print("3. Faça push: python src/push_prompts.py")
        return 0

    print("\n❌ Pull falhou. Corrija os erros acima e tente novamente.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
