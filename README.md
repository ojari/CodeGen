# CodeGen

CodeGen is a Python library for programmatically generating source code in various languages, including C, C++, C#, and Java. It provides an object-oriented API to construct code elements like classes, methods, and variables, which can then be rendered into source files.

This library is particularly useful for:
- Generating boilerplate code from a data model.
- Creating cross-language implementations from a single source.
- Automating the creation of data transfer objects (DTOs), hardware abstraction layers (HALs), or other repetitive code structures.

## Core Concepts

The library is built around a set of classes (e.g., `OClass`, `OMethod`) that represent different parts of a program. You create instances of these classes and assemble them to define your desired code structure. The `OFile` class manages the final output to a file, adapting the syntax based on the file extension.

### Modifiers

Code elements like classes, methods, and arguments can be assigned modifiers. These are string constants that control visibility and behavior.

- **Visibility**: `PUBLIC`, `PRIVATE`, `PROTECTED`
- **Behavior**: `STATIC`, `CONST`, `FINAL`, `OVERRIDE`
- **Special**: `GETTER`, `SETTER` (for automatic property generation), `TEST` (for test classes/methods), `DBVAR`, `EXTERNAL`

## File Generation

### `OFile(fname, namespace="")`

The `OFile` class is the main entry point for creating a source file.

- `fname`: The name of the file to be generated (e.g., `"myclass.cpp"`). The file extension determines the output language.
- `namespace`: (Optional) The namespace for the code (used in C# and C++).

You can write raw strings or `OBase` objects to the file using the left-shift `<<` operator. The class automatically handles indentation.

```python
f = OFile("config.h")
f << "#define VERSION 1.0"
f.close()
```

### Writer Functions

Several helper functions simplify the process of writing complete classes to files:

- `write_file_cs(classes, fname, namespace, includes=[])`: Writes a list of classes to a single C# file.
- `write_file_c(class_obj, path, cincludes, hincludes)`: Writes a class to a pair of `.c` and `.h` files.
- `write_file_cpp(class_obj, path)`: Writes a class to a pair of `.cpp` and `.hpp` files.

## Code Generation Classes

The following classes are used to build the code structure.

### `OClass(name, mods={PUBLIC})`

Represents a class definition. You can add members (methods, arguments) to it using the `<<` operator.

```python
my_class = OClass("MyClass")
my_class << OMethod("myMethod", "void")
```

### `OMethod(name, ctype, args=[], mods={PUBLIC})`

Represents a method or function.

- `name`: The method name.
- `ctype`: The return type.
- `args`: A list of `OArg` objects for the parameters.
- `mods`: A set of modifiers (e.g., `{PUBLIC, STATIC}`).

Method body code can be added as a list of strings.

```python
# void sayHello(const char* name) { ... }
method = OMethod("sayHello", "void", [OArg("name", "const char*")])
method << 'printf("Hello, %s\\n", name);'
```

### `OArg(name, ctype, mods={PRIVATE}, initial=None)`

Represents a variable, class member, or function argument.

- `name`: The variable name.
- `ctype`: The variable type.
- `initial`: An optional initial value.

### `OEnum(name, mods={PUBLIC}, items=[])`

Represents an enumeration.

```python
# enum Color { RED, GREEN, BLUE };
color_enum = OEnum("Color", items=["RED", "GREEN", "BLUE"])
```

### `OStruct(name, mods={PUBLIC})`

Represents a C-style struct.

```python
# typedef struct { int x; int y; } Point_t;
point_struct = OStruct("Point")
point_struct << OArg("x", "int")
point_struct << OArg("y", "int")
```

## Example: Generating a C++ Class

This example demonstrates how to generate a simple C++ class with a header and source file.

```python
from codegen import *

# Define the class structure
user_class = OClass("User")
user_class.implements = ["IComparable"] # For C# or Java

# Add member variables
user_class << OArg("name", "string", {PRIVATE, GETTER, SETTER})
user_class << OArg("userId", "int", {PRIVATE, GETTER})

# Add a constructor
constructor = OMethod("User", "", [OArg("name", "string"), OArg("id", "int")])
constructor << "this->name = name;"
constructor << "this->userId = id;"
user_class << constructor

# Add a method
method = OMethod("print", "void", mods={PUBLIC, CONST})
method << 'cout << "User ID: " << userId << ", Name: " << name << endl;'
user_class << method

# Write to .hpp and .cpp files
write_file_cpp(user_class, "./output/")
```

This will generate `output/User.hpp` and `output/User.cpp` with the corresponding class definition, member implementations, and getter/setter methods.

