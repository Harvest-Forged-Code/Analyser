# ---
# name: data-pipeline-design
# description: >
#   Use when designing ETL/ELT pipelines, data validation, scheduling,
#   monitoring, and data quality frameworks. Covers batch and streaming
#   patterns, error handling, idempotency, and observability.
# trigger: >
#   When user asks to build a data pipeline, ETL, ELT, data ingestion,
#   data processing, data validation, or data quality system.
# references:
#   - CLAUDE.md [DATA-ML] section
# ---

# Data Pipeline Design Skill

## Purpose

Design and implement reliable, idempotent, and observable data pipelines
that move data from sources to destinations with proper validation, error
handling, and monitoring at every stage.

## Workflow — Follow Each Step in Order

### Step 1: Gather Requirements

Before writing any pipeline code, collect and document these requirements:

**Data Sources:**
- What are the source systems? (databases, APIs, files, streams, SaaS tools)
- What formats? (CSV, JSON, Parquet, Avro, database tables, API responses)
- What authentication is needed? (API keys, OAuth, DB credentials, IAM roles)
- What are the data schemas? (obtain sample data or schema definitions)
- Are schemas stable or do they change without notice?

**Data Destinations:**
- Where does the data need to go? (data warehouse, data lake, another DB, API)
- What format is required at the destination?
- Are there schema requirements or constraints at the destination?

**Volume and Velocity:**
- How much data per run? (rows, GB)
- How often does it need to run? (real-time, hourly, daily, weekly)
- Is the data volume growing? At what rate?
- Peak vs average volume?

**SLAs and Constraints:**
- Maximum acceptable latency (source event to destination availability)
- Maximum acceptable data loss (zero loss? best effort?)
- Retention requirements (how long to keep raw and processed data)
- Compliance requirements (PII handling, data residency, encryption)

**Document the answers in a pipeline specification before proceeding.**

### Step 2: Explore Existing Pipelines and Data Infrastructure

Survey the current data landscape:

1. **Existing pipelines**: Are there other pipelines already running? What
   tools do they use (Airflow, Prefect, dbt, Luigi, custom scripts)?
2. **Orchestration**: Is there an existing scheduler/orchestrator?
3. **Compute**: What compute is available? (local, cloud functions, Spark,
   Kubernetes, dedicated workers)
4. **Storage**: What storage is available? (S3, GCS, HDFS, local filesystem)
5. **Catalog/Registry**: Is there a data catalog or schema registry?
6. **Monitoring**: Is there existing monitoring/alerting infrastructure?
7. **Conventions**: Are there naming conventions, folder structures, or
   patterns that existing pipelines follow?

Align the new pipeline with existing infrastructure and patterns wherever
possible. Do not introduce new tools without justification.

### Step 3: Choose Pipeline Pattern

Select the appropriate pattern based on requirements from Step 1:

#### ETL (Extract-Transform-Load)
**Use when:**
- Transformations are complex and require application logic
- Data must be cleaned/validated before loading
- Destination has strict schema requirements
- Volume is moderate (fits in memory or can be chunked)

```
Source --> Extract --> Transform --> Validate --> Load --> Destination
```

#### ELT (Extract-Load-Transform)
**Use when:**
- Destination is a powerful query engine (data warehouse like BigQuery,
  Snowflake, Redshift)
- Transformations are SQL-expressible
- You want to keep raw data for reprocessing
- Volume is large and warehouse can handle the compute

```
Source --> Extract --> Load (raw) --> Transform (in warehouse) --> Curated tables
```

#### Streaming
**Use when:**
- Latency requirement is sub-minute
- Data arrives as a continuous stream (Kafka, Kinesis, Pub/Sub)
- Processing is event-driven
- Real-time aggregations or alerts are needed

```
Source --> Stream --> Process (per-event or micro-batch) --> Sink
```

**Document the chosen pattern and the rationale for the choice.**

### Step 4: Design Pipeline Stages

Design each stage of the pipeline with specific implementation details:

#### 4a: Extract Stage

- **Source connectors**: Identify or build connectors for each source system.
  Use existing libraries where possible (e.g., `sqlalchemy` for databases,
  `requests`/`httpx` for APIs, `boto3` for S3, `google-cloud-storage` for GCS)
- **Schema inference**: If source schema is not documented, infer it from
  sample data. Pin the schema to detect drift
- **Incremental vs full load**: Choose the extraction strategy:

