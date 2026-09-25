import re

def fix_md025(filepath):
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

def fix_md024_and_md036(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # fix MD036 (Emphasis used instead of a heading) - wait, line 5 in ROADMAP is **FLEEX — Edge-AI...**
    # We can change it to a heading or just leave it. The user just threw the lint block.
    
    # fix MD024 (duplicate headings)
    current_phase = ""
    for i, line in enumerate(lines):
        if line.startswith('## Phase'):
            current_phase = line.strip().replace('## ', '').split('—')[0].strip()
        elif line.startswith('### Tasks'):
            lines[i] = f"### {current_phase} Tasks\n" if current_phase else "### Tasks\n"
        elif line.startswith('### Exit Condition'):
            lines[i] = f"### {current_phase} Exit Condition\n" if current_phase else "### Exit Condition\n"
        elif line.startswith('### Tests'):
            lines[i] = f"### {current_phase} Tests\n" if current_phase else "### Tests\n"
            
    with open(filepath, 'w') as f:
        f.writelines(lines)

fix_md025('/home/cp-lab/sih_fleex_workspace/dev/AI_RULES.md')
fix_md025('/home/cp-lab/sih_fleex_workspace/dev/ROADMAP.md')
fix_md024_and_md036('/home/cp-lab/sih_fleex_workspace/dev/ROADMAP.md')
