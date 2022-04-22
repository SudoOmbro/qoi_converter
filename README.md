# Quite Okay Image format converter
A pure python implementation of a QOI converter, it writes PIL Images into QOI files or Opens QOI files and loads them as PIL Images.

[Based on this specification](https://qoiformat.org/qoi-specification.pdf)

## Architecture
Very object-oriented, uses the visitor pattern.

## Why python?
This is supposed to be more of a learning project than anything actually useful, but it does remove the need for compiled binaries in some instances.
