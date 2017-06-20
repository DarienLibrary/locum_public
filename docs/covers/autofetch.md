#### auto fetch

Checks sources for cover.

* url: `/works/{work_id}/poll_sources/`
* method: `post`
* arguments:
  * url:
    * `work_id`

example:

```
POST /works/1/poll_sources/ HTTP/1.1
Content-Type: application/json
Host: colin.darienlibrary.org
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 62
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Mon, 25 Apr 2016 20:28:57 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: POST, OPTIONS
Vary: Cookie
X-Frame-Options: SAMEORIGIN

{}
```
