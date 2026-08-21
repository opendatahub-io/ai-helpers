# ADR 0002: Migrate User Profile Service from PostgreSQL to DynamoDB

## Status
Proposed

## Context
The User Profile service currently runs on a single PostgreSQL instance (db.r5.2xlarge). We have 40M users and expect to reach 200M within 2 years. Read QPS is ~8k peak, write QPS ~1.2k peak. p99 read latency is 45ms, which is acceptable, but we are seeing occasional connection pool exhaustion during traffic spikes. The schema is simple: a profile is a user_id plus a JSON blob of ~2KB. We rarely query by anything other than user_id. The team has 6 engineers, 2 of whom have prior DynamoDB experience.

## Decision Drivers
- Horizontal scalability to 200M users
- p99 read latency < 50ms
- Operational simplicity (small team)
- Cost predictability

## Considered Options
1. Shard the existing PostgreSQL cluster
2. Migrate to DynamoDB
3. Migrate to Aurora Serverless v2

## Decision
We will migrate to DynamoDB. Key-value access pattern matches DynamoDB's strengths, horizontal scale is handled by the service, and we avoid the ops burden of sharded Postgres.

## Consequences
### Positive
- Scales to 200M+ users without manual sharding.
- Predictable single-digit-ms reads on user_id lookups.
- Reduced ops burden (managed service).

### Negative
- We lose ad-hoc SQL. Analytics queries must go through a separate pipeline (we will export to S3 nightly).
- DynamoDB costs scale with provisioned capacity; we need careful capacity planning to avoid overpaying.
- The two engineers with DynamoDB experience become key-person dependencies until the rest of the team ramps up.
- Migration itself is non-trivial: we will run dual-writes for 30 days, then cut reads over, then decommission Postgres.

## Rollback
If DynamoDB proves unworkable, we can fall back to Postgres during the dual-write window. After cutover, rollback requires a reverse migration (estimated 2 weeks of engineering effort).
