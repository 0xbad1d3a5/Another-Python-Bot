import os
import re

# Accept file as part of module if it ends in ".py" and does not being with "_"
search = re.compile("(?!_).*(?=.py$)")
__all__ = [f[:-3] for f in os.listdir("./modules") if search.match(f)]
