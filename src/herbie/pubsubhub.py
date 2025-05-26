# https://gist.github.com/appeltel/fd3ddeeed6c330c7208502462639d2c9
import asyncio

class Hub():

    def __init__(self):
        self.subscriptions = set()

    def publish(self, message):
        for queue in self.subscriptions:
            queue.put_nowait(message)

    def subscribe(self, queue):
        self.subscriptions.add(queue)

    def unsubscribe(self, queue):
        self.subscriptions.remove(queue)

class Sub():

    def __init__(self, hub):
        self.hub = hub
        self.queue = asyncio.Queue()

    def __enter__(self):
        self.hub.subscribe(self.queue)
        return self.queue

    def __exit__(self, type, value, traceback):
        self.hub.unsubscribe(self.queue)


# async def reader(name, hub):

#     await asyncio.sleep(random.random() * 15)
#     print(f'Reader {name} has decided to subscribe now!')

#     msg = ""    
#     with Subscription(hub) as queue:
#         while msg != 'SHUTDOWN':
#             msg = await queue.get()
#             print(f'Reader {name} got message: {msg}')

#             if random.random() < 0.1:
#                 print(f'Reader {name} has read enough')
#                 break

#     print(f'Reader {name} is shutting down')


# async def writer(name, iterations, hub):

#     for x in range(iterations):
#         print(f'Writer {name}: I have {len(hub.subscriptions)} subscribers now')
#         hub.publish(f'Hello world - {x} - from {name}')
#         await asyncio.sleep(3)
#     hub.publish('SHUTDOWN')
