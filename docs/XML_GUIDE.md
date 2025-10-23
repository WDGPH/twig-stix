# XML Guide

This document provides a concise overview of XML files. Created to help understand how to develop, validate, and check STIX files, this document is a reference guide of knowledge learned along the way.

## 1. What is XML

- XML = eXtensible Markup Language
- Markup language that is used to store and transport data in a structured, readable format for humans and machines [1]
- XML follows established standards so machine-to-machine interactions can be streamlined, allowing data sharing between different applications (i.e. enabling interoperability) [1]
- XML is self-descriptive. This means that the structure of the data is defined by the tags that describe the content.

For example: 

```xml
<Student>
  <FirstName>Jane</FirstName>
  <LastName>Doe</LastName>
  <Grade>6</Grade>
</Student>
```

## 2. XML Schema Definitions (XSD)

- XML Schema Definitions (XSD) define the structure, content, constraints, and semantics of XML documents. 
- XSD is standardized by the World Wide Web Consortium (W3C), thereby being a global industry standard for XML documents.
- More information on XML structure, as articulated by XSD can be found in [2].
- XSD ensures all XML files follow consistent data formats, making automated validation possible. 

For example: 

```xml
<xs:element name="Student">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="FirstName" type="xs:string"/>
      <xs:element name="LastName" type="xs:string"/>
      <xs:element name="Grade" type="xs:integer"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

## 3. How Schemas are Referenced 

- XML schemas exist openly. XML files therefore often include a reference to their schema using an attribute such as `xsi:noNameSpaceSchemaLocation`
- This tells validation tools which XSD file to use when checking structure and types.
- The path can be relative or absolute. 
- In STIX workflows, we don't have access to reference schemas. However, we would still like to be able to validate the data. We can therefore pull the schema from the attributes and tags, creating a relative schema, and storing it locally.

## 4. Fetching Schemas

Schemas can be: 

- Stored locally (e.g., within a repository like `twig-stix/schemas/`)
- Fetched dynamically (e.g., from an API or endpoint)

## 5. Generating Mock Data

Mocking up XML data is useful for testing validation pipelines or demonstrating schema compliance. 

Exmaple: 

```python
import xmlschema

schema = xmlschema.XMLSchema("SchoolUpload_v1.0.xsd")
example_xml = schema.encode({
  'School': {'Name': 'Maple Public School', 'BoardNumber': '1234'}
})
print(example_xml)
```

## 6. Validation 

Validation ensures the XML: 

- Conforms to its schema (structural validation)
- Contains valid data values (semantic validation)
- Is complete (all required elements are present)

## 7. Links and References 

[1] https://www.codecademy.com/resources/blog/what-is-xml-used-for
[2] https://www.liquid-technologies.com/Reference/Glossary/XML_Overview.html

- Namespaces in XML 1.0 (Third Edition) W3C: https://www.w3.org/TR/REC-xml-names/#dt-prefix
- Overview of XML documents: https://www.liquid-technologies.com/Reference/Glossary/XML_Overview.html