| Strategy       | When to Use                                  | Implementation                     |
|----------------|----------------------------------------------|-------------------------------------|
| **Full load**  | Small tables, no reliable change tracking    | `SELECT *` or full file download   |
| **Incremental**| Large tables with reliable timestamp/ID      | `WHERE updated_at > last_run`      |
| **CDC**        | Need real-time changes, source supports it   | Debezium, DMS, WAL-based capture   |
| **Snapshot diff** | No change tracking, need incremental     | Compare current vs previous snapshot|

- **Rate limiting**: Respect API rate limits; implement backoff and retry
- **Pagination**: Handle paginated API responses; track cursor/offset state

```python
# Example: Incremental extract with watermark
def extract_orders(db_session, watermark: datetime) -> Iterator[dict]:
    """Extract orders modified since the last watermark."""
    query = (
        db_session.query(Order)
        .filter(Order.updated_at > watermark)
        .order_by(Order.updated_at.asc())
        .yield_per(1000)  # stream results, do not load all into memory
    )
    for order in query:
        yield order_to_dict(order)
```

#### 4b: Transform Stage

- **Validation**: Validate data at entry to the transform stage. Use
  schema validation libraries:
  - Python: `pandera`, `great_expectations`, `pydantic`, `cerberus`
  - SQL: dbt tests, custom SQL assertions
- **Cleaning**: Handle nulls, duplicates, encoding issues, type coercion
- **Enrichment**: Join with reference data, geocode, resolve foreign keys
- **Aggregation**: Pre-aggregate if downstream consumers need summaries
- **Type safety**: Enforce column types and constraints throughout

```python
import pandera as pa
from pandera import Column, Check

# Define expected schema with validation rules
order_schema = pa.DataFrameSchema({
    "order_id": Column(str, Check.str_matches(r"^ORD-\d{8}$"), nullable=False),
    "customer_id": Column(str, nullable=False),
    "amount": Column(float, Check.greater_than(0), nullable=False),
    "currency": Column(str, Check.isin(["USD", "EUR", "GBP"]), nullable=False),
    "created_at": Column(pa.DateTime, nullable=False),
    "status": Column(str, Check.isin(["pending", "shipped", "delivered", "cancelled"])),
})

def transform_orders(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Validate, clean, and transform raw orders."""
    # Validate against schema — raises on failure
    validated = order_schema.validate(raw_df)

    # Clean
    cleaned = validated.drop_duplicates(subset=["order_id"])
    cleaned["amount"] = cleaned["amount"].round(2)

    # Enrich
    cleaned["amount_usd"] = cleaned.apply(convert_to_usd, axis=1)

    return cleaned
```

#### 4c: Load Stage

- **Target format**: Write in the format the destination expects (Parquet for
  data lakes, INSERT for databases, API calls for SaaS destinations)
- **Partitioning**: Partition output by date, region, or another high-cardinality
  dimension to enable efficient querying and selective reprocessing
- **Upsert strategy**: Choose how to handle existing records:

| Strategy       | When to Use                                        |
|----------------|----------------------------------------------------|
| **Append**     | Event/log data that is never updated               |
| **Upsert**     | Dimension data that can be updated (MERGE/ON CONFLICT) |
| **Replace**    | Full partition replacement (swap atomically)        |
| **SCD Type 2** | Need to track historical changes to dimension data |

```python
# Example: Atomic partition replacement
def load_orders(df: pd.DataFrame, partition_date: str, output_path: str):
    """Load orders with atomic partition swap."""
    partition_path = f"{output_path}/date={partition_date}"
    staging_path = f"{partition_path}._staging"

    # Write to staging location
    df.to_parquet(staging_path, index=False)

    # Atomic swap: remove old partition, rename staging
    if os.path.exists(partition_path):
        shutil.rmtree(partition_path)
    os.rename(staging_path, partition_path)
```

### Step 5: Design Error Handling

Every pipeline must handle failures gracefully:

1. **Dead letter queues (DLQ)**: Records that fail validation or processing
   are sent to a DLQ for manual inspection, not silently dropped

```python
def process_record(record: dict, dlq: list) -> Optional[dict]:
    """Process a record; send to DLQ on failure."""
    try:
        validated = validate(record)
        transformed = transform(validated)
        return transformed
    except ValidationError as e:
        dlq.append({
            "record": record,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "stage": "validation",
        })
        return None
```

2. **Retry logic**: Transient failures (network errors, rate limits, lock
   contention) should be retried with exponential backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def fetch_from_api(url: str) -> dict:
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

