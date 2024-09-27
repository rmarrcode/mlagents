note to myself to avoid the pain of setting up env
move mlagents to Documents: C:\Users\rmarr\Documents\mlagents
copy learn.py mlagents and rename it to learn-copy.py 
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
        "justMyCode": false,
      }
    ]
}
set virtual environment to C:\Users\rmarr\Documents\python-envs\.mlagents\Scripts\python.exe
