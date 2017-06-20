#### history

Updates reading history.

* url: `\patrons\{patron_id}\update_history`
* method: `post`
* arguments:
  * url:
    * `patron_id`

example:

```
POST /patrons/15141/update_history/ HTTP/1.1
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 0
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Mon, 25 Apr 2016 18:54:52 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
X-Frame-Options: SAMEORIGIN
Vary: Cookie
Allow: POST, OPTIONS

{"success":true}
```
