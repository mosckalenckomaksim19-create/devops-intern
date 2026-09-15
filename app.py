"""Small HTTP application for the DevOps internship assignment."""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socket import gethostname


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body = (
                "<!doctype html><html lang='en'><meta charset='utf-8'>"
                "<title>Hello world</title><h1>Hello world!</h1>"
                f"<p>Instance: {escape(gethostname())}</p></html>"
            ).encode("utf-8")
            status, content_type = 200, "text/html; charset=utf-8"
        elif self.path == "/healthz":
            body = b"ok\n"
            status, content_type = 200, "text/plain; charset=utf-8"
        else:
            body = b"Not found\n"
            status, content_type = 404, "text/plain; charset=utf-8"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Instance", gethostname())
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 32777), Handler)
    print("Listening on 0.0.0.0:32777", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
