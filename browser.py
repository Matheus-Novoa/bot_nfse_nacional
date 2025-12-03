from patchright.sync_api import sync_playwright
from pathlib import Path


class Browser:

    def __init__(self, download_dir):
        self.play = None
        self.browser = None
        self.page = None
        self.download_dir = Path(download_dir)
        self._browser_dir = Path('browser_dir')
        self._channel = 'chrome'


    def setup_browser(self):
        if not self._browser_dir.exists():
            self._browser_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.download_dir.exists():
            self.download_dir.mkdir(parents=True, exist_ok=True)

        self.play = sync_playwright().start()
        
        self.browser = self.play.chromium.launch_persistent_context(
            user_data_dir=self._browser_dir.name,
            downloads_path=self.download_dir,
            channel=self._channel,
            headless=False,
            ignore_https_errors=True,
            args=['--start-maximized']
        )
        self.page = self.browser.new_page()

        return self.page
    
    def close_browser(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.play:
            self.play.stop()