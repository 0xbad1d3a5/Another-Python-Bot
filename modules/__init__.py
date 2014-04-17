import os

# Accept file as part of module if it ends in ".py" and is not listed below
__all__ = [x[:-3] for x in os.listdir("./modules")
           if x[-3:] == ".py"
           and x != "__init__.py"
           and x != "_example_module.py"]
