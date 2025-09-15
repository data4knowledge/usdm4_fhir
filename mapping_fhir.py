#!/usr/bin/env python3
"""
FHIR Mapping Excel to YAML Converter

This program reads the FHIRMapping.xlsx file and converts it to a YAML file
with the structure keyed by "Short Name" column and containing data from
columns E through I inclusive.
"""

import pandas as pd
import yaml
from pathlib import Path
import sys


def read_excel_data(excel_path):
    """
    Read the Excel file and return the data as a pandas DataFrame.
    
    Args:
        excel_path (str): Path to the Excel file
        
    Returns:
        pandas.DataFrame: The Excel data
    """
    try:
        # Read the Excel file - it has a single sheet named "FHIR"
        df = pd.read_excel(excel_path, sheet_name="FHIR")
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)


def process_data(df):
    """
    Process the DataFrame to create the YAML structure.
    
    Args:
        df (pandas.DataFrame): The Excel data
        
    Returns:
        dict: Dictionary ready for YAML conversion
    """
    yaml_data = {}
    
    # Get column names for reference
    columns = df.columns.tolist()
    print(f"Columns found: {columns}")
    
    # Map column indices (assuming standard Excel column order)
    # Column D (index 3): Short Name - this will be our key
    # Column E (index 4): Resource - check if empty to skip row
    # Columns E-I (indices 4-8): Resource, Sample XML, Example Value(s), Binding (strength), Comment
    
    short_name_col = columns[3]  # Column D: Short Name
    resource_col = columns[4]    # Column E: Resource
    sample_xml_col = columns[5]  # Column F: Sample XML
    example_values_col = columns[6]  # Column G: Example Value(s)
    binding_col = columns[7]     # Column H: Binding (strength)
    comment_col = columns[8]     # Column I: Comment
    
    for index, row in df.iterrows():
        # Skip rows where Resource column is empty
        if pd.isna(row[resource_col]) or str(row[resource_col]).strip() == "":
            continue
            
        # Get the Short Name as the key
        short_name = row[short_name_col]
        if pd.isna(short_name) or str(short_name).strip() == "":
            continue
            
        short_name = str(short_name).strip()
        
        # Create the data dictionary for columns E through I
        entry_data = {}
        
        # Column E: Resource
        if not pd.isna(row[resource_col]):
            entry_data['Resource'] = str(row[resource_col]).strip()
            
        # Column F: Sample XML - preserve formatting
        if not pd.isna(row[sample_xml_col]):
            sample_xml = str(row[sample_xml_col]).strip()
            # Preserve the XML formatting by using literal scalar style
            entry_data['Sample XML'] = sample_xml
            
        # Column G: Example Value(s)
        if not pd.isna(row[example_values_col]):
            entry_data['Example Value(s)'] = str(row[example_values_col]).strip()
            
        # Column H: Binding (strength)
        if not pd.isna(row[binding_col]):
            entry_data['Binding (strength)'] = str(row[binding_col]).strip()
            
        # Column I: Comment
        if not pd.isna(row[comment_col]):
            entry_data['Comment'] = str(row[comment_col]).strip()
        
        # Add to yaml_data with Short Name as key
        yaml_data[short_name] = entry_data
    
    return yaml_data


def write_yaml_file(data, output_path):
    """
    Write the data to a YAML file.
    
    Args:
        data (dict): The data to write
        output_path (str): Path to the output YAML file
    """
    try:
        # Ensure the mapping directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write YAML file with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, 
                     default_flow_style=False,
                     allow_unicode=True,
                     sort_keys=False,
                     width=120,
                     default_style='|' if any('Sample XML' in str(v) for v in data.values()) else None)
        
        print(f"YAML file successfully written to: {output_path}")
        print(f"Total entries processed: {len(data)}")
        
    except Exception as e:
        print(f"Error writing YAML file: {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate the conversion process."""
    
    # Define file paths
    excel_file = "docs/FHIRMapping.xlsx"
    yaml_file = "mapping/fhir.yaml"
    
    print("FHIR Mapping Excel to YAML Converter")
    print("=" * 40)
    
    # Check if Excel file exists
    if not Path(excel_file).exists():
        print(f"Error: Excel file not found at {excel_file}")
        sys.exit(1)
    
    print(f"Reading Excel file: {excel_file}")
    
    # Read the Excel data
    df = read_excel_data(excel_file)
    print(f"Loaded {len(df)} rows from Excel file")
    
    # Process the data
    print("Processing data...")
    yaml_data = process_data(df)
    
    # Write the YAML file
    print(f"Writing YAML file: {yaml_file}")
    write_yaml_file(yaml_data, yaml_file)
    
    print("Conversion completed successfully!")


if __name__ == "__main__":
    main()
