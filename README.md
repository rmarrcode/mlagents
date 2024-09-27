# Setting Up the MLAgents Environment

## Steps to Follow:

- **Move `mlagents` to `Documents`:**
  - Path: `C:\Users\rmarr\Documents\mlagents`

- **Copy `learn.py` to `mlagents` and rename it:**
  - New file: `learn-copy.py`

- **Configure `launch.json` for VSCode:**

  ```json
  {
    "version": "0.2.0",
    "configurations": [
      {
        "name": "Python: Current File",
        "type": "python",
        "request": "launch",
        "program": "${file}",
        "args": [
            "C:\\Users\\rmarr\\Documents\\visibility-game\\Assets\\ryan_was_here\\config\\hide-and-seek.yaml",
            "--force"
        ],
        "console": "integratedTerminal",
        "env": {
          "PYTHONPATH": "C:\\Users\\rmarr\\Documents"
        },
        "justMyCode": false
      }
    ]
  }
