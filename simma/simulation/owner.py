import asyncio

from simma.simulation.process import Client


class Owner:
    """Manages a simulation as an owner, controlling who can currently edit the simulation."""

    def __init__(self, owner_client: Client):
        self._client: Client = owner_client
        self._editor_token = None
        self._edit_lock = asyncio.Lock()

    def get_editor(self):
        return self._editor_token

    async def start_editing(self, editor_token):
        if not editor_token:
            raise ValueError("Cannot start editing: invalid editor token.")

        async with self._edit_lock:
            if self._editor_token:
                raise RuntimeError("Cannot start editing: there is already an editor.")

            if await self._client.is_editing():
                raise RuntimeError("FATAL ERROR: Owner and simulation edit state are mismatched.")

            await self._client.set_editor_token(editor_token)

            self._editor_token = editor_token

    async def end_editing(self, editor_token):
        if not self._editor_token or editor_token != self._editor_token:
            raise RuntimeError("Cannot end edits: not editor.")

        await self._client.set_editor_token('')
        self._editor_token = None
