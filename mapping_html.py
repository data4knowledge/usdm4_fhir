#!/usr/bin/env python3
"""
Mapping HTML Generator

This program reads the merged.yaml file and creates a set of local HTML files
that allow navigation of the data using a local browser.

Features:
- Main index.html file with section navigation
- Individual pages for each section and data element
- Bootstrap 5 styling with Yeti theme
- Responsive design with collapsible panels
- Search functionality
"""

import yaml
import shutil
from pathlib import Path
from collections import defaultdict
import html


def load_merged_data():
    """Load the merged.yaml file"""
    try:
        with open("mapping/merged.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: mapping/merged.yaml not found")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in mapping/merged.yaml: {e}")
        return None


def create_html_structure():
    """Create the HTML directory structure"""
    html_dir = Path("html")

    # Remove existing directory if it exists
    if html_dir.exists():
        shutil.rmtree(html_dir)

    # Create main directory and subdirectories
    html_dir.mkdir()
    (html_dir / "sections").mkdir()
    (html_dir / "elements").mkdir()
    (html_dir / "css").mkdir()
    (html_dir / "js").mkdir()

    return html_dir


def get_base_template():
    """Get the base HTML template with Bootstrap 5 and Yeti theme"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://bootswatch.com/5/yeti/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand {{
            font-weight: bold;
        }}
        .card-header {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        .section-card {{
            margin-bottom: 1rem;
        }}
        .element-card {{
            margin-bottom: 0.5rem;
        }}
        .data-panel {{
            margin-bottom: 1rem;
        }}
        .search-box {{
            margin-bottom: 2rem;
        }}
        .breadcrumb {{
            background-color: #f8f9fa;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
        }}
        .metadata {{
            font-size: 0.9em;
            color: #6c757d;
        }}
        .xml-code {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.375rem;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .back-to-top {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{home_link}">
                <i class="fas fa-sitemap me-2"></i>FHIR Mapping Navigator
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{home_link}">
                            <i class="fas fa-home me-1"></i>Home
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {breadcrumb}
        {content}
    </div>

    <button class="btn btn-primary back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">
        <i class="fas fa-arrow-up"></i>
    </button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Search functionality
        function filterElements(searchTerm) {{
            const elements = document.querySelectorAll('.searchable');
            const term = searchTerm.toLowerCase();
            
            elements.forEach(element => {{
                const text = element.textContent.toLowerCase();
                const parent = element.closest('.card, .list-group-item');
                if (parent) {{
                    if (text.includes(term) || term === '') {{
                        parent.style.display = '';
                    }} else {{
                        parent.style.display = 'none';
                    }}
                }}
            }});
        }}

        // Show/hide back to top button
        window.addEventListener('scroll', function() {{
            const backToTop = document.querySelector('.back-to-top');
            if (window.pageYOffset > 300) {{
                backToTop.style.display = 'block';
            }} else {{
                backToTop.style.display = 'none';
            }}
        }});
    </script>
</body>
</html>"""


def escape_html(text):
    """Escape HTML characters in text"""
    if text is None:
        return ""
    return html.escape(str(text))


def format_xml(xml_text):
    """Format XML text for display"""
    if not xml_text:
        return ""

    # Basic XML formatting - replace common patterns
    formatted = str(xml_text)
    formatted = formatted.replace("<", "&lt;")
    formatted = formatted.replace(">", "&gt;")

    return formatted


def create_breadcrumb(current_page, section_title=None, element_name=None):
    """Create breadcrumb navigation"""
    breadcrumb = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
    breadcrumb += '<li class="breadcrumb-item"><a href="../index.html"><i class="fas fa-home"></i> Home</a></li>'

    if section_title:
        breadcrumb += f'<li class="breadcrumb-item"><a href="../sections/{section_title.replace(" ", "_").replace("/", "_")}.html">{escape_html(section_title)}</a></li>'

    if element_name:
        breadcrumb += f'<li class="breadcrumb-item active" aria-current="page">{escape_html(element_name)}</li>'
    elif section_title:
        breadcrumb += '<li class="breadcrumb-item active" aria-current="page">Section Overview</li>'
    else:
        breadcrumb += f'<li class="breadcrumb-item active" aria-current="page">{current_page}</li>'

    breadcrumb += "</ol></nav>"
    return breadcrumb


