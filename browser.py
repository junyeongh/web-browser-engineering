import socket
import ssl


class URL:
    schemes = ["http", "https", "file", "data"]

    def __init__(self, url):
        self.scheme, url = url.split(":", 1)
        url = url.lstrip("//")

        assert self.scheme in self.schemes

        match self.scheme:
            case "http" | "https":
                if "/" not in url:
                    url = url + "/"
                self.host, url = url.split("/", 1)
                self.path = "/" + url

                if self.scheme == "http":
                    self.port = 80
                if self.scheme == "https":
                    self.port = 443

                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)

            case "file":
                self.host = None
                self.path = url
                self.port = None

            case "data":
                self.host = None
                self.path = None
                self.port = None

                self.mime, self.data = url.split(",", 1)
                self.mime_type, self.mime_subtype = self.mime.split("/")

    def request(self, headers={}):
        match self.scheme:
            case "http" | "https":
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP,
                )
                if self.scheme == "https":
                    ctx = ssl.create_default_context()
                    s = ctx.wrap_socket(s, server_hostname=self.host)

                address = (self.host, self.port)
                s.connect(address)

                request = f"GET {self.path} HTTP/1.1\r\n"
                request += f"Host: {self.host}\r\n"
                request += "Connection: close\r\n"
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
                s.send(request.encode("utf8"))

                response = s.makefile("r", encoding="utf8", newline="\r\n")
                statusline = response.readline()
                version, status, explanation = statusline.split(" ", 2)

                response_headers = {}
                while True:
                    line = response.readline()
                    if line == "\r\n":
                        break
                    header, value = line.split(":", 1)
                    response_headers[header.casefold()] = value.strip()

                # assert "transfer-encoding" not in response_headers
                assert "content-encoding" not in response_headers

                body = response.read()
                s.close()

                return body

            case "file":
                try:
                    with open(self.path) as f:
                        body = f.read()
                        return body
                except FileNotFoundError:
                    with open("./src/index.html") as f:
                        body = f.read()
                        return body

            case "data":
                match self.mime:
                    case "text/html":
                        return f"<html><head></head><body>{self.data}</body></html>\r\n"
                    case _:
                        return self.data


def show(body):
    _in_tag = False
    for c in body:
        print(c, end="")
        match c:
            case "<":
                _in_tag = True
            case ">":
                _in_tag = False
            case _:
                # print(c, end="")
                pass


def load(url):
    body = url.request()
    show(body)


def main():
    import sys

    load(URL(sys.argv[1]))


if __name__ == "__main__":
    main()
