import re
import pytest
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    assert V2_PATH.exists(), f"Arquivo do prompt não encontrado: {V2_PATH}"
    data = load_prompts(str(V2_PATH))
    assert isinstance(data, dict), "YAML do prompt inválido"
    return data.get(V2_KEY, data)


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        system_prompt = prompt["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        system_prompt = prompt.get("system_prompt", "").lower()
        role_markers = ["você é um", "você é uma", "voce e um", "atue como", "seu papel"]
        assert any(marker in system_prompt for marker in role_markers), (
            "O prompt não define uma persona/role (ex: 'Você é um Product Manager')"
        )
        assert "product manager" in system_prompt, (
            "A persona esperada (Product Manager) não foi encontrada"
        )

    def test_prompt_mentions_format(self, prompt):
        system_prompt = prompt.get("system_prompt", "").lower()
        mentions_markdown = "markdown" in system_prompt
        mentions_user_story_format = (
            "como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
        )
        assert mentions_markdown or mentions_user_story_format, (
            "O prompt não exige formato Markdown nem o padrão de User Story"
        )

    def test_prompt_has_few_shot_examples(self, prompt):
        system_prompt = prompt.get("system_prompt", "").lower()
        assert "exemplo" in system_prompt, "Nenhum exemplo (few-shot) encontrado"
        assert "bug report:" in system_prompt, "Exemplos não trazem a entrada (Bug Report)"
        assert "user story:" in system_prompt, "Exemplos não trazem a saída (User Story)"
        assert system_prompt.count("bug report:") >= 2, (
            "São esperados pelo menos 2 exemplos few-shot"
        )

    def test_prompt_no_todos(self, prompt):
        blob = " ".join(
            str(v) for v in prompt.values() if isinstance(v, (str, int, float))
        )
        placeholders = re.findall(r"\[TODO\]|\bTODO\b\s*[:\-]|\bTODO\b(?=\s)|\[FIXME\]", blob)
        assert not placeholders, (
            f"O prompt ainda contém marcações de placeholder: {placeholders}"
        )

    def test_minimum_techniques(self, prompt):
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), (
            "'techniques_applied' deve ser uma lista nos metadados do YAML"
        )
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )
        joined = " ".join(techniques).lower()
        assert "few-shot" in joined or "few shot" in joined, (
            "A técnica obrigatória Few-shot Learning não está listada"
        )

    def test_prompt_structure_is_valid(self, prompt):
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
