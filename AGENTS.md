# Agents

This project separates concerns into pluggable components:
- data agent
- strategy agent
- risk agent
- execution connector agent
- reconciliation agent

Each agent integration should implement interfaces under `src/algotradeplan/plugins` and include tests with fakes/mocks.
