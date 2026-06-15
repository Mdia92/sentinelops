Splunk Indexes
      |
      v
Splunk MCP Server  (primary spine)
      |
      v
+------------------+
|  Watcher Agent   |  SPL threshold scan
+--------+---------+
         |
         v
+----------------------+
| Diagnostician Agent  |  correlate logs + memory lookup
+----------+-----------+
           |
           v
+-------------------+
|  Proposer Agent   |  ranked remediation options
+---------+---------+
          |
          v
+-------------------+
|   Human Gate      |  Approve / Reject
+---------+---------+
          |
          v
+-------------------+
|  Verifier Agent   |  re-query metric -> RESOLVED / ESCALATE
+---------+---------+
          |
          v
+-------------------+
|  ChromaDB Memory  |  compound across sessions
+-------------------+
