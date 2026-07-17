# FraudShield Agent Framework

Multi-agent orchestration system for healthcare fraud detection,
built on **LangGraph** with a deterministic sequential workflow.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                      │
│                                                              │
│  START                                                       │
│    │                                                         │
│    ▼                                                         │
│  ┌──────────────────────┐                                    │
│  │  Investigation Agent  │  Validates pipeline output,       │
│  │  (investigation_agent)│  produces initial findings        │
│  └──────────┬───────────┘                                    │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────┐                                    │
│  │    Knowledge Agent    │  Retrieves regulatory and         │
│  │   (knowledge_agent)   │  case context from knowledge base │
│  └──────────┬───────────┘                                    │
│             │                                                │
│             ▼                                                │
│  ┌───────────────────────────┐                               │
│  │  Fraud Intelligence Agent  │  Deep analysis, pattern      │
│  │ (fraud_intelligence_agent) │  matching, impact estimation │
│  └──────────┬────────────────┘                               │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────┐                                    │
│  │     Report Agent      │  Assembles final report for       │
│  │    (report_agent)     │  PDF generation                   │
│  └──────────┬───────────┘                                    │
│             │                                                │
│             ▼                                                │
│            END                                               │
└─────────────────────────────────────────────────────────────┘
```

## Package Structure

```
ml/agents/
├── __init__.py              # Public API exports (legacy + LangGraph)
├── state.py                 # InvestigationState TypedDict definition
├── utils.py                 # State factory, log helpers, validation
├── supervisor.py            # Graph topology and routing logic
├── graph.py                 # Workflow builder and runner (public API)
├── base_agent.py            # Abstract BaseAgent (legacy interface)
├── supervisor_agent.py      # Legacy SupervisorAgent orchestrator
├── risk_agent.py            # Risk assessment agent (fully implemented)
├── investigation_agent.py   # Investigation agent + LangGraph node
├── knowledge_agent.py       # Knowledge retrieval agent node
├── fraud_intelligence_agent.py  # Fraud intelligence agent node
├── report_agent.py          # Report agent + LangGraph node
├── prompts/                 # LLM prompt templates (Phase 4C-F)
│   ├── investigation.txt    # Investigation prompt template
│   ├── fraud.txt            # Fraud intelligence prompt template
│   └── report.txt           # Report generation prompt template
└── tests/
    ├── test_graph.py        # Graph compilation and execution tests
    ├── test_supervisor.py   # Graph topology and routing tests
    └── test_agents.py       # Individual agent node tests
```

## State Schema

The workflow uses `InvestigationState` (`TypedDict`) as the shared
state object. All fields are optional (`total=False`) because the
state is populated progressively:

| Field | Type | Populated By |
|-------|------|-------------|
| `investigation_id` | `str` | Workflow initialisation |
| `provider_id` | `str` | Workflow initialisation |
| `csv_data` | `Any` | Workflow initialisation |
| `features` | `Any` | Pipeline (FeatureBuilder) |
| `prediction` | `dict` | Pipeline (Predictor) |
| `fraud_score` | `float` | Pipeline (RiskScorer) |
| `risk_level` | `str` | Pipeline (RiskScorer) |
| `indicators` | `list[dict]` | Pipeline (ExplainabilityEngine) |
| `provider_statistics` | `dict` | Pipeline (ExplainabilityEngine) |
| `retrieved_documents` | `list[dict]` | Knowledge Agent |
| `ai_findings` | `list[dict]` | Investigation + Intelligence Agents |
| `recommendations` | `list[dict]` | All agents (accumulated) |
| `report` | `dict` | Report Agent |
| `metadata` | `dict` | Any agent |
| `status` | `str` | Every node |
| `execution_log` | `list[dict]` | Every node |

## Usage

```python
from ml.agents import create_initial_state, run_workflow

# 1. Create initial state with pipeline results.
state = create_initial_state(
    provider_id="PRV-001",
    csv_data=df,
)
state["features"] = features_df
state["prediction"] = prediction
state["risk_level"] = "High"
state["indicators"] = indicators

# 2. Run the full workflow.
final_state = run_workflow(state)

# 3. Inspect results.
print(final_state["status"])        # "completed"
print(final_state["report"])        # Structured report dict
print(final_state["execution_log"]) # Full audit trail
```

## Testing

```bash
# Run all LangGraph agent tests.
python -m pytest ml/tests/test_agents.py -v

# Run graph and supervisor tests.
python -m pytest ml/tests/test_supervisor.py ml/tests/test_graph.py -v

# Run the full test suite (60 tests).
python -m pytest ml/tests/test_agents.py ml/tests/test_supervisor.py ml/tests/test_graph.py -v
```

## Future Phases

| Phase | Component | Description |
|-------|-----------|-------------|
| 4C | Gemini Investigation Agent | LLM-powered evidence analysis and narrative generation |
| 4D | ChromaDB Knowledge Agent | Vector search for regulatory documents and prior cases |
| 4E | Fraud Intelligence Agent | Multi-step reasoning for pattern identification |
| 4F | Autonomous Workflow | Conditional routing, parallel execution, human-in-the-loop |

## Design Decisions

- **TypedDict over Pydantic** for LangGraph state: LangGraph's
  `StateGraph` works natively with TypedDict, avoiding validation
  overhead during graph execution while maintaining type safety.

- **Deterministic routing (Phase 4B)**: All nodes execute in sequence.
  Conditional routing will be added in Phase 4F based on risk level,
  findings severity, and knowledge base relevance.

- **Coexistence with legacy framework**: The `BaseAgent` + `SupervisorAgent`
  pattern continues to work. Both interfaces can be used independently
  or during the migration period.

- **No LLM calls yet**: All agent nodes produce placeholder outputs
  with TODO markers. The prompt templates in `prompts/` define the
  exact format that will be used when Gemini is integrated.
