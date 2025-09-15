#!/usr/bin/env python3
"""
Merge mapping files program

This program merges three mapping files:
- mapping/m11.json (master file)
- mapping/usdm.yaml 
- mapping/fhir.yaml

The result is saved as mapping/merged.yaml
"""

import json
import yaml
import os

def load_json_file(filepath):
    """Load JSON file and return data"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return None

def load_yaml_file(filepath):
    """Load YAML file and return data"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {filepath}: {e}")
        return None

def save_yaml_file(data, filepath):
    """Save data as YAML file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error: Could not save {filepath}: {e}")
        return False

def check_key_mismatches(m11_keys, usdm_keys, fhir_keys):
    """Check for key mismatches and report warnings"""
    warnings = []
    
    # Check for USDM keys not in M11
    usdm_only = set(usdm_keys) - set(m11_keys)
    if usdm_only:
        warnings.append(f"WARNING: {len(usdm_only)} USDM entries have no M11 match:")
        for key in sorted(usdm_only):
            warnings.append(f"  - {key}")
    
    # Check for FHIR keys not in M11
    fhir_only = set(fhir_keys) - set(m11_keys)
    if fhir_only:
        warnings.append(f"WARNING: {len(fhir_only)} FHIR entries have no M11 match:")
        for key in sorted(fhir_only):
            warnings.append(f"  - {key}")
    
    # Check for M11 keys with no USDM match
    m11_no_usdm = set(m11_keys) - set(usdm_keys)
    if m11_no_usdm:
        warnings.append(f"INFO: {len(m11_no_usdm)} M11 entries have no USDM mapping")
    
    # Check for M11 keys with no FHIR match
    m11_no_fhir = set(m11_keys) - set(fhir_keys)
    if m11_no_fhir:
        warnings.append(f"INFO: {len(m11_no_fhir)} M11 entries have no FHIR mapping")
    
    return warnings

def merge_mapping_files():
    """Main function to merge the mapping files"""
    print("Mapping File Merger")
    print("==================")
    
    # Load the master file (m11.json)
    print("Loading master file: mapping/m11.json")
    m11_data = load_json_file("mapping/m11.json")
    if m11_data is None:
        return False
    
    # Load the USDM mapping file
    print("Loading USDM mapping file: mapping/usdm.yaml")
    usdm_data = load_yaml_file("mapping/usdm.yaml")
    if usdm_data is None:
        return False
    
    # Load the FHIR mapping file
    print("Loading FHIR mapping file: mapping/fhir.yaml")
    fhir_data = load_yaml_file("mapping/fhir.yaml")
    if fhir_data is None:
        return False
    
    print(f"Loaded {len(m11_data)} entries from M11 master file")
    print(f"Loaded {len(usdm_data)} entries from USDM mapping file")
    print(f"Loaded {len(fhir_data)} entries from FHIR mapping file")
    
    # Check for key mismatches and display warnings
    print("\nChecking for key mismatches...")
    warnings = check_key_mismatches(m11_data.keys(), usdm_data.keys(), fhir_data.keys())
    if warnings:
        print("\nKey Mismatch Analysis:")
        print("=" * 50)
        for warning in warnings:
            print(warning)
        print("=" * 50)
    else:
        print("No key mismatches detected.")
    
    # Create merged data starting with m11 data
    merged_data = {}
    usdm_matches = 0
    fhir_matches = 0
    
    print("\nMerging data...")
    
    # Process each entry in the M11 master file
    for key, m11_entry in m11_data.items():
        # Start with the M11 data
        merged_entry = m11_entry.copy()
        
        # Check for USDM match
        if key in usdm_data:
            merged_entry["usdm"] = usdm_data[key]
            usdm_matches += 1
        
        # Check for FHIR match
        if key in fhir_data:
            merged_entry["fhir"] = fhir_data[key]
            fhir_matches += 1
        
        # Add to merged data
        merged_data[key] = merged_entry
    
    print(f"Found {usdm_matches} USDM matches")
    print(f"Found {fhir_matches} FHIR matches")
    
    # Save the merged data
    output_file = "mapping/merged.yaml"
    print(f"\nSaving merged data to: {output_file}")
    
    if save_yaml_file(merged_data, output_file):
        print(f"Successfully saved merged data to: {output_file}")
        print(f"Total merged entries: {len(merged_data)}")
        return True
    else:
        return False

if __name__ == "__main__":
    success = merge_mapping_files()
    if success:
        print("\nMerge completed successfully!")
    else:
        print("\nMerge failed!")
        exit(1)
