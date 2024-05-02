### svgstate.py

A script to export multiple SVGs for each object group at a specified depth in
the object tree from a single template SVG while maintaining canvas properties
of the template and persisting parents of the states as needed, specifically
compatible with Inkscape SVGs.

This is useful for creating simplistic image-overlay based SCADA and similar 
state diagrams where you desire to have overlapping elements, one for each 
state the object can be in.

For example, consider a SVG structured like this:
```
example.svg
    light-switch
        on
        off
    coffee-pot
        full
        brewing
        empty
```

I can invoke this script like so, noting that `-d 2` specifies the depth 
relative to the SVG root level. This means I want all groups at depth 2 to be 
considered states. Review all options and usage with `-h`.

```
$ python svgstate.py -d 2 example.svg some-folder/ 
```

Each state, `on`, `off`, `full`, `empty`, etc. will be individually exported to 
a new SVG file in the output directory, in this case `some-folder/` keeping the 
same canvas properties (size) as the input SVG and parent objects (pruned).

If all the SVG objects have the `inkscape:label` defined, these will be 
collected top-down (excluding the SVG root), concatenated with `-`, and finally 
combined with the label of the state group itself. Continuing with the example 
above, `example.svg > coffee-pot > brewing` would be saved as 
`coffee-pot-brewing.svg`.

If the parent objects to the state group have labels, but a state group does 
not, the state group will be named with a sequence suffix unique to its position 
under its immedate parent, starting at 1. For example, if `on` did not have a 
label defined, it would be named `light-switch-1.svg`.

In all other cases, the export will be named only with a sequence unique to the 
entire input file, starting at 1, meaning each state would have its own 
identifier (`1.svg`, `2.svg`, `3.svg`, etc.).

Multiple SVG objects in the same input file is supported.
Any extra data surrounding the SVG objects is ignored.

### export_all.py

A complementary script to bulk export an entire directory of SVGs into another 
format in parallel. Calls `inkscape`, so you must have it on your PATH or 
specify using `-I`. Review all options and usage with `-h`.

```
$ python export_all.py some-folder/
```

By default, it will export `png` images in the same directory as the source SVG.

Note that Inkscape seems to not save the exported files to a known location if 
the working directory is not the same as the directory of the source SVG.
