import os
import glob
import re

files = glob.glob("*.html")

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove the exact <p> tag containing "Pusat Pendidikan dan Pelatihan Keuangan" across multiple lines
    content = re.sub(
        r'[ \t]*<p class="text-\[10px\] font-bold mt-1 uppercase tracking-widest text-slate-500">\s*Pusat Pendidikan(?: dan)?\s*Pelatihan Keuangan\s*</p>\n?',
        '',
        content
    )
    
    # Just in case "Republik Indonesia" is left awkwardly on a newline in the copyright, let's fix it if asked. But I only remove the unit <p> tag here.
    
    if content != original_content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
