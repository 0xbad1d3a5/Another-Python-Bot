A simple IRC bot written in Python 3.

There are no external dependencies in the core bot code, but there are some in the modules. To get the bot running create a "info" file with the required connection information in JSON (see sample for an example).

The architecture of the bot is irc.py communicates with the server, which bot.py calls in a loop to get chat text. If a command is triggered, a new thread is spun off to handle the command based on the module (detected using reflection). It is realized that reflection and multiple threads are extremely expensive for simple commands, however many modules I written required web access and some heavy processing, which may block the bot. A less resource intensive solution is being investigated for simpler modules.

A database API is also being throught of for safe storage of information instead of the current "throw everything in a JSON file" solution.