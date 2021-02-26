# PyGridWorld

PyGridWorld is a tool to manage simulation code, binaries, and configurations, as well as their outputs.

When simulating scenarios, tweaking the simulation inputs is a critical step that allows
observing how the outputs change in response. When the input to tweak is simple data,
such as numbers or text, it is not too difficult to manage, but what if the code of the
simulation itself becomes a tweakable input? Code can span many files in a nested structure,
code must be compiled, and then the binary itself must be loaded.

This project aims to manage not only the simple parameters provided to the simulation code, but the
simulation code itself. The goal is to make changing code as a parameter as painless as possible,
ideally as simple as changing a parameter from a 1 to a 2.

The project also collects, stores, and provides the outputs of the simulations in a standardized
fashion, easing the data munging process.

## Installation / Usage

The documentation for installation and usage will be provided at a future date, since the project
structure is planned to significantly change in the near future.

In the meantime, here are some images showcasing the current GUI interface.


![Simulation tab showcase](https://user-images.githubusercontent.com/5760167/109278108-c31f0580-77dd-11eb-8e46-9379afb7c89f.png)

*The simulation tab, allowing interaction with a running simulation.*


![Simulation Registry tab showcase](https://user-images.githubusercontent.com/5760167/109278410-201abb80-77de-11eb-8a68-31064e531313.png)

*The simulation registry tab, where simulation code is saved for use as an input.*

## Dependencies
+ PySide2
