#### balance

Gets patron balance

* url: `\patrons\{patron_id}\balance`
* method: `get`
* arguments:
  * url:
    * `patron_id`

example:

```
GET /patrons/15141/balance/ HTTP/1.1
Host: fleur.darienlibrary.org:8080
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Mon, 25 Apr 2016 17:38:16 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Vary: Cookie
Allow: GET, HEAD, OPTIONS
X-Frame-Options: SAMEORIGIN

{"balance":"23.20","success":true}
```