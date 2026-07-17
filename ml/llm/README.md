# FraudShield LLM Integration Layer

The `ml.llm` package provides a provider-agnostic abstraction for LLM communication across all FraudShield agents.

## Architecture

```
ml.llm/
  exceptions.py       Exception hierarchy (LLMProviderError and subclasses)
  schemas.py          Pydantic models for config and structured outputs
  base.py             Abstract BaseLLMProvider interface
  gemini_provider.py  Google Gemini implementation (google-generativeai SDK)
  factory.py          Provider factory with registry pattern
  parser.py           Response parsing and JSON extraction utilities
  client.py           Legacy LLMClient (preserved for backward compatibility)
  prompts.py          Legacy prompt template collection
  __init__.py         Public API exports
```

## Quick Start

```python
from ml.llm import create_llm_provider, InvestigationLLMResponse

# Create provider from environment (requires GEMINI_API_KEY)
provider = create_llm_provider("gemini")

# Raw text generation
text = await provider.generate("Analyse this claim data...")

# Structured generation with Pydantic validation
response = await provider.generate_structured(
    "Investigate provider PRV-001 for fraud patterns",
    InvestigationLLMResponse,
)
print(response.executive_summary)
print(f"Found {len(response.findings)} issues")
```

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Model identifier |
| `GEMINI_TEMPERATURE` | `0.3` | Sampling temperature |
| `GEMINI_MAX_TOKENS` | `4096` | Max tokens per completion |
| `GEMINI_TIMEOUT` | `60` | Per-request timeout (seconds) |
| `GEMINI_MAX_RETRIES` | `3` | Retry count for transient failures |

## Exception Hierarchy

```
LLMProviderError (base)
  ├── LLMConnectionError        Network / timeout failures
  ├── LLMRateLimitError          429 responses (includes retry_after)
  ├── LLMResponseError           Empty or unusable responses
  ├── LLMConfigError             Missing / invalid configuration
  └── LLMResponseValidationError Pydantic validation failure
```

## Response Schemas

### InvestigationLLMResponse

```json
{
  "executive_summary": "Provider shows upcoding patterns...",
  "findings": [
    {
      "category": "upcoding",
      "severity": "High",
      "description": "Systematic upcoding of E&M codes...",
      "evidence": ["CLM-001 ($5,200)", "CLM-002 ($4,800)"],
      "confidence": 0.87,
      "estimated_impact": 25000.0
    }
  ],
  "recommendations": [
    {
      "category": "audit",
      "priority": "Immediate",
      "description": "Conduct full E&M code audit",
      "rationale": "High confidence upcoding detected"
    }
  ]
}
```

## Factory Pattern

```python
from ml.llm import create_llm_provider, register_provider, list_providers

# List available providers
print(list_providers())  # ['gemini', ...]

# Register a custom provider
register_provider("anthropic", "ml.llm.anthropic_provider.AnthropicProvider")

# Create with explicit config
from ml.llm import LLMConfig
config = LLMConfig(provider="gemini", model="gemini-1.5-pro", temperature=0.1)
provider = create_llm_provider("gemini", config=config)
```

## Testing

All LLM calls in tests use mocked providers:

```python
from ml.llm.schemas import InvestigationLLMResponse, InvestigationFinding

class MockProvider(BaseLLMProvider):
    async def generate(self, prompt, **kwargs):
        return "Mock response"
    async def generate_structured(self, prompt, response_model, **kwargs):
        return response_model(executive_summary="Test", findings=[], recommendations=[])
    async def health_check(self):
        return True
```

Run tests: `python -m pytest ml/tests/test_llm_provider.py -v`
