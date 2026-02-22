# Market Signals - Options Memo

## Approaches

### 1. Third-Party Rate Shopping API
- **Cost**: $500-2000/month per property depending on provider
- **Reliability**: High, dedicated infrastructure
- **Dev effort**: 2-3 weeks integration
- **Risks**: Contract lock-in, API changes

### 2. Customer-Provided CSV Upload
- **Cost**: None
- **Reliability**: Depends on customer refresh cadence
- **Dev effort**: 1 week (column mapping, validation)
- **Risks**: Stale data, format inconsistencies

### 3. Licensed/Partner Feed
- **Cost**: Negotiated per deal
- **Reliability**: Variable
- **Dev effort**: 2-4 weeks per partner
- **Risks**: Integration complexity

## Recommendation

Implement **Customer-Provided CSV** first (Option 2):
- Zero ongoing cost
- Fast to ship
- Pluggable adapter allows adding API later without engine changes
- Document refresh cadence expectations (e.g. daily)

Add third-party API adapter when customer budget allows.
