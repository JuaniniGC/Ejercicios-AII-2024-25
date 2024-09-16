import urllib.request
from urllib.error import URLError, HTTPError

def read_web(url):
    try:
        raw = urllib.request.urlopen(url)
        return raw.read()
    except HTTPError as e:
        print("Ocurrió un error")
        print(e.code)
    except URLError as e:
        print("Ocurrió un error")
        print(e.code)