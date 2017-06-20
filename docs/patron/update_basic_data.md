#### update basic data

updates patron basic info

* url: `\patrons\{patron_id}\`
* method: `patch`
* arguments:
  * url:
    * `patron_id`
  * body: (provide at least one of the following)
    * `email` string
    * `home` string
    * `cell` string
    * `checkout_history` bool

example:

```
PATCH /patrons/38085/ HTTP/1.1
Content-Type: application/json
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 107

{
   "email":"j@yahoo.com",
   "checkout_history":true,
   "home":"555-555-5555",
   "cell":"555-555-5555"
}
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Tue, 26 Apr 2016 16:46:46 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
X-Frame-Options: SAMEORIGIN
Vary: Cookie
Allow: GET, PATCH, HEAD, OPTIONS

{"success":true}
```