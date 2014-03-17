CodeGen
=======

Python library to generate C/C++/C# code


# Parsing data

This chapter tells how to get input data to the library.

## Excel sheet

```
import xml.etree.ElementTree as ET

tree = ET.parse('excel_sheet.xml')
root = tree.getroot()
for r in root.iter("{urn:schemas-microsoft-com:office:spreadsheet}Row"):
    data = []
    for c in r.getchildren():
        data.append(c.getchildren()[0].text)
    print data
```

## UML model (xmi)


## Source code (doxygen xml format)

