# TraceDisplay

```
# Record something.
trace-cmd record -o trace.dat -e sched echo Hello World

# Convert trace.dat into trace.h5
Trace_to_DataFrames trace.h5 trace.dat

# Build default image.i.h5
Trace_to_image image.i.h5 trace.h5

# Render image.html or image.png
Render_Image image.html image.i.h5
```
