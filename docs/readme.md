# FHIR Processing

## M11 to FHIR M11 Message

### FHIR Mapping Background Information

| String | Substitute | Purpose |
| :----- | :----- | :----- |
| $FHIR | http://hl7.org/fhir | General URL for FHIR elements |
| $EBM | http://hl7.org/fhir/uv/ebm | General URL for EBM IG |
| $EBM_SD | http://hl7.org/fhir/uv/ebm/StructureDefinition | General URL for EBM IG extensions and profiles |
| $EBM_Conf | http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement | EBM Sponsor  Confidentiality Statement |
        
| String | Substitute | Purpose |
| :----- | :----- | :----- |
| $UDP | http://hl7.org/fhir/uv/pharmaceutical-research-protocol | General URL for UDP IG |
| $ext-amd | http://hl7.org/fhir/uv/pharmaceutical-research-protocolStructureDefinition/protocol-amendment | The Protocol-Amendment extension |
| $ext-m11 | http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/m11-research-study | The M11 Research Study extension |
| $ext-nar | http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/narrative-elements | The Narrative Elelement extension |
| $ext-scope | http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/scopeImpact | The Amendment Scope extension
        

| String | Substitute | Purpose |
| :----- | :----- | :----- |
| $NCIT | http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl | System URL for NCI codes |
| $mime | https://example.org/mime | Terminolofy URL for MIME codes (used here for signature format)  |
        
        
| String | Substitute | Purpose |
| :----- | :----- | :----- |
| $SpID | https://example.org/sponsor-identifier | System URL for a sponsor identifier system |
| $AmdD | https://example.org/amendment-identifier | System URL for a sponsor's amendment identifier system |
| $AmdSite | https://example.org/site-identifier | System URL for a sponsor's site identifier system |

## Notes

### Research Study
- id: What should this be being set to? Currently setting to sponsor identifier plus "-ResearchStudy"
- status: Document status, hard coded to first document 
- phase: Code system set to thresarus owl file?

#### Composition Narratives

```
{
    "url": "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/narrative-elements",
    "valueReference": {
        "reference": "Composition/IGBJ-Narrative-2.1"
    }
}
```

### Merged File Status

| Value | Meaning |
| :---- | :---- |
| Full | Fully implemented |
| Extra | Using the extra file to circumnvigate some issue or other, see the notes field |
| Other | Something else is going on 






