import os

d = r'd:\AI\test\survey\templates'
files = [f for f in os.listdir(d) if f.endswith('.html') and f not in ['settings.html', 'nasa_tlx.html']]

general_css = """
    <style>
        html { font-size: calc({{ global_font_size }} * 10px); }
        label, .sus-question-text, .question label { font-size: {{ question_font_size }}rem !important; }
        p, .text-muted, .description { font-size: {{ description_font_size }}rem !important; }
    </style>
"""

for fname in files:
    p = os.path.join(d, fname)
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()

    if '</head>' in content:
        content = content.replace('</head>', general_css + '</head>', 1)
        
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

print("Font CSS restored for all templates.")
