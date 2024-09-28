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

  
- **Set the virtual environment in VSCode:**
  - Python interpreter: `C:\Users\rmarr\Documents\python-envs\.mlagents\Scripts\python.exe`
 
  
### Additional Notes:
- **Ensure `PYTHONPATH`** is correctly set to point to the parent directory of `mlagents`, as shown in the `launch.json` configuration.
- **Virtual Environment Activation:** If not using the Python extension’s interpreter selector, manually activate the virtual environment in the terminal.

This should help streamline your setup and avoid issues in the future!

