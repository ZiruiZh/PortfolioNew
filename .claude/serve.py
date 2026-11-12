"""Local preview server for this folder that never hands a browser a stale copy.

Python's built-in server answers "304 Not Modified" whenever a file is not newer than the browser's
cached date. This site's original files are dated a few hours in the future, so after any edit the
browser kept its old copy. This server always sends the current file and asks browsers not to cache.
Usage: python3 .claude/serve.py [port]
"""
import http.server
import os
import sys


class FreshHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        del self.headers['If-Modified-Since']
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    http.server.ThreadingHTTPServer(('', port), FreshHandler).serve_forever()
