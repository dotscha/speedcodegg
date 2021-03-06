# Speedcode Generator Generator for mortals

The aim or this project is to create a tool that aids the process of writing [speedcode](http://codebase64.org/doku.php?id=base:speedcode) generators for the MOS 6502 processor family. Most of us do prototypes using macros in assemblers or generate code by other programs (or both), but that's not production ready code. The [real thing](http://codebase64.org/doku.php?id=base:speedcode#runtime_code_generators) is to generate the same code in memory with machine code. This can be a very boring or sometimes very complex task especially if the code is highly optimized.

The basic idea is that two PRG files (binary files), one for the speedcode and one that contains a list of 
typical code snippets should be enough to parse the speedcode, extract data and generate a speedcode generator 
that can reconstruct the exact same speedcode based on that data. Different parts of the data can be directed 
into different streams and those streams can be replaced by generators if needed, like consecutive numbers can 
be generated instead of storing as data.
