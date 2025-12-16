from patchright.async_api import async_playwright
from pathlib import Path


class Browser:

    def __init__(self, download_dir):
        self.play_obj = None
        self.play = None
        self.browser = None
        self.page = None
        self.download_dir = Path(download_dir)
        self._browser_dir = Path('browser_dir')
        self._channel = 'chrome'


    async def setup_browser(self):
        if not self._browser_dir.exists():
            self._browser_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.download_dir.exists():
            self.download_dir.mkdir(parents=True, exist_ok=True)

        self.play_obj = async_playwright().start()
        self.play = await self.play_obj
        
        self.browser = await self.play.chromium.launch_persistent_context(
            user_data_dir=self._browser_dir.name,
            downloads_path=self.download_dir,
            channel=self._channel,
            headless=False,
            ignore_https_errors=True,
            args=['--start-maximized']
        )
        self.page = await self.browser.new_page()

        return self.page
    
    async def close_browser(self):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.play:
            await self.play.stop()