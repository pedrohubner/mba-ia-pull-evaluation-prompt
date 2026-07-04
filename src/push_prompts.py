import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

V2_FILE = "prompts/bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"
REPO_NAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
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
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    safe_system = system_prompt.replace("{", "{{").replace("}", "}}")

    return ChatPromptTemplate.from_messages(
        [
            ("system", safe_system),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    try:
        chat_prompt = build_chat_prompt(prompt_data)
    except Exception as e:
        print(f"❌ Erro ao montar o ChatPromptTemplate: {e}")
        return False

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get(
        "description", "Prompt otimizado para converter bugs em User Stories"
    )
    tags = list(prompt_data.get("tags", []))
    tags += [t.lower().replace(" ", "-") for t in techniques]
    tags = sorted(set(tags))

    readme = (
        f"# {prompt_name}\n\n"
        f"{description}\n\n"
        "**Técnicas de Prompt Engineering aplicadas:**\n"
        + "\n".join(f"- {t}" for t in techniques)
        + "\n\n**Variável de entrada:** `{bug_report}`\n"
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
    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt '{prompt_name}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- Você tem permissão de escrita no seu workspace do LangSmith")
        return False


def main():
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
