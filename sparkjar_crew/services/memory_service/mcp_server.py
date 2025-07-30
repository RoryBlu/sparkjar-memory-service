class MemoryMCPServer:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def start(self):
        return True
