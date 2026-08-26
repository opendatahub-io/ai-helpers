# ADR 0001: Adopt Kafka as the Company Event Bus

## Status
Proposed

## Context
We currently have five services that communicate via direct HTTP calls. As we add more services, the point-to-point coupling is becoming a problem. We want an event bus.

## Decision
We will adopt Apache Kafka as the company-wide event bus. All services will publish domain events to Kafka topics and consume events they care about.

## Consequences
- Services are decoupled.
- We get a durable event log.
- Kafka is industry standard.