def create_data_panel(title, data, panel_id):
    """Create a collapsible panel for data display"""
    if not data:
        return ""

    panel_html = f'''
    <div class="card data-panel">
        <div class="card-header" data-bs-toggle="collapse" data-bs-target="#{panel_id}" style="cursor: pointer;">
            <i class="fas fa-chevron-down me-2"></i>{escape_html(title)}
        </div>
        <div id="{panel_id}" class="collapse">
            <div class="card-body">
    '''

    if isinstance(data, dict):
        for key, value in data.items():
            # Check if this specific field should be highlighted in red
            # Only highlight specific guidance/instruction fields
            is_guidance_field = key.lower() == "guidance" or "guidance" in key.lower()
            is_instruction_field = (
                key.lower() == "instruction" or "instruction" in key.lower()
            )

            # Only highlight guidance and instruction fields
            should_highlight = is_guidance_field or is_instruction_field

            text_style = 'style="color: red;"' if should_highlight else ""

            if key == "Sample XML" and value:
                panel_html += f"""
                <div class="mb-3">
                    <strong {text_style}>{escape_html(key)}:</strong>
                    <div class="xml-code" {text_style}>{format_xml(value)}</div>
                </div>
                """
            elif isinstance(value, list):
                panel_html += f'<div class="mb-2"><strong {text_style}>{escape_html(key)}:</strong></div>'
                
                # Special handling for mappings field - display as structured array with conditions
                if key.lower() == "mappings":
                    panel_html += f'<div class="ms-3" {text_style}>'
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            panel_html += f'<div class="mb-3 p-3 border rounded bg-light">'
                            panel_html += f'<h6 class="text-primary">Mapping {i+1}:</h6>'
                            for sub_key, sub_value in item.items():
                                if sub_key.lower() == "conditions" and isinstance(sub_value, list):
                                    panel_html += f'<div class="mb-2"><strong>{escape_html(sub_key)}:</strong></div>'
                                    panel_html += f'<div class="ms-2">'
                                    for j, condition in enumerate(sub_value):
                                        if isinstance(condition, dict):
                                            panel_html += f'<div class="mb-2 p-2 border rounded bg-white">'
                                            panel_html += f'<small class="text-muted">Condition {j+1}:</small>'
                                            for cond_key, cond_value in condition.items():
                                                panel_html += f'<div class="ms-2"><strong>{escape_html(cond_key)}:</strong> {escape_html(cond_value)}</div>'
                                            panel_html += '</div>'
                                        else:
                                            panel_html += f'<div class="mb-1 p-1 border rounded bg-white">{escape_html(condition)}</div>'
                                    panel_html += '</div>'
                                elif isinstance(sub_value, dict):
                                    panel_html += f'<div class="mb-2"><strong>{escape_html(sub_key)}:</strong></div>'
                                    panel_html += f'<div class="ms-2">'
                                    for dict_key, dict_value in sub_value.items():
                                        panel_html += f'<div><strong>{escape_html(dict_key)}:</strong> {escape_html(dict_value)}</div>'
                                    panel_html += '</div>'
                                else:
                                    panel_html += f'<div class="mb-1"><strong>{escape_html(sub_key)}:</strong> {escape_html(sub_value)}</div>'
                            panel_html += '</div>'
                        else:
                            panel_html += f'<div class="mb-1 p-1 border rounded bg-light">{escape_html(item)}</div>'
                    panel_html += '</div>'
                else:
                    # Default list handling for other fields
                    panel_html += f'<ul class="list-unstyled ms-3" {text_style}>'
                    for item in value:
                        if isinstance(item, dict):
                            for sub_key, sub_value in item.items():
                                panel_html += f"<li><strong>{escape_html(sub_key)}:</strong> {escape_html(sub_value)}</li>"
                        else:
                            panel_html += f"<li>{escape_html(item)}</li>"
                    panel_html += "</ul>"
            elif isinstance(value, dict):
                panel_html += f'<div class="mb-2"><strong {text_style}>{escape_html(key)}:</strong></div>'
                panel_html += f'<div class="ms-3" {text_style}>'
                for sub_key, sub_value in value.items():
                    panel_html += f"<div><strong>{escape_html(sub_key)}:</strong> {escape_html(sub_value)}</div>"
                panel_html += "</div>"
            else:
                panel_html += f'<div class="mb-2" {text_style}><strong>{escape_html(key)}:</strong> {escape_html(value)}</div>'
    else:
        panel_html += f"<div>{escape_html(data)}</div>"

    panel_html += """
            </div>
        </div>
    </div>
    """

    return panel_html


