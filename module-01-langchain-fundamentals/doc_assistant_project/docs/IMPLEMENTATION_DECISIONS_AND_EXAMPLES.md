# Implementation Decisions and Example Conversations

This document explains the main implementation decisions in the document assistant, how state and memory are handled, how structured outputs are enforced, and how the committed `logs/` and `sessions/` artifacts demonstrate the implemented features.

## Implementation Decisions

### LangGraph as the orchestration layer

The assistant uses LangGraph to make the workflow explicit instead of placing all logic in one prompt. The graph is defined in `src/agent.py` and follows this path:

1. `classify_intent`
2. One task-specific node:
   - `qa_agent`
   - `summarization_agent`
   - `calculation_agent`
3. `update_memory`
4. `END`

This design keeps routing, task execution, and memory update separate. The intent classifier only decides what kind of request the user made. The task nodes perform the actual work. The memory node summarizes what happened after the task is complete.

### Separate prompts by task type

Prompt text lives in `src/prompts.py`. The implementation uses separate system prompts for Q&A, summarization, and calculation so each task has different instructions:

- Q&A must search documents and cite document IDs.
- Summarization must retrieve and read relevant documents before summarizing.
- Calculation must retrieve/read source documents and use the calculator tool for arithmetic.

This keeps task behavior clearer than using one large general-purpose prompt.

### Simulated retrieval instead of a vector database

`src/retrieval.py` uses an in-memory `SimulatedRetriever` with hardcoded sample documents. This is intentional for the coursework scope: it demonstrates document retrieval patterns without requiring a database, embeddings, or external indexing infrastructure.

The retriever supports:

- keyword search
- document type search
- amount range search
- exact amount search
- approximate amount search
- lookup by document ID
- collection statistics

### Tools as deterministic boundaries

Tools are defined in `src/tools.py` and exposed to the ReAct agent. The main tools are:

- `calculator`: evaluates basic mathematical expressions.
- `document_search`: searches documents by keyword, type, or amount criteria.
- `document_reader`: reads a full document by ID.
- `document_statistics`: summarizes the in-memory document collection.

The key design decision is that the LLM decides when a tool is needed, but deterministic code performs retrieval and calculation. This reduces the chance that the model invents document contents or performs arithmetic mentally.

### Persistent evidence artifacts

The assistant writes two kinds of runtime artifacts:

- `logs/tool_usage_20260621_094135.json`: tool call audit log.
- `sessions/6a9dba93-bfb0-4cf8-8a83-a7e5288ea03e.json`: persisted conversation/session state.

These files are committed because they demonstrate that the assistant used tools, saved memory, and preserved conversation history across turns.

## State and Memory

### Runtime graph state

The graph state is defined by `AgentState` in `src/agent.py`. Important fields include:

- `user_input`: the current user request.
- `messages`: LangChain message history for the current graph run.
- `intent`: the structured intent classification.
- `next_step`: the route selected by the classifier.
- `conversation_summary`: memory summary generated after each turn.
- `active_documents`: document IDs considered relevant so far.
- `current_response`: raw agent result for the current task.
- `tools_used`: tool names observed in the agent trace.
- `session_id` and `user_id`: session ownership fields.
- `actions_taken`: graph nodes executed during the conversation.

`messages` uses LangGraph's `add_messages` reducer, and `actions_taken` uses `operator.add`, so repeated graph updates append instead of replacing those lists.

### Short-term checkpoint memory

`create_workflow()` compiles the graph with `InMemorySaver`. This gives LangGraph a thread-scoped checkpoint while the process is running. The thread ID is the active session ID:

```python
config = {
    "configurable": {
        "thread_id": self.current_session.session_id,
        "llm": self.llm,
        "tools": self.tools,
    }
}
```

This lets the workflow retrieve current graph state for the active session during the running process.

### Long-term session persistence

`DocumentAssistant._save_session()` writes the `SessionState` object to `sessions/<session_id>.json`. The saved session includes:

