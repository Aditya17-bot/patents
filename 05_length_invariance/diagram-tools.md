# Architecture Diagram Tools Reference

## Recommended Tools for Antigravity

### Option 1: Matplotlib with Patches (Preferred for Patent Diagrams)

Best for: System architecture diagrams, control flow diagrams, hardware-software interaction diagrams

```python
# Installation (usually pre-installed)
pip install matplotlib

# Template for architecture diagram
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Add boxes for components
box = FancyBboxPatch((x, y), width, height, 
                      boxstyle="round,pad=0.1",
                      facecolor='lightblue', edgecolor='black', linewidth=1.5)
ax.add_patch(box)
ax.text(x + width/2, y + height/2, "Component Name", 
        ha='center', va='center', fontsize=10, fontweight='bold')

# Add arrows for data flow
ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

plt.title("Figure N: [Title]", fontsize=12, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('figure_N.png', dpi=300, bbox_inches='tight')
```

### Option 2: Graphviz (For Complex Flow Diagrams)

```python
# Installation
pip install graphviz
# System dependency (if needed):
# apt-get install graphviz

from graphviz import Digraph

dot = Digraph(comment='System Architecture')
dot.attr(rankdir='TB', size='10,10')

dot.node('A', 'Sensor Interface', shape='box', style='filled', fillcolor='lightblue')
dot.node('B', 'Validation Engine', shape='box', style='filled', fillcolor='lightyellow')
dot.edge('A', 'B', label='sensor data')

dot.render('figure_N', format='png', cleanup=True)
```

### Option 3: Mermaid (Simple Diagrams Only)

```
# Only if mermaid-cli is available
npm install -g @mermaid-js/mermaid-cli
```

## Diagram Types for Patents

### 1. System Architecture Diagram
Shows all major components and their interconnections.
- Must include: physical sensors, processing units, actuators, communication buses
- Color coding: blue for hardware, yellow for processing, green for validation, red for enforcement

### 2. Data Flow Diagram
Shows how data moves through the system.
- Must show: sensor input → processing → validation → decision → actuator output
- Include data types at each stage

### 3. Control Loop Diagram
Shows the closed-loop feedback mechanism.
- Must include: command input → validation → execution → feedback → comparison
- Highlight the enforcement/gating point

### 4. Hardware-Software Interaction Diagram
Shows the boundary between software and physical systems.
- Draw clear boundary line between cyber and physical layers
- Show signal types crossing the boundary

## Graph Types for Experimental Results

### Performance Comparison Bar Chart
```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=df, x='method', y='metric', ax=ax)
ax.set_title('Figure N: [Title]')
ax.set_xlabel('[X Label]')
ax.set_ylabel('[Y Label]')
plt.savefig('figure_N.png', dpi=300, bbox_inches='tight')
```

### Time-Series Line Chart
```python
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['timestamp'], df['metric'], linewidth=1.5)
ax.set_title('Figure N: [Title]')
plt.savefig('figure_N.png', dpi=300, bbox_inches='tight')
```

### Heatmap (Correlation or Spatial)
```python
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=ax)
ax.set_title('Figure N: [Title]')
plt.savefig('figure_N.png', dpi=300, bbox_inches='tight')
```

### Box Plot (Distribution Comparison)
```python
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df, x='category', y='metric', ax=ax)
ax.set_title('Figure N: [Title]')
plt.savefig('figure_N.png', dpi=300, bbox_inches='tight')
```

## Table Generation — Word-Formatted (.docx)

Tables must be generated as `.docx` files using `python-docx`, NOT as markdown or PNG images.

```python
pip install python-docx

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

def create_styled_table(data, headers, title, filename):
    """
    Creates a professionally styled Word table.
    data: list of lists (rows)
    headers: list of column header strings
    title: table caption
    filename: output .docx path
    """
    doc = Document()
    
    # Add caption
    caption = doc.add_paragraph()
    run = caption.add_run(title)
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = 'Arial'
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Create table
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    # Header row styling
    header_color = '1565C0'  # Blue
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(header)
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.name = 'Arial'
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Blue background
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{header_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)
    
    # Data rows with alternating colors
    for row_idx, row_data in enumerate(data):
        for col_idx, value in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = ''
            p = cell.paragraphs[0]
            run = p.add_run(str(value))
            run.font.size = Pt(10)
            run.font.name = 'Arial'
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # Alternating row color
            if row_idx % 2 == 0:
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E3F2FD"/>')
                cell._tc.get_or_add_tcPr().append(shading)
    
    doc.save(filename)
    print(f"Saved: {filename}")
```

### Usage in Antigravity Prompt
```python
# Table 1: System Performance Metrics
headers = ['Performance Metric', 'Value', 'Unit', 'Measurement Basis']
data = [
    # ALL rows computed from dataset — NO hardcoded values
]
create_styled_table(data, headers, 'Table 1: Aggregate System Performance Metrics', 'table_1.docx')
```

Tables output as .docx files — user opens and copies the table directly into patent document.

## Important Notes for Antigravity Prompts

1. Always specify `dpi=300` for publication-quality images
2. Always use `bbox_inches='tight'` to avoid clipping
3. Use consistent color schemes across all diagrams in one patent
4. Font sizes: title=12-14, labels=10-12, annotations=8-10
5. Save all figures as PNG
6. Number figures sequentially across the entire Section 8
