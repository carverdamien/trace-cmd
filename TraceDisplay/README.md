# TraceDisplay

```
# Record something.
trace-cmd record -o trace.dat -e sched echo Hello World

# Convert trace.dat into trace.h5
Trace_to_DataFrames.py trace.h5 trace.dat

# Build image.h5

# Render image.png
```
