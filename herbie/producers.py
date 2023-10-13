
import asyncio
    
from herbie.events import parse

async def hcidle(hub, wants=()):
    cmd = ['herbstclient', '--idle'] + list(wants)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE)
    #print("reading idle")
    while (True):
        line = await proc.stdout.readline()
        line = line.decode().strip()
        obj = parse(line)
        hub.publish(obj)
    
