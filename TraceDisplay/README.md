# TraceDisplay

TraceDisplay is a visualization tool for trace-cmd records.
The trace-cmd records are converted into a collection of pandas DataFrame to ease manipulation.
Rules are then specified and applied to describe how to draw and color shapes from the data.
The default rules are the following:
For each event a small vertical segment is drawn at `(x0,y0)` where `x0` is the timestamp at which the event occured and `y0` the cpu on with the event was recorded.
Each segment are then colored according to the type of the event.

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
