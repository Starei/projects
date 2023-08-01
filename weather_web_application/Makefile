SHELL = C:/Windows/System32/cmd

# Styling
.PHONY: style
style:
	black .
	flake8 .
	isort .

# Cleaning -> Here an error throws
.PHONY: clean
clean:
	for /d /r . %d in (.ipynb_checkpoints, .vscode, __pycache__) \
    do @if exist "%d" rd /s/q "%d"
	

# Help
.PHONY: help
help:
	echo Commands:
	echo style -> executes style formatting.
	echo clean -> cleans all unnecessary files.
