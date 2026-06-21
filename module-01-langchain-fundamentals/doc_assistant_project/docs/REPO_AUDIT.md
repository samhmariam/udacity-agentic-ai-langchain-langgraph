# REPO AUDIT

## Scope
This audit covers the repository at [module-01-langchain-fundamentals/doc_assistant_project](../).

## Observed Facts

### 1) Repository Structure Summary
- Top-level files and folders present:
  - [module-01-langchain-fundamentals/doc_assistant_project/main.py](../main.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/pyproject.toml](../pyproject.toml)
  - [module-01-langchain-fundamentals/doc_assistant_project/requirements.txt](../requirements.txt)
  - [module-01-langchain-fundamentals/doc_assistant_project/README.md](../README.md)
  - [module-01-langchain-fundamentals/doc_assistant_project/src](../src)
  - [module-01-langchain-fundamentals/doc_assistant_project/sessions](../sessions)
  - [module-01-langchain-fundamentals/doc_assistant_project/.env](../.env)
  - [module-01-langchain-fundamentals/doc_assistant_project/uv.lock](../uv.lock)
- Source modules in [module-01-langchain-fundamentals/doc_assistant_project/src](../src):
  - [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py)

### 2) Main Application Entry Points
- CLI runtime entry point is [module-01-langchain-fundamentals/doc_assistant_project/main.py](../main.py), function main.
- Assistant orchestration entry point is [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py), class DocumentAssistant, method process_message.

### 3) Main Packages and Modules
- Session lifecycle and workflow invocation: [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py).
- Graph state and node definitions: [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py).
- Prompt templates and system prompts: [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py).
- Tool definitions and logging: [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).
- Retrieval abstraction and sample documents: [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py).
- Pydantic schemas for intent, responses, and session state: [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py).

### 4) Dependency Stack
- Declared dependencies are in [module-01-langchain-fundamentals/doc_assistant_project/pyproject.toml](../pyproject.toml):
  - langchain
  - langchain-core
  - langchain-openai
  - langgraph
  - openai
  - print-color
  - pydantic
  - python-dotenv
- Lock file present: [module-01-langchain-fundamentals/doc_assistant_project/uv.lock](../uv.lock).
- [module-01-langchain-fundamentals/doc_assistant_project/requirements.txt](../requirements.txt) currently contains only placeholder text and is not aligned to pyproject.

### 5) LangChain Usage
- Prompting classes used in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py): PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder.
- Tools built with decorator in [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py): langchain.tools.tool.
- LLM client in [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py): ChatOpenAI.

### 6) LangGraph Usage
- State graph and compile in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py): StateGraph, END, add_messages, InMemorySaver.
- ReAct-style agent construction in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py): create_react_agent.
- Nodes implemented: classify_intent, qa_agent, summarization_agent, calculation_agent, update_memory.

### 7) Document Ingestion Flow
- No external ingestion pipeline exists in code.
- Documents are loaded from hardcoded sample records in SimulatedRetriever._load_sample_documents at [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py).
- API to add a document exists via add_document in [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py), but no file parser or upload endpoint is present.

### 8) Retrieval and Vector Store Flow
- Retrieval is in-memory and keyword/metadata/range-based, not vector-based, in [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py).
- Search tool surfaces retrieval behavior in [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py), function create_document_search_tool.
- No embedding model, no vector index, no persistent retrieval store observed.

### 9) Prompt Templates
- Intent classifier prompt: get_intent_classification_prompt in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py).
- System prompts for QA, summarization, calculation in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py).
- Prompt router by intent via get_chat_prompt_template in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py).
- Memory summary prompt constant in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py).

### 10) Tools and Functions Exposed to Agent
- calculator in create_calculator_tool at [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).
- document_search in create_document_search_tool at [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).
- document_reader in create_document_reader_tool at [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).
- document_statistics in create_document_statistics_tool at [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).
- Tool registration list in get_all_tools at [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).

### 11) State Definitions
- Graph state typed dict AgentState in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py).
- Structured outputs in [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py):
  - UserIntent
  - AnswerResponse
  - SummarizationResponse
  - CalculationResponse
  - UpdateMemoryResponse
  - SessionState
  - DocumentChunk

### 12) Tests and Coverage
- No test files were found in this project directory.
- No coverage tooling configuration found in repository files inspected.

### 13) Configuration and Environment Variables
- Environment loading done in [module-01-langchain-fundamentals/doc_assistant_project/main.py](../main.py) with load_dotenv.
- Required env variable checked in runtime: OPENAI_API_KEY in [module-01-langchain-fundamentals/doc_assistant_project/main.py](../main.py).
- Additional values shown in template env file [module-01-langchain-fundamentals/doc_assistant_project/.env](../.env): MODEL_NAME, TEMPERATURE, SESSION_STORAGE_PATH.
- Current code does not consume MODEL_NAME/TEMPERATURE/SESSION_STORAGE_PATH from env in main.py.

### 14) Existing Documentation
- Primary documentation/instructions in [module-01-langchain-fundamentals/doc_assistant_project/README.md](../README.md).
- README includes architecture intent, implementation tasks, and expected behavior.

### 15) Missing or Incomplete Pieces
- requirements.txt is placeholder and does not provide installable dependency list: [module-01-langchain-fundamentals/doc_assistant_project/requirements.txt](../requirements.txt).
- No automated tests for tools, retrieval, graph routing, or schema conformance.
- No evaluation datasets, no quality metrics, no regression harness.
- No real document ingestion/parsing pipeline beyond hardcoded samples.
- No vector retrieval or citation span extraction strategy.
- No explicit safety policy layer for healthcare/financial high-risk outputs.
- No explicit access control, encryption-at-rest strategy, or retention policy implementation.
- No CI workflow files found in this folder.

## Assumptions and Inferences (Explicit)
- README positions this as an instructional exercise project rather than production-ready system.
- The architecture is likely intended to evolve toward production patterns, but current implementation is best classified as an educational baseline.
- Hardcoded base_url in LLM initialization suggests course lab environment constraints.

## Key Audit Risks
- Misalignment risk between README-stated goals and implemented capabilities.
- Accuracy risk due to LLM-driven responses without mandatory deterministic verification layer.
- Safety risk in healthcare/financial domains due absent hard guardrails and test coverage.
