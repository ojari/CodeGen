# CodeGen

CodeGen is a Python library for programmatically generating source code in various languages. It provides an object-oriented API to construct code elements like classes, methods, and variables, which can then be rendered into source files.

This library is particularly useful for:
- Generating boilerplate code from a data model.
- Creating cross-language implementations from a single source.
- Automating the creation of data transfer objects (DTOs), hardware abstraction layers (HALs), or other repetitive code structures.

## Core Concepts

The library is built around two main components:

1.  **Code Model**: A set of classes (e.g., `OClass`, `OMethod`, `OArg`) that represent the abstract structure of the code you want to generate. You create instances of these classes and assemble them into a tree that represents your program's structure.
2.  **Code Generators**: A collection of "visitor" classes (e.g., `CGenerator`, `CSGenerator`) that traverse the code model and translate it into source code for a specific language.

This design separates the code's structure from its implementation in a particular language, making it easy to add support for new languages without changing the core model.

### Modifiers

Code elements like classes, methods, and arguments can be assigned modifiers to control their behavior and visibility. These are defined in the `py2code.codegen.Mod` enum, which is a `Flag` enum, allowing for combinations.

- **Visibility**: `Mod.PUBLIC`, `Mod.PRIVATE`, `Mod.PROTECTED`
- **Behavior**: `Mod.STATIC`, `Mod.CONST`, `Mod.FINAL`, `Mod.OVERRIDE`
- **Special**: `Mod.GETTER`, `Mod.SETTER` (for automatic property generation), `Mod.TEST` (for test classes/methods), `Mod.DBVAR`, `Mod.EXTERNAL`, `Mod.REMEMBER`.

Example:
```python
from py2code.codegen import OMethod, Mod

# A public static method
method = OMethod("myMethod", "void", mods={Mod.PUBLIC, Mod.STATIC})
```

## Code Generation

### Generators

Code generation is handled by `CodeGenerator` subclasses. Each generator is responsible for producing syntax for a specific language.

The available generators are located in `py2code.generator`:
- `CSGenerator`: For C#
- `CGenerator`: For C source files
- `HGenerator`: For C header files
- `CPPGenerator`: For C++ source files
- `HPPGenerator`: For C++ header files

### File Output

The `OFile` class and the `write_file` helper function manage the file output.

#### `write_file(code_object, filename, generator, includes=[])`

This is the primary function for generating a file.

- `code_object`: The top-level `OClass` or list of objects to generate.
- `filename`: The path to the output file.
- `generator`: An instance of a `CodeGenerator` subclass (e.g., `CSGenerator()`).
- `includes`: A list of headers or namespaces to include.

### `OFile(fname, generator, namespace="")`

You can also use `OFile` directly for more control.

- `fname`: The name of the file to be generated.
- `generator`: An instance of a `CodeGenerator`.
- `namespace`: (Optional) The namespace for the code.

You can write raw strings or `OBase` objects to the file using the left-shift `<<` operator.

```python
from py2code.codegen import OFile
from py2code.generator import HGenerator

f = OFile("config.h", HGenerator())
f << "#define VERSION 1.0"
f.close()
```

## Code Model Classes

The following classes are used to build the code structure.

### `OClass(name, mods={Mod.PUBLIC})`

Represents a class definition. You can add members (methods, arguments) to it using the `<<` operator.

```python
my_class = OClass("MyClass")
my_class << OMethod("myMethod", "void")
```

### `OMethod(name, ctype, args=[], mods={Mod.PUBLIC})`

Represents a method or function.

- `name`: The method name.
- `ctype`: The return type.
- `args`: A list of `OArg` objects for the parameters.
- `mods`: A set of `Mod` enum members (e.g., `{Mod.PUBLIC, Mod.STATIC}`).

Method body code can be added as a list of strings.

```python
# void sayHello(const char* name) { ... }
method = OMethod("sayHello", "void", [OArg("name", "const char*")])
method << 'printf("Hello, %s\\n", name);'
```

### `OArg(name, ctype, mods={Mod.PRIVATE}, initial=None)`

Represents a variable, class member, or function argument.

- `name`: The variable name.
- `ctype`: The variable type.
- `initial`: An optional initial value.

### `OEnum(name, mods={Mod.PUBLIC}, items=[])`

Represents an enumeration.

```python
# enum Color { RED, GREEN, BLUE };
color_enum = OEnum("Color", items=["RED", "GREEN", "BLUE"])
```

### `OStruct(name, mods={Mod.PUBLIC})`

Represents a C-style struct.

```python
# typedef struct { int x; int y; } Point_t;
point_struct = OStruct("Point")
point_struct << OArg("x", "int")
point_struct << OArg("y", "int")
```

## Example: Generating a C++ Class

This example demonstrates how to generate a simple C++ class with a header and source file using the new generator system.

```python
from py2code.codegen import OClass, OMethod, OArg, Mod, write_file
from py2code.generator import HPPGenerator, CPPGenerator

# Define the class structure
user_class = OClass("User")
user_class.implements = ["IComparable"] # For C# or Java

# Add member variables with private visibility and public getters/setters
user_class << OArg("name", "string", {Mod.PRIVATE, Mod.GETTER, Mod.SETTER})
user_class << OArg("userId", "int", {Mod.PRIVATE, Mod.GETTER})

# Add a constructor
constructor = OMethod("User", "", [OArg("name", "string"), OArg("id", "int")])
constructor << "this->name = name;"
constructor << "this->userId = id;"
user_class << constructor

# Add a method
method = OMethod("print", "void", mods={Mod.PUBLIC, Mod.CONST})
method << 'cout << "User ID: " << userId << ", Name: " << name << endl;'
user_class << method

# Write to .hpp and .cpp files
write_file(user_class, "./output/User.hpp", HPPGenerator(), includes=["<string>", "<iostream>"])
write_file(user_class, "./output/User.cpp", CPPGenerator(), includes=['"User.hpp"'])
```

This will generate `output/User.hpp` and `output/User.cpp` with the corresponding class definition, member implementations, and getter/setter methods.

