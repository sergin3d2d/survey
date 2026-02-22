import os, re
d = r'd:\AI\test\survey\templates'
for f in os.listdir(d):
    if f.endswith('.html'):
        p = os.path.join(d, f)
        with open(p, 'r', encoding='utf-8') as file:
            content = file.read()
            
        content = re.sub(r'\{\s*\{\s*([a-zA-Z_0-9]+)\s*\}\s*\}', r'{{ \1 }}', content)
        content = re.sub(r'\{%\s*endif\s*%\}', r'{% endif %}', content)
        
        with open(p, 'w', encoding='utf-8') as file:
            file.write(content)
print("done")