- `session_id`
- `user_id`
- `conversation_history`
- `document_context`
- `created_at`
- `last_updated`

After every successful graph run, `process_message()` appends the final graph state to `conversation_history`, updates `document_context` with active document IDs, updates `last_updated`, and writes the JSON file.

### Memory summary

After each task node, the graph runs `update_memory`. That node sends the latest chat history to the LLM with `MEMORY_SUMMARY_PROMPT` and enforces the `UpdateMemoryResponse` schema. It returns:

- `conversation_summary`: concise memory of what happened.
- `active_documents`: document IDs relevant to the latest message.

Example from `sessions/6a9dba93-bfb0-4cf8-8a83-a7e5288ea03e.json` after the first turn:

```text
The user requested the sum of all invoice totals. Three invoices were identified:
Invoice #12345 with a total of $22,000, Invoice #12346 with a total of $69,300,
and Invoice #12347 with a total of $214,500. The sum of these invoice totals is
$305,800.
```

By the third turn, memory includes prior calculation and retrieval context plus the contract summary.

## Structured Output Enforcement

Structured outputs are enforced with Pydantic schemas in `src/schemas.py`.

### Intent classification

`classify_intent()` calls:

```python
structured_llm = llm.with_structured_output(UserIntent)
```

The classifier must return:

- `intent_type`: one of `qa`, `summarization`, `calculation`, or `unknown`
- `confidence`
- `reasoning`

The graph uses `intent_type` to choose `qa_agent`, `summarization_agent`, or `calculation_agent`.

### Task responses

Each task-specific agent passes a response schema into `create_react_agent()`:

- Q&A uses `AnswerResponse`.
- Summarization uses `SummarizationResponse`.
- Calculation uses `CalculationResponse`.

The shared helper `invoke_react_agent()` passes the schema as `response_format`, so the model is expected to produce data matching the selected schema.

### Memory update

`update_memory()` uses:

```python
structured_llm = llm.with_structured_output(UpdateMemoryResponse)
```

This ensures memory updates have a predictable shape:

- `summary`
- `document_ids`

## Tool Logging

`ToolLogger` writes every tool call to JSON. Each log entry has:

- `timestamp`
- `tool_name`
- `input`
- `output`

The committed log file contains nine tool calls:

| # | Tool | Purpose |
|---|------|---------|
| 1 | `document_statistics` | Inspect collection totals before invoice calculation |
| 2 | `document_search` | Find invoice documents |
| 3 | `document_reader` | Read `INV-001` |
| 4 | `document_reader` | Read `INV-002` |
| 5 | `document_reader` | Read `INV-003` |
| 6 | `calculator` | Evaluate `22000 + 69300 + 214500` |
| 7 | `document_search` | Find documents over `$50,000` |
| 8 | `document_search` | Find contract documents |
| 9 | `document_reader` | Read `CON-001` |

This log is the audit trail proving that document lookup, reading, and arithmetic were performed through tools.

## Example Conversations from `sessions/` and `logs/`

### Example 1: Calculation over invoice documents

User:

```text
Calculate the sum of all invoice totals
```

Intent classification from the session:

```json
{
  "intent_type": "calculation",
  "confidence": 0.95,
  "reasoning": "The user's request explicitly asks for a calculation, specifically the sum of all invoice totals. This involves a mathematical operation, which aligns with the 'calculation' intent category."
}
```

Tool sequence from the log:

1. `document_statistics`
2. `document_search` with `doc_type="invoice"`
3. `document_reader` for `INV-001`
4. `document_reader` for `INV-002`
5. `document_reader` for `INV-003`
6. `calculator` with `expression="22000 + 69300 + 214500"`

Calculator log entry:

```json
{
  "tool_name": "calculator",
  "input": {
    "expression": "22000 + 69300 + 214500"
  },
  "output": "{'result': 305800}"
}
```

Assistant response from the session:

```text
The sum of all invoice totals is $305,800. This calculation is based on the following invoices:

- Invoice #12345: $22,000
- Invoice #12346: $69,300
- Invoice #12347: $214,500

These amounts were retrieved from documents INV-001, INV-002, and INV-003.
```