3. **Alerting**: Failures that exceed retry limits must trigger alerts
   (email, Slack, PagerDuty) with actionable information:
   - Which pipeline failed
   - Which stage failed
   - What error occurred
   - How many records were affected
   - Link to logs for investigation

4. **Partial failure handling**: Decide whether a batch with some failed
   records should commit the successes or fail the entire batch. Document
   the decision.

### Step 6: Design Monitoring and Observability

Every pipeline must emit metrics for operational visibility:

**Row-level metrics:**
- Records extracted from source
- Records passing validation
- Records failing validation (with reason breakdown)
- Records loaded to destination
- Records sent to DLQ

**Quality metrics:**
- Null rate per column (alert if exceeds threshold)
- Duplicate rate
- Schema drift detection (new columns, type changes, missing columns)
- Value distribution anomalies (e.g., order amounts suddenly all zero)

**Operational metrics:**
- Pipeline duration (total and per-stage)
- Data latency (time from source event to destination availability)
- Resource usage (memory, CPU, network I/O)

```python
# Example: Pipeline metrics collection
@dataclass
class PipelineMetrics:
    pipeline_name: str
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    records_extracted: int = 0
    records_validated: int = 0
    records_failed_validation: int = 0
    records_loaded: int = 0
    records_sent_to_dlq: int = 0

    def summary(self) -> dict:
        duration = (self.end_time - self.start_time).total_seconds()
        return {
            "pipeline": self.pipeline_name,
            "run_id": self.run_id,
            "duration_seconds": duration,
            "extracted": self.records_extracted,
            "loaded": self.records_loaded,
            "failed": self.records_failed_validation,
            "dlq": self.records_sent_to_dlq,
            "success_rate": self.records_loaded / max(self.records_extracted, 1),
        }
```

### Step 7: Make Pipeline Idempotent

**Non-negotiable requirement: re-running a pipeline must produce the same
result as running it once.** This means:

- **Upserts, not inserts**: Use `INSERT ... ON CONFLICT UPDATE` or MERGE
  statements so duplicate runs do not create duplicate records
- **Partition replacement**: Overwrite entire partitions atomically so
  re-running replaces rather than appends
- **Deterministic transforms**: Same input must always produce same output;
  avoid non-deterministic functions (random, current_timestamp) in transforms
- **Watermark management**: Store watermarks in a separate state table; update
  only after successful load

```python
# Example: Idempotent upsert
def load_users(db_session, users: list[dict]):
    """Idempotent load — safe to re-run."""
    for user in users:
        db_session.execute(
            text("""
                INSERT INTO users (id, name, email, updated_at)
                VALUES (:id, :name, :email, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    updated_at = EXCLUDED.updated_at
            """),
            user,
        )
    db_session.commit()
```

### Step 8: Add Checkpointing for Long-Running Pipelines

For pipelines that process large volumes or run for extended periods:

- **Save progress at regular intervals**: After every N records or every M
  minutes, persist the current position (offset, page number, watermark)
- **Resume from checkpoint on failure**: When restarting after a crash, read
  the last checkpoint and continue from there instead of starting over
- **Checkpoint storage**: Use a durable store (database table, S3 file) that
  survives process restarts

```python
class Checkpoint:
    def __init__(self, pipeline_name: str, storage_path: str):
        self.pipeline_name = pipeline_name
        self.storage_path = storage_path

    def save(self, state: dict):
        """Persist checkpoint state."""
        checkpoint_file = f"{self.storage_path}/{self.pipeline_name}.json"
        with open(checkpoint_file, "w") as f:
            json.dump({
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
            }, f)

    def load(self) -> Optional[dict]:
        """Load last checkpoint, or None if no checkpoint exists."""
        checkpoint_file = f"{self.storage_path}/{self.pipeline_name}.json"
        try:
            with open(checkpoint_file) as f:
                return json.load(f)["state"]
        except FileNotFoundError:
            return None

# Usage
checkpoint = Checkpoint("orders_pipeline", "/var/checkpoints")
last_state = checkpoint.load()
start_offset = last_state["offset"] if last_state else 0

for i, batch in enumerate(extract_batches(start_offset=start_offset)):
    transformed = transform(batch)
    load(transformed)
    checkpoint.save({"offset": start_offset + (i + 1) * BATCH_SIZE})
```

### Step 9: Write Tests

Create comprehensive tests for the pipeline:

