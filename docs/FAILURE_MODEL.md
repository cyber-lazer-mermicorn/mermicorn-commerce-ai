# Failure Model

## Failure Modes

| Mode | Detection | Containment | Recovery |
|------|-----------|-------------|----------|
| Invalid input | Validation | Reject | Return error |
| Empty state | Check | Default | Initialize |
| Export failure | Try-except | Log | Retry |
| Missing dependency | Import error | Inform | Install |

## Recovery Strategies

1. **Graceful degradation** — Continue with defaults
2. **Error propagation** — Return structured error
3. **State recovery** — Reset to last valid state

## Blast Radius

- **Single operation**: Isolated failure, no cascade
- **Export**: File not written, data preserved
- **Import**: Module not loaded, feature unavailable

## Observability

| Metric | Source | Purpose |
|--------|--------|---------|
| Operation count | Engine stats | Usage tracking |
| Error rate | Logs | Health monitoring |
| Export success | Return values | Data integrity |
