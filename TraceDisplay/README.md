# TraceDisplay

```
# Record something.
trace-cmd record -o trace.dat -e sched echo Hello World

# Convert trace.dat into trace.h5
Trace_to_DataFrames.py trace.h5 trace.dat

# Build image.h5

# Render image.png
```

```
# Load one or more trace
t = Trace()
t.load('trace.dat')

# Filter events to put in the image.
# Chose a shape for events.
i = Image()
i.build(t)

# Apply colors to sets of shape.
ci = ColoredImage()
ci.build(i)

# Output to png, html
r = Renderer()
r.render(ci)
```
