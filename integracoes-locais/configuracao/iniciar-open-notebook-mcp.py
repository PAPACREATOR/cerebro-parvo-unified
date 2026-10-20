import os,json
from pathlib import Path
root=Path(r'C:\Nexus')
config=json.loads((root/'configuracao/notebook.json').read_text(encoding='utf-8'))
os.environ['OPEN_NOTEBOOK_URL']='http://127.0.0.1:5055'
os.environ['OPEN_NOTEBOOK_PASSWORD']=config['password']
os.environ['MCP_TRANSPORT']='stdio'
from open_notebook_mcp import main
main()
