"""
Agentic AutoML Intelligence Platform — CDC Ingestion Agent
Processes real-time Change Data Capture events and feeds the feature store.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from streaming.schemas import CDCEvent, CDCEventBatch, CDCOperation
from streaming.pipeline import cdc_pipeline


class CDCIngestionAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="CDCIngestionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        raw_events = input_data.parameters.get("events", [])
        if not raw_events and "payload" in input_data.parameters:
            raw_events = [input_data.parameters]

        processed_events = []
        for e in raw_events:
            event = CDCEvent(
                source=e.get("source", "realtime_stream"),
                entity_id=str(e.get("entity_id", "unknown_entity")),
                operation=CDCOperation(e.get("operation", "INSERT")),
                payload=e.get("payload", e),
            )
            processed_event = cdc_pipeline.process_event(event)
            processed_events.append(processed_event.model_dump())

        metrics = cdc_pipeline.get_metrics()
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"events": processed_events, "pipeline_metrics": metrics},
            summary=f"Processed {len(processed_events)} CDC events into FeatureStore. Lifetime: {metrics['processed']} processed, {metrics['duplicates']} duplicates.",
        )
