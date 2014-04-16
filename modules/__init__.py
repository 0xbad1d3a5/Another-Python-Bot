import os

__all__ = [x[:-3] for x in os.listdir("./modules")
           if x[-3:] == ".py"
           and x != "__init__.py"]
