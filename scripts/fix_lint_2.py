import re

def fix_md025(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        first_h1_found = False
        for i, line in enumerate(lines):
            if line.startswith('# '):
                if not first_h1_found:
                    first_h1_found = True
                else:
                    lines[i] = '#' + line
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
    except FileNotFoundError:
        pass

def fix_md024(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        current_phase = ""
        for i, line in enumerate(lines):
            if line.startswith('## Phase'):
                current_phase = line.strip().replace('## ', '').split('—')[0].strip()
            elif line.startswith('### ') and current_phase:
                heading = line.strip().replace('### ', '')
                # To make it unique, prepend the current phase
                if not heading.startswith('Phase'):
                    lines[i] = f"### {current_phase} {heading}\n"
                
        with open(filepath, 'w') as f:
            f.writelines(lines)
    except FileNotFoundError:
        pass

fix_md025('/home/cp-lab/sih_fleex_workspace/dev/FLEEX_TODO.md')
fix_md024('/home/cp-lab/sih_fleex_workspace/dev/ROADMAP.md')
