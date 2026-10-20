import asyncio,json,os,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(r'C:\Nexus')
CONFIG=json.loads((ROOT/'configuracao/notebook.json').read_text(encoding='utf-8'))
REPORT={'protocol':'MCP stdio real','server':'open-notebook-mcp==0.3.0','checks':[]}
def unpack(result):
    if result.isError:raise RuntimeError('Ferramenta MCP devolveu erro')
    if result.structuredContent is not None:return result.structuredContent
    for item in result.content:
        if getattr(item,'type',None)=='text':return json.loads(item.text)
    raise RuntimeError('Sem resultado estruturado')
async def run(url,password,negative=None):
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','PATHEXT','TEMP','TMP')}
    env.update(OPEN_NOTEBOOK_URL=url,MCP_TRANSPORT='stdio',PYTHONUTF8='1')
    if password:env['OPEN_NOTEBOOK_PASSWORD']=password
    args=['-c','from open_notebook_mcp import main; main()'] if negative else ['-X','utf8',str(ROOT/'configuracao/iniciar-open-notebook-mcp.py')]
    params=StdioServerParameters(command=sys.executable,args=args,env=env)
    with (ROOT/'registos/open-notebook-mcp-servidor.log').open('a',encoding='utf-8') as log:
        async with stdio_client(params,errlog=log) as (read,write):
            async with ClientSession(read,write) as session:
                initialized=await session.initialize()
                if negative:
                    result=await session.call_tool('list_notebooks',{'limit':5})
                    assert result.isError,'Falha deveria ser rejeitada'
                    REPORT['checks'].append({'test':negative,'status':'PASS'})
                    return
                tools=await session.list_tools();names=sorted(t.name for t in tools.tools)
                assert len(names)==33 and {'list_notebooks','list_sources','list_models','search_capabilities'}<=set(names)
                REPORT['tools_count']=len(names)
                REPORT['checks'].append({'test':'initialize-and-tools-list','status':'PASS'})
                for name,args in [('search_capabilities',{'query':'','detail':'name','limit':50}),('list_notebooks',{'limit':20}),('list_sources',{'limit':20}),('list_models',{'limit':20})]:
                    value=unpack(await session.call_tool(name,args))
                    assert isinstance(value,dict) and isinstance(value.get('count'),int)
                    REPORT['checks'].append({'test':name,'status':'PASS','count':value['count']})
                REPORT['server_identity']=initialized.serverInfo.model_dump()
async def main():
    await run('http://127.0.0.1:5055',CONFIG['password'])
    await run('http://127.0.0.1:5055',None,'unauthenticated-request-rejected')
    await run('http://127.0.0.1:1',CONFIG['password'],'backend-unavailable-controlled-error')
    REPORT.update(status='PASS',scope='Descoberta e leitura via protocolo MCP real; sem escrita nem geracao IA')
try:asyncio.run(asyncio.wait_for(main(),timeout=100))
except BaseException as e:
    REPORT.update(status='FAIL',error=type(e).__name__)
    raise
finally:
    (ROOT/'registos/open-notebook-mcp-teste-real.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
    print(json.dumps(REPORT,indent=2))