Features demonstrated:

- calculation intent routing
- document search
- document reading
- deterministic calculator use
- source document citation
- tool logging
- session memory update

### Example 2: Amount-based document retrieval

User:

```text
Find documents with amounts over $50,000
```

Intent classification from the session:

```json
{
  "intent_type": "calculation",
  "confidence": 0.95,
  "reasoning": "The user's request to \"Find documents with amounts over $50,000\" involves identifying documents based on a numerical threshold, which implies a need for comparison or filtering based on numerical values."
}
```

Tool call from the log:

```json
{
  "tool_name": "document_search",
  "input": {
    "query": "documents over $50,000",
    "search_type": "amount",
    "comparison": "over",
    "amount": 50000.0
  },
  "output": "{'results_count': 3}"
}
```

Assistant response from the session:

```text
Here are the documents with amounts over $50,000:

1. Invoice #12347 (ID: INV-003)
   - Type: Invoice
   - Amount: $214,500.00

2. Service Agreement (ID: CON-001)
   - Type: Contract
   - Amount: $180,000.00

3. Invoice #12346 (ID: INV-002)
   - Type: Invoice
   - Amount: $69,300.00
```

Features demonstrated:

- amount-aware retrieval
- metadata filtering
- result ranking by amount
- continuity from previous conversation history
- session document context update

### Example 3: Contract summarization

User:

```text
Summarize all contracts
```

Intent classification from the session:

```json
{
  "intent_type": "summarization",
  "confidence": 0.95,
  "reasoning": "The user's request 'Summarize all contracts' is a clear directive to extract key points or provide a concise overview of the contracts, which aligns with the 'summarization' intent."
}
```

Tool sequence from the log:

1. `document_search` with `doc_type="contract"`
2. `document_reader` for `CON-001`

Assistant response from the session:

```text
Contract Summary: Service Agreement (ID: CON-001)

- Parties Involved:
  - Provider: DocDacity Solutions Inc.
  - Client: Healthcare Partners LLC

- Effective Date: January 1, 2024
- Services Provided:
  1. Document Processing Platform Access
  2. 24/7 Technical Support
  3. Monthly Data Analytics Reports
  4. Compliance Monitoring

- Financial Details:
  - Monthly Fee: $15,000
  - Total Contract Value: $180,000

- Duration: 12 months
- Termination Clause: Either party may terminate the agreement with a 60-day written notice.
```

Features demonstrated:

- summarization intent routing
- contract search by document type
- full document reading before summarization
- document ID citation
- cumulative memory across turns

## Session Evidence Summary

The committed session file demonstrates three user turns:

| Turn | User input | Routed intent | Active documents after turn |
|------|------------|---------------|-----------------------------|
| 1 | `Calculate the sum of all invoice totals` | `calculation` | `INV-001`, `INV-002`, `INV-003` |
| 2 | `Find documents with amounts over $50,000` | `calculation` | `INV-001`, `INV-002`, `INV-003`, `CON-001` |
| 3 | `Summarize all contracts` | `summarization` | `INV-001`, `INV-002`, `INV-003`, `CON-001` |

The session proves that the assistant persists:

- user inputs
- message traces
- tool calls and tool responses
- intent classifications
- actions taken by graph nodes
- active document IDs
- rolling conversation summary

## Current Limitations

The implementation is a coursework-oriented assistant, not a production document platform. Current limitations include:

- Documents are hardcoded in memory rather than ingested from uploaded files.
- Retrieval is keyword and metadata based, not vector based.
- Calculator safety is limited to a character filter and restricted `eval`.
- Citation checking is prompt-driven rather than independently verified.
- `InMemorySaver` persists graph checkpoints only while the process is running.
- Long-term persistence is JSON file based, not a database.

These constraints keep the project simple enough to demonstrate LangChain tools, LangGraph state, structured outputs, and session persistence in one module.
