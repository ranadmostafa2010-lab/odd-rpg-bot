
# core/__init__.py
init_content = """# ODD RPG Bot Core Package
__version__ = '2.0.0 Ultimate'
__author__ = 'ODD RPG Team'
"""

with open('core/__init__.py', 'w') as f:
    f.write(init_content)

print("✅ core/__init__.py created!")