**Unit tests for transforms:**
```python
def test_transform_converts_currency():
    raw = pd.DataFrame({"amount": [100.0], "currency": ["EUR"]})
    result = transform_orders(raw)
    assert "amount_usd" in result.columns
    assert result["amount_usd"].iloc[0] > 0

def test_transform_rejects_negative_amounts():
    raw = pd.DataFrame({"amount": [-50.0], "currency": ["USD"]})
    with pytest.raises(pa.errors.SchemaError):
        transform_orders(raw)

def test_transform_handles_nulls():
    raw = pd.DataFrame({"amount": [None], "currency": ["USD"]})
    with pytest.raises(pa.errors.SchemaError):
        transform_orders(raw)
```

**Integration tests for full pipeline:**
```python
def test_full_pipeline_end_to_end(test_db, sample_source_data):
    """Run full pipeline with sample data and verify output."""
    # Seed source
    insert_source_data(test_db, sample_source_data)

    # Run pipeline
    result = run_pipeline(source_db=test_db, target_db=test_db)

    # Verify
    assert result.metrics.records_extracted == len(sample_source_data)
    assert result.metrics.records_loaded == len(sample_source_data)
    assert result.metrics.records_sent_to_dlq == 0

    # Verify output data
    loaded = read_target_table(test_db, "orders_curated")
    assert len(loaded) == len(sample_source_data)
    assert loaded["amount_usd"].notna().all()
```

**Idempotency tests:**
```python
def test_pipeline_is_idempotent(test_db, sample_source_data):
    """Running pipeline twice produces same result as running once."""
    insert_source_data(test_db, sample_source_data)

    run_pipeline(source_db=test_db, target_db=test_db)
    first_run = read_target_table(test_db, "orders_curated")

    run_pipeline(source_db=test_db, target_db=test_db)
    second_run = read_target_table(test_db, "orders_curated")

    pd.testing.assert_frame_equal(first_run, second_run)
```

### Step 10: Verify with Sample Data

Run the pipeline end-to-end with representative sample data:

1. Prepare sample data that covers:
   - Normal records (happy path)
   - Edge cases (nulls, empty strings, boundary values)
   - Invalid records (to verify DLQ behavior)
   - Duplicates (to verify idempotency)
2. Run the pipeline
3. Inspect output:
   - Row counts match expectations
   - Data types are correct
   - Values are transformed as expected
   - Invalid records are in the DLQ with correct error messages
   - Metrics are accurate
4. Run the pipeline a second time (idempotency check):
   - No duplicate records in destination
   - Metrics are consistent

### Step 11: Document the Pipeline

Create documentation that enables others to operate and maintain the pipeline:

1. **Data lineage**: Source-to-destination mapping showing which source
   fields map to which destination fields, and what transformations are applied
2. **Schema documentation**: Input schema, output schema, intermediate schemas
   with data types, constraints, and descriptions for each field
3. **Schedule**: When the pipeline runs (cron expression or trigger), expected
   duration, and SLA
4. **Runbook**: Operational procedures for common scenarios:
   - How to manually trigger a run
   - How to reprocess a specific date range
   - How to investigate and resolve DLQ records
   - How to handle schema changes in the source
   - How to scale the pipeline for increased volume
   - Contact information for source system owners
5. **Monitoring dashboard**: Where to find pipeline metrics, what thresholds
   trigger alerts, and escalation procedures

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during data pipeline design MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during data pipeline design MUST follow this format:
- **Signed commits**: Always use `git commit -S`
- **Semantic prefix**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `ci:`
- **File-change table** in the commit body:
  ```
  type: concise description

  | File (Location) | Summary of Change |
  |---|---|
  | path/to/file.py | What changed in this file |

  Author: PrabhukumarSivamoorthy@gmail.com
  ```
- See CLAUDE.md [GIT] for full specification.

## Checklist Before Completion

- [ ] Requirements documented (sources, destinations, volume, SLAs)
- [ ] Pipeline pattern chosen and justified (ETL / ELT / streaming)
- [ ] Extract stage handles incremental loading and rate limits
- [ ] Transform stage validates data with schema enforcement
- [ ] Load stage uses upserts or atomic partition replacement
- [ ] Error handling: DLQ, retries, and alerting are in place
- [ ] Monitoring: row counts, quality metrics, and latency tracking
- [ ] Pipeline is idempotent (re-run produces same result)
- [ ] Checkpointing implemented for long-running pipelines
- [ ] Unit tests for transforms, integration tests for full pipeline
- [ ] Verified with sample data covering happy path, edge cases, and errors
- [ ] Documentation: lineage, schema, schedule, and runbook
- [ ] Consistent with CLAUDE.md [DATA-ML] section patterns
