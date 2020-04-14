```
# Load trace.dat and store it as a graph
./Trace_to_Graph.py graph.pkl trace.dat
# See Graph.py:
# * Nodes are events
# * Edges are per_pid, per_cpu, per_switch etc..

# Upload graph to a neo4j database
./Uplaod_Graph.py graph.pkl HOST:PORT

# Query the database to find pattern of events
# See examples/graph/*.cql
```
