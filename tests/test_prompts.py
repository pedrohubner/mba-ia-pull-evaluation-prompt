"""
Testes automatizados para validação de prompts.

Valida a estrutura e as técnicas de Prompt Engineering aplicadas no prompt
otimizado (prompts/bug_to_user_story_v2.yml), sem precisar de chamadas à API.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

# Caminho do prompt otimizado que será validado.
V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Retorna o dicionário do prompt v2 (conteúdo sob a chave raiz)."""
    assert V2_PATH.exists(), f"Arquivo do prompt não encontrado: {V2_PATH}"
    data = load_prompts(str(V2_PATH))
    assert isinstance(data, dict), "YAML do prompt inválido"
    # Suporta tanto {v2_key: {...}} quanto o conteúdo direto na raiz.
    return data.get(V2_KEY, data)


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        system_prompt = prompt["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt.get("system_prompt", "").lower()
        # Padrões que indicam definição de papel/persona.
        role_markers = ["você é um", "você é uma", "voce e um", "atue como", "seu papel"]
        assert any(marker in system_prompt for marker in role_markers), (
            "O prompt não define uma persona/role (ex: 'Você é um Product Manager')"
        )
        # A persona escolhida é a de Product Manager.
        assert "product manager" in system_prompt, (
            "A persona esperada (Product Manager) não foi encontrada"
        )

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt.get("system_prompt", "").lower()
        mentions_markdown = "markdown" in system_prompt
        # Estrutura padrão de User Story: "Como um... eu quero... para que..."
        mentions_user_story_format = (
            "como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
        )
        assert mentions_markdown or mentions_user_story_format, (
            "O prompt não exige formato Markdown nem o padrão de User Story"
        )

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt.get("system_prompt", "").lower()
        # Precisa apresentar exemplos com entrada (bug) e saída (user story).
        assert "exemplo" in system_prompt, "Nenhum exemplo (few-shot) encontrado"
        assert "bug report:" in system_prompt, "Exemplos não trazem a entrada (Bug Report)"
        assert "user story:" in system_prompt, "Exemplos não trazem a saída (User Story)"
        # Pelo menos 2 blocos de exemplo (2-3 recomendados).
        assert system_prompt.count("bug report:") >= 2, (
            "São esperados pelo menos 2 exemplos few-shot"
        )

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        # Verifica todos os campos textuais do prompt.
        blob = " ".join(
            str(v) for v in prompt.values() if isinstance(v, (str, int, float))
        )
        # Procura marcações de placeholder (não a palavra "metodologias" etc.):
        # [TODO], TODO:, TODO em caixa alta isolado, e [FIXME].
        placeholders = re.findall(r"\[TODO\]|\bTODO\b\s*[:\-]|\bTODO\b(?=\s)|\[FIXME\]", blob)
        assert not placeholders, (
            f"O prompt ainda contém marcações de placeholder: {placeholders}"
        )

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), (
            "'techniques_applied' deve ser uma lista nos metadados do YAML"
        )
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )
        # Few-shot é obrigatório pelo desafio.
        joined = " ".join(techniques).lower()
        assert "few-shot" in joined or "few shot" in joined, (
            "A técnica obrigatória Few-shot Learning não está listada"
        )

    def test_prompt_structure_is_valid(self, prompt):
        """Sanidade extra: usa o validador compartilhado de utils.py."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
