import urllib.request
from urllib.error import URLError, HTTPError

# No usamos urllib2, ya que en Python 3 se unificaron urllib y urllib2
# urllib. --> urllib.parse
# urllib2. --> urllib.request

try:
    f = urllib.request.urlopen("http://www.python.org")
    print(f.read())
    f.close()
except HTTPError as e:
    print("Ocurrió un error")
    print(e.code)
except URLError as e:
    print("Ocurrió un error")
    print(e.code)
