# M11 Export

## ResearchStudy

### id
What should this be being set to? Currently setting to sponsor identifier plus "-ResearchStudy"

### meta
Fixed and set to
```
{
    "profile": [
        "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/m11-research-study-profile"
    ]
}
```

### text
What is this all about?

### identifiers
Set to list of available study identidiers

The following parameters look "interesting":
- "use"
- "type"
- "system"

### version
Setting to USDM version

### title
Set to offical title

### label
Study titles acronym and short title

### date
Using approval date

### status
Document status, hard coded to first document 

### phase
Code system set to thresarus owl file?
We also have to take into account xM11 preferred terms 

### focus

TBD

### condition

TBD

### extensions

#### 

#### confidentiality 

```
{
    "url": "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
    "valueString": "All data is confidential"
}
```






