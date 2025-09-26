from quart import Quart, send_from_directory, request
from os import path
import contextlib
import io
import yaml
import json
import asyncio
import base64
import traceback

from backend.executor import Context, executor, ExecutorEnvironment, AbortError


app = Quart(
    __name__,
    static_url_path='/static',
    static_folder=path.join(path.dirname(__file__), '../web/')
)


@app.route("/")
async def serve_index():
    return await send_from_directory(app.static_folder, 'index.html')


class ExecutorEnvWeb(ExecutorEnvironment):
    def __init__(self, queue: asyncio.Queue[str]):
        super().__init__()
        self.queue = queue

    async def print(self, *args):
        await self.queue.put(json.dumps({
            'log': ' '.join(str(arg) for arg in args)
        }))

    async def error(self, error: str):
        await self.queue.put(json.dumps({
            'error': error
        }))
    
    async def get_file(self, filename: str, extra: dict):
        @contextlib.asynccontextmanager
        async def ctx():
            with io.BytesIO() as fh:
                yield fh
                fh.seek(0)
                await self.queue.put(json.dumps(dict(
                    name=filename, 
                    data=base64.b64encode(fh.read()).decode('ascii'),
                    **extra,
                )))
        return ctx()


async def _processing_task(queue: asyncio.Queue[str], config: dict|list):
    """
    Run the executor, and then emit `None` to signal completion. 
    """
    env = ExecutorEnvWeb(queue)
    try:
        await Context(executor, env=env).process(config)
    except AbortError as e:
        env.error('Execution halted prematurely.')
    except Exception as e:
        print(f'Unhandled {e.__class__.__name__}: {e}')
        traceback.print_exception(e)
        await queue.put(json.dumps({'error': 'A server side error occurred.'}))
    finally:
        await queue.put(None)  # signals shutdown


async def _stream_renders(yml: str):
    """
    Stream events fromm the executor, rendering any STLs.

    Events are single line json messages which can contain either base64
    encoded stl files, printed debug messages, or error messages.
    """
    queue = asyncio.Queue[str]()
    try:
        config = yaml.safe_load(yml)
    except Exception as e:
        yield json.dumps({'error': f'Failed to parse input: {e}'})
        return

    app.add_background_task(_processing_task, queue, config)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield f'{item}\n'


@app.route("/cgi-bin/render.pl", methods=['POST'])
async def serve_render():
    yaml_data = await request.get_data(as_text=True)
    return _stream_renders(yaml_data)
