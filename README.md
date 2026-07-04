# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Software que faz **pull** de um prompt de baixa qualidade do LangSmith Prompt Hub,
o **refatora** com técnicas avançadas de Prompt Engineering, faz **push** da versão
otimizada de volta ao Hub e **avalia** o resultado com 5 métricas customizadas
(Helpfulness, Correctness, F1-Score, Clarity, Precision), buscando **≥ 0.8 em todas**.

Caso de uso: converter **relatos de bug** em **User Stories** ágeis, claras e testáveis.

---

## A) Técnicas Aplicadas (Fase 2)

O prompt otimizado ([`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml))
combina **3 técnicas** de Prompt Engineering. A técnica obrigatória (Few-shot) mais duas
adicionais:

### 1. Role Prompting (persona)
**Por quê:** dar ao modelo uma identidade especializada calibra vocabulário, nível de
detalhe e critérios de qualidade. Um "Product Manager sênior de Scrum" naturalmente
escreve histórias centradas no usuário e critérios testáveis.

**Como apliquei:**
```
# PAPEL
Você é um Product Manager sênior, especialista em metodologias ágeis (Scrum)
e em escrever User Stories de altíssima qualidade...
```

### 2. Few-shot Learning (obrigatória)
**Por quê:** exemplos de entrada→saída são a forma mais eficaz de fixar **formato**,
**tom** e **nível de completude** esperados. Reduzem drasticamente a variância da saída e
alinham o modelo ao *estilo do ground truth* usado na avaliação.

**Como apliquei:** 3 exemplos cobrindo complexidades diferentes — bug simples de UI,
bug médio **com contexto técnico** (log/exceção) e bug de dados/relatório — cada um no
formato exato "Como um… eu quero… para que…" + Critérios de Aceitação Dado/Quando/Então:
```
## Exemplo 2 — bug médio com contexto técnico
Bug Report:
Ao aplicar cupom de desconto no checkout, a API retorna erro 500 ... NullPointerException...

User Story:
Como um cliente finalizando uma compra, eu quero aplicar um cupom de desconto válido...
Critérios de Aceitação:
- Dado que informei um cupom de desconto válido no checkout
- Quando confirmo a finalização do pedido
- Então o desconto deve ser aplicado corretamente ao valor total
...
Contexto Técnico:
- Tratar o NullPointerException em CouponService.apply() ...
```

### 3. Chain of Thought (CoT)
**Por quê:** transformar um bug (às vezes vago/técnico) em User Story exige raciocínio:
identificar persona, funcionalidade, valor e critérios. Pensar passo a passo antes de
escrever melhora **correção** e **completude**. Instruí o modelo a raciocinar
**internamente** e emitir **apenas** a história final — assim o CoT eleva a qualidade sem
poluir a saída (o que protegeria as métricas de Precision e Clarity).

**Como apliquei:**
```
# RACIOCÍNIO (Chain of Thought — pense internamente, NÃO exiba estas etapas)
1. Quem é o usuário afetado pelo bug?
2. Qual funcionalidade esse usuário espera?
3. Qual é o valor de negócio de resolver isso?
4. Quais condições comprovam que o bug foi resolvido? (viram os Critérios de Aceitação)
5. O relato traz detalhes técnicos? Só então inclua Contexto Técnico.
```

### Demais requisitos do prompt otimizado
- **Instruções claras e específicas** e **regras explícitas de comportamento** (seção
  "REGRAS EXPLÍCITAS DE COMPORTAMENTO").
- **Tratamento de edge cases**: relato vago, múltiplos problemas, relato puramente
  técnico, ou pedido de melhoria (seção "TRATAMENTO DE EDGE CASES").
- **System vs User Prompt**: instruções ficam no `system_prompt`; a variável
  `{bug_report}` fica no `user_prompt` (mensagem humana).
- **Formato**: saída em **Markdown**, no padrão de User Story.

---

## B) Resultados Finais

Provider usado na avaliação: **OpenAI** — resposta `gpt-4o-mini`, avaliação (LLM-as-Judge)
`gpt-4o`. Resultado **APROVADO** (todas as 5 métricas ≥ 0.8), confirmado em 2 execuções.

- **Prompt público v2:** https://smith.langchain.com/hub/pedrohubner/bug_to_user_story_v2
- **Dataset de avaliação:** `prompt-optimization-challenge-eval` (15 exemplos) — visível
  no dashboard em **Datasets & Experiments**.
- **Projeto de tracing:** `prompt-optimization-challenge` (200 runs: geração das user
  stories + avaliadores F1/Clarity/Precision) — em **Tracing**.
- **Tracing público de 3 exemplos** (abrem sem login):
  - Botão adicionar ao carrinho: https://smith.langchain.com/public/b30de827-c4b6-4641-9dec-42fee6f7dc97/r
  - Validação de e-mail: https://smith.langchain.com/public/9cd5de3e-0820-462c-ab0f-3705e2254574/r
  - Layout iOS em paisagem: https://smith.langchain.com/public/e13417ca-beec-4fc0-931a-c2eb5061fde7/r
- **Screenshots (opcional):** se quiser anexar imagens, salve em `screenshots/` e
  referencie aqui _(ex.: `![aprovado](screenshots/eval-aprovado.png)`)_.

### Tabela comparativa v1 (ruim) × v2 (otimizado)

| Métrica          | v1 (baixa qualidade)¹ | v2 — run 1 | v2 — run 2 | Meta   |
|------------------|:---------------------:|:----------:|:----------:|:------:|
| Helpfulness      | 0.45 ✗                | 0.85 ✓     | 0.87 ✓     | ≥ 0.80 |
| Correctness      | 0.52 ✗                | 0.81 ✓     | 0.83 ✓     | ≥ 0.80 |
| F1-Score         | 0.48 ✗                | 0.81 ✓     | 0.81 ✓     | ≥ 0.80 |
| Clarity          | 0.50 ✗                | 0.89 ✓     | 0.90 ✓     | ≥ 0.80 |
| Precision        | 0.46 ✗                | 0.82 ✓     | 0.85 ✓     | ≥ 0.80 |
| **Média**        | ~0.48                 | **0.8374** | **0.8533** | ≥ 0.80 |
| **Status**       | ❌ REPROVADO          | ✅ APROVADO | ✅ APROVADO | —      |

> ¹ Coluna v1: valores ilustrativos do enunciado (ponto de partida). As colunas v2 são
> saídas reais de `src/evaluate.py` em duas execuções consecutivas do mesmo prompt
> publicado, evidenciando estabilidade do resultado.

### Processo de otimização (8 iterações)
Resumo do que cada iteração corrigiu, guiado pelo *reasoning* do juiz F1 no tracing:
1. Baseline com Role + Few-shot + CoT → média ~0.81, F1/Correctness < 0.8.
2. Escala de detalhe por complexidade + ator "sistema" para bugs de backend.
3. Bug simples fica enxuto mesmo com números; sem inventar benefícios → Precision ↑.
4. Convenções de critérios + identificação de ator por domínio → recall ↑.
5. Critérios genéricos e concisos (sem especificidades incidentais).
6. Gatilhos de "médio" para modal/estoque + não contradizer a solução.
7. Few-shots concretos de acessibilidade (modal) e prevenção (estoque).
8. Meta de performance = tempo rápido (nunca repetir o tempo ruim) + proibição de
   nomear atores/quantidades do passo-a-passo nos critérios → **APROVADO**.

**Evidências no LangSmith:**
- ✅ Dataset de avaliação com 15 exemplos (`prompt-optimization-challenge-eval`).
- ✅ Execuções do prompt v2 com notas ≥ 0.8 (saída do `src/evaluate.py`, acima).
- ✅ Tracing detalhado com o raciocínio do LLM e dos avaliadores — 3 traces públicos
  linkados acima (input do bug → user story gerada → score + reasoning do juiz).

---

## C) Como Executar

### Pré-requisitos
- Python **3.9+**
- Conta no **LangSmith** ([smith.langchain.com](https://smith.langchain.com)) e uma API Key
- Uma API Key de LLM: **OpenAI** e/ou **Google Gemini**

### 1. Ambiente virtual e dependências
```bash
python3 -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar credenciais
Copie o template e preencha suas chaves:
```bash
cp .env.example .env
```
Variáveis principais do `.env`:
```env
LANGSMITH_API_KEY=...
USERNAME_LANGSMITH_HUB=seu_username        # visível no cadeado 🔒 de qualquer prompt seu
LLM_PROVIDER=google                        # 'google' (Gemini) ou 'openai'
LLM_MODEL=gemini-2.5-flash                 # responder: gemini-2.5-flash | gpt-4o-mini
EVAL_MODEL=gemini-2.5-flash                # avaliador: gemini-2.5-flash | gpt-4o
GOOGLE_API_KEY=...                         # se LLM_PROVIDER=google
# OPENAI_API_KEY=...                       # se LLM_PROVIDER=openai
```

### 3. Fluxo completo (na ordem)
```bash
# 1) Pull do prompt ruim (salva em prompts/bug_to_user_story_v1.yml)
python src/pull_prompts.py

# 2) (já feito) refatorar: prompts/bug_to_user_story_v2.yml

# 3) Push do prompt otimizado (público) -> {seu_username}/bug_to_user_story_v2
python src/push_prompts.py

# 4) Avaliação automática (pull do v2 + 5 métricas + publica no dashboard)
python src/evaluate.py
```

### 4. Testes de validação
```bash
pytest tests/test_prompts.py -v
```
Cobrem: existência/preenchimento do `system_prompt`, definição de persona, exigência de
formato (Markdown/User Story), presença de exemplos Few-shot, ausência de `[TODO]` e
mínimo de 2 técnicas nos metadados.

### 5. Iteração até ≥ 0.8
Se alguma métrica ficar abaixo de 0.8: ajuste `prompts/bug_to_user_story_v2.yml`
(mais/menos detalhe, exemplos melhores, regras mais específicas) → `push_prompts.py` →
`evaluate.py`. Repita (3–5 iterações são normais). Use o **Tracing** do LangSmith como
principal ferramenta de debug.

---

## Estrutura do Projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt inicial (baixa qualidade)
│   └── bug_to_user_story_v2.yml   # prompt otimizado ✅
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 bugs (não alterar)
├── src/
│   ├── pull_prompts.py            # pull do Hub            (implementado)
│   ├── push_prompts.py            # push público + metadados (implementado)
│   ├── evaluate.py                # avaliação (pronto)
│   ├── metrics.py                 # 5 métricas (pronto)
│   └── utils.py                   # auxiliares (pronto)
└── tests/
    └── test_prompts.py            # 7 testes (implementado)
```

## Notas de implementação
- `pull_prompts.py` extrai `system_prompt`/`user_prompt` de qualquer `ChatPromptTemplate`
  ou `PromptTemplate` retornado pelo Hub e serializa em YAML.
- `push_prompts.py` monta um `ChatPromptTemplate` com **uma única variável**
  (`{bug_report}`, exigida pelo dataset), **escapando chaves literais** dos exemplos
  few-shot para não serem interpretadas como variáveis, e publica com `is_public=True`
  incluindo descrição, README e tags (técnicas aplicadas).
- As instruções (system) e a entrada variável (user) ficam separadas — boa prática de
  System vs User Prompt.
