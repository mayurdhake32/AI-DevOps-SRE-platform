# Elasticsearch Troubleshooting

## Cluster Health Red

### Diagnosis
```bash
curl -X GET "localhost:9200/_cluster/health"
curl -X GET "localhost:9200/_cluster/allocation/explain"
```

### Fixes
1. **Unassigned shards**: Check disk space on nodes
2. **Node left**: Restart missing node or reroute shards
3. **Too many shards**: Reduce index shard count

```bash
# Force allocation
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "allocate_stale_primary": {
        "index": "my-index",
        "shard": 0,
        "node": "node-1"
      }
    }
  ]
}'
```

## Search Slow

### Diagnosis
```bash
# Slow queries
GET /_nodes/hot_threads

# Query profiling
GET /my-index/_search
{
  "profile": true,
  "query": { ... }
}
```

### Fixes
1. Add appropriate mappings (avoid dynamic string mapping)
2. Use `keyword` fields for aggregations
3. Increase `index.refresh_interval` for write-heavy loads
4. Enable slow query logging

## Out of Memory

```bash
# Check heap usage
GET /_nodes/stats/jvm

# Reduce heap pressure
# 1. Decrease index buffer size
# 2. Reduce bulk request size
# 3. Add more nodes to cluster
```

## Disk Watermark

### Error
```
high disk watermark [90%] exceeded on node
```

### Fix
```bash
# Delete old indices
curl -X DELETE "localhost:9200/logstash-2026.01.*"

# Or change watermark (temporary)
curl -X PUT "localhost:9200/_cluster/settings" -d'
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.high": "95%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "97%"
  }
}'
```
