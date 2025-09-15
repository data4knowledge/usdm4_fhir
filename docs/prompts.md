Write a small program in python to read the spreadsheet "docs/FHIRMapping.xlsx" and the single sheet within it.
- Turn the data in the sheet into a single YAML file
- Save the YAML file in the "mapping" directory called "fhir.yaml"
- The excel sheet has a single row holding column headers
- Rows where the "Resource" column is empty can be ignored
The YAML file should be structured as follows:
- Keyed by the "Short Name" column
- Contain all the data from columns E thru I inclusive (a dictionary)
- Column F contains sample XML so needs to be formatted correctly as per the spreadsheet
Place the program in a file called fhir_mapping.py in the top level directory

-----+-----

Write a small program that merges three files:

Takes "mapping/m11.json" as the master file

Reads mapping/usdm.yaml and matches to the M11 data on the main, top level key
- When a match is found the data from "mapping/usdm.yaml" is added to the m11 entry under a top-level key "usdm"

Reads mapping/fhir.yaml and matches to the M11 data on the main, top level key
- When a match is found the data from "mapping/fhir.yaml" is added to the m11 entry under a top-level key "fhir"

Save the resulting merged data as "merged.yaml" in the "mapping" directory

-----+-----

Write a small python program that takes the "mapping/merged.yaml" file and creates a set of local ".html" files that allows me to naviagte the data using a local browser.
- Main html file should be called "index.html"
- All other html pages can be held in sub directories, one for each section of the M11 document or a data element
    - Sections of the M11 document are held in the template.section_title field
    - Date elements are defined by the main key in the data
Each section of the document should display the set data elements contained within the section
Each data element should display all of the information available under the keys "template", "technical", "usdm" and "fhir" each as a panel
Use bootstrap 5 to style the web pages using the theme from https://bootswatch.com/yeti/
Store all the output in a top level directory called "html"
Store the program in a top level file called "mapping_html.py"


 