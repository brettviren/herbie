
from herbie.pubsubhub import Sub
from herbie.events import terminate

async def chirp(hub):
    with Sub(hub) as queue:
        while True:             # fixme: define a terminate condition
            event = await queue.get()
            if (isinstance(event, terminate)):
                break
            print(event)

    
