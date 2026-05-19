# Agents and Automation Policy

## Agent Domains
AlgoTradePlan organizes automated responsibilities into pluggable agent families:
- **data agent**: ingestion, normalization, quality, storage, provenance
- **strategy agent**: signal generation and decision preparation
- **risk agent**: policy evaluation and trade approval
- **execution connector agent**: venue transport and order submission
- **reconciliation agent**: local-vs-remote state comparison and repair guidance

## Contract Locations
| Agent | Primary Interface Root | Expected Behavior |
| --- | --- | --- |
| Data | `/src/algotradeplan/plugins/data/interfaces.py` | fetch data, validate quality, persist, record provenance |
| Strategy | `/src/algotradeplan/plugins/interfaces.py` | emit normalized signal payloads |
| Risk | `/src/algotradeplan/plugins/interfaces.py` | approve or reject intents with reasons |
| Execution | `/src/algotradeplan/plugins/interfaces.py` | submit orders and return transport state |
| Reconciliation | `/src/algotradeplan/plugins/interfaces.py` | compare snapshots and surface drift |

## Working Rules
- every agent integration must implement the documented protocol before orchestration code is added
- new agents require example plugins and deterministic tests with fakes or mocks
- data-domain expansion must stay within the active phase and update `/docs/DATA_STRATEGY.md`
- no later-phase automation may bypass the current phase checklist or approval gate

## Automation API Expectations
- inputs and outputs should be explicit dictionaries or dataclass-backed contracts
- plugin ids must be stable and unique
- quality, provenance, and audit hooks should be treated as API surface, not optional extras
- operational automation must reference a runbook under `/docs/runbooks`

## Review Policy for Agent Changes
- confirm the phase doc allows the new capability
- review interface changes first, implementation second
- require tests for success and failure paths
- record any durable design choice in the master decision log