def create_index_page(data, html_dir):
    """Create the main index.html page"""
    # Group data by section
    sections = defaultdict(list)

    for element_name, element_data in data.items():
        template_data = element_data.get("template", {})
        section_title = template_data.get("section_title", "Unknown Section")
        sections[section_title].append((element_name, element_data))

    # Sort sections by section number, with Title Page first
    def get_section_sort_key(section_item):
        section_title, elements = section_item
        # Get the first element to find section number
        if elements:
            first_element = elements[0][1]  # Get element data
            template_data = first_element.get("template", {})
            section_number = template_data.get("section_number", "")

            # Title Page should come first (has blank section number)
            if section_title == "Title Page" or section_number == "":
                return (0, section_title)  # Sort first, then by title

            # Try to parse section number for proper numeric sorting
            try:
                # Handle section numbers like "1.1", "2.3.1", etc.
                parts = section_number.split(".")
                numeric_parts = [int(part) for part in parts if part.isdigit()]
                # Pad with zeros to ensure consistent sorting
                while len(numeric_parts) < 5:  # Support up to 5 levels deep
                    numeric_parts.append(0)
                return (1, tuple(numeric_parts), section_title)
            except (ValueError, AttributeError):
                # If section number can't be parsed, sort by title at the end
                return (2, section_title)

        return (2, section_title)  # Fallback for sections without elements

    sorted_sections = sorted(sections.items(), key=get_section_sort_key)

    content = """
    <div class="row">
        <div class="col-12">
            <div class="jumbotron bg-light p-5 rounded mb-4">
                <h1 class="display-4"><i class="fas fa-sitemap me-3"></i>FHIR Mapping Navigator</h1>
                <p class="lead">Navigate through M11, USDM, and FHIR mapping data organized by protocol sections.</p>
                <hr class="my-4">
                <p>This tool provides an interactive way to explore the relationships between M11 protocol elements, USDM mappings, and FHIR resources.</p>
            </div>
        </div>
    </div>

    <div class="search-box">
        <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input type="text" class="form-control" placeholder="Search sections and elements..." 
                   onkeyup="filterElements(this.value)">
        </div>
    </div>

    <div class="row">
    """

    # Statistics
    total_elements = len(data)
    total_sections = len(sections)
    usdm_mapped = sum(1 for item in data.values() if item.get("usdm"))
    fhir_mapped = sum(1 for item in data.values() if item.get("fhir"))

    content += f"""
        <div class="col-12 mb-4">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-primary">{total_sections}</h5>
                            <p class="card-text">Sections</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-success">{total_elements}</h5>
                            <p class="card-text">Data Elements</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-info">{usdm_mapped}</h5>
                            <p class="card-text">USDM Mapped</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-warning">{fhir_mapped}</h5>
                            <p class="card-text">FHIR Mapped</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """

    # Section cards
    for section_title, elements in sorted_sections:
        section_filename = section_title.replace(" ", "_").replace("/", "_")
        element_count = len(elements)
        usdm_count = sum(1 for _, elem in elements if elem.get("usdm"))
        fhir_count = sum(1 for _, elem in elements if elem.get("fhir"))

        content += f"""
        <div class="col-lg-6 col-xl-4 mb-3">
            <div class="card section-card searchable">
                <div class="card-header">
                    <h5 class="mb-0">
                        <a href="sections/{section_filename}.html" class="text-white text-decoration-none">
                            <i class="fas fa-folder me-2"></i>{escape_html(section_title)}
                        </a>
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-4">
                            <div class="text-primary">
                                <strong>{element_count}</strong><br>
                                <small>Elements</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="text-info">
                                <strong>{usdm_count}</strong><br>
                                <small>USDM</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="text-warning">
                                <strong>{fhir_count}</strong><br>
                                <small>FHIR</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    content += """
    </div>
    """

    # Create the full HTML page
    template = get_base_template()
    html_content = template.format(
        title="FHIR Mapping Navigator",
        home_link="index.html",
        breadcrumb="",
        content=content,
    )

    # Write the index.html file
    with open(html_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(
        f"Created index.html with {total_sections} sections and {total_elements} elements"
    )


def create_section_page(section_title, elements, html_dir):
    """Create a section page showing all elements in that section"""
    section_filename = section_title.replace(" ", "_").replace("/", "_")

    content = f"""
    <div class="row">
        <div class="col-12">
            <h1><i class="fas fa-folder me-3"></i>{escape_html(section_title)}</h1>
            <p class="lead">Data elements in this section: {len(elements)}</p>
        </div>
    </div>

    <div class="search-box">
        <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input type="text" class="form-control" placeholder="Search elements in this section..." 
                   onkeyup="filterElements(this.value)">
        </div>
    </div>

    <div class="row">
    """

    # Sort elements by ordinal field, fallback to name if ordinal not present
    def get_element_sort_key(element_item):
        element_name, element_data = element_item
        ordinal = element_data.get(
            "ordinal", float("inf")
        )  # Use infinity if no ordinal
        return (ordinal, element_name)  # Secondary sort by name for consistency

    sorted_elements = sorted(elements, key=get_element_sort_key)

    for element_name, element_data in sorted_elements:
        template_data = element_data.get("template", {})
        # technical_data = element_data.get("technical", {})
        usdm_data = element_data.get("usdm")
        fhir_data = element_data.get("fhir")
        status_data = element_data.get("status", {})

        # Create status badges
        badges = []
        if usdm_data:
            badges.append('<span class="badge bg-info me-1">USDM</span>')
        if fhir_data:
            badges.append('<span class="badge bg-warning me-1">FHIR</span>')

        badges_html = (
            "".join(badges)
            if badges
            else '<span class="badge bg-secondary">No Mappings</span>'
        )

        # Create status icon based on traffic light system
        status_value = status_data.get("value", "").lower()
        if status_value == "full":
            status_icon = (
                '<i class="fas fa-circle text-success me-2" title="Full Implementation"></i>'
            )
        elif status_value == "partial":
            status_icon = (
                '<i class="fas fa-circle text-warning me-2" title="Partial Implementation"></i>'
            )
        elif status_value == "none":
            status_icon = (
                '<i class="fas fa-circle text-danger me-2" title="No Implementation"></i>'
            )
        elif status_value == "extra":
            status_icon = (
                '<i class="fas fa-circle text-primary me-2" title="Extra Used"></i>'
            )
        elif status_value == "other":
            status_icon = (
                '<i class="fas fa-circle text-info me-2" title="Something Else Going On"></i>'
            )
        else:
            status_icon = (
                '<i class="fas fa-circle text-light me-2" title="No Status"></i>'
            )

        # Get short description
        short_name = template_data.get("short_name", element_name)
        section_number = template_data.get("section_number", "")
        optional = template_data.get("optional", False)

        element_filename = (
            element_name.replace(" ", "_")
            .replace("/", "_")
            .replace("?", "")
            .replace(":", "")
        )

        content += f"""
        <div class="col-lg-6 col-xl-4 mb-3">
            <div class="card element-card searchable">
                <div class="card-body position-relative">
                    <div class="position-absolute top-0 end-0 mt-2 me-2">
                        {status_icon}
                    </div>
                    <h6 class="card-title">
                        <a href="../elements/{element_filename}.html" class="text-decoration-none">
                            {escape_html(short_name)}
                        </a>
                    </h6>
                    <div class="metadata mb-2">
                        {f"Section: {escape_html(section_number)}" if section_number else ""}
                        {" • Optional" if optional else " • Required" if not optional else ""}
                    </div>
                    <div class="mb-2">
                        {badges_html}
                    </div>
                </div>
            </div>
        </div>
        """

    content += """
    </div>
    """

    # Create the full HTML page
    template = get_base_template()
    breadcrumb = create_breadcrumb("Section", section_title=section_title)
    html_content = template.format(
        title=f"{section_title} - FHIR Mapping Navigator",
        home_link="../index.html",
        breadcrumb=breadcrumb,
        content=content,
    )

    # Write the section HTML file
    section_file = html_dir / "sections" / f"{section_filename}.html"
    with open(section_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Created section page: {section_filename}.html ({len(elements)} elements)")


def create_element_page(element_name, element_data, section_title, html_dir):
    """Create an individual element page"""
    element_filename = (
        element_name.replace(" ", "_")
        .replace("/", "_")
        .replace("?", "")
        .replace(":", "")
    )

    template_data = element_data.get("template", {})
    technical_data = element_data.get("technical", {})
    usdm_data = element_data.get("usdm")
    fhir_data = element_data.get("fhir")
    status_data = element_data.get("status")

    # Create status badges
    badges = []
    if usdm_data:
        badges.append('<span class="badge bg-info me-1">USDM Mapped</span>')
    if fhir_data:
        badges.append('<span class="badge bg-warning me-1">FHIR Mapped</span>')

    badges_html = (
        "".join(badges)
        if badges
        else '<span class="badge bg-secondary">No Mappings</span>'
    )

    content = f"""
    <div class="row">
        <div class="col-12">
            <h1>{escape_html(element_name)}</h1>
            <div class="mb-3">
                {badges_html}
            </div>
        </div>
    </div>
    """

    # Template panel
    if template_data:
        content += create_data_panel(
            "Template Information", template_data, "template-panel"
        )

    # Technical panel
    if technical_data:
        content += create_data_panel(
            "Technical Specification", technical_data, "technical-panel"
        )

    # USDM panel
    if usdm_data:
        content += create_data_panel("USDM Mapping", usdm_data, "usdm-panel")

    # FHIR panel
    if fhir_data:
        content += create_data_panel("FHIR Mapping", fhir_data, "fhir-panel")

    # Status panel
    if status_data:
        content += create_data_panel(
            "Implementation Status", status_data, "status-panel"
        )

    # Create the full HTML page
    template = get_base_template()
    breadcrumb = create_breadcrumb(
        "Element", section_title=section_title, element_name=element_name
    )
    html_content = template.format(
        title=f"{element_name} - FHIR Mapping Navigator",
        home_link="../index.html",
        breadcrumb=breadcrumb,
        content=content,
    )

    # Write the element HTML file
    element_file = html_dir / "elements" / f"{element_filename}.html"
    with open(element_file, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_html_files():
    """Main function to generate all HTML files"""
    print("FHIR Mapping HTML Generator")
    print("=" * 40)

    # Load the merged data
    print("Loading merged.yaml...")
    data = load_merged_data()
    if not data:
        return False

    print(f"Loaded {len(data)} data elements")

    # Create HTML directory structure
    print("Creating HTML directory structure...")
    html_dir = create_html_structure()

    # Group data by section
    sections = defaultdict(list)
    for element_name, element_data in data.items():
        template_data = element_data.get("template", {})
        section_title = template_data.get("section_title", "Unknown Section")
        sections[section_title].append((element_name, element_data))

    # Create index page
    print("Creating index.html...")
    create_index_page(data, html_dir)

    # Create section pages
    print("Creating section pages...")
    for section_title, elements in sections.items():
        create_section_page(section_title, elements, html_dir)

    # Create element pages
    print("Creating element pages...")
    element_count = 0
    for element_name, element_data in data.items():
        template_data = element_data.get("template", {})
        section_title = template_data.get("section_title", "Unknown Section")
        create_element_page(element_name, element_data, section_title, html_dir)
        element_count += 1

        if element_count % 50 == 0:
            print(f"  Created {element_count} element pages...")

    print("\nHTML generation completed successfully!")
    print("Generated files:")
    print("  - 1 index page")
    print(f"  - {len(sections)} section pages")
    print(f"  - {len(data)} element pages")
    print("\nOpen html/index.html in your browser to start navigating the data.")

    return True


if __name__ == "__main__":
    success = generate_html_files()
    if not success:
        exit(1)
