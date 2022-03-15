# LaoTracker
This project is a dash app in python using the RiotAPI to provide an overview about my accounts and my progress along those accounts.

## Development

### Poetry
In order to manage dependencies `poetry` is used.  
Install poetry: `pip install poetry`  
Install environment: `poetry install` (within the projects folder including poetry.lock file)  
Add package to environment: `poetry add pkg`  
Run python file with environment: `poetry run python path/to/file.py`  
Enter environment shell: `poetry shell`  

### API Key
Developers need to add their API Key in lao_tracker/RIOT_API_KEY in plain text.  
For tests and deployment there might be a key stored in github secrets.  

## Deployment

There might be a deployment to a server of mine, but most likely all details will be masked.
