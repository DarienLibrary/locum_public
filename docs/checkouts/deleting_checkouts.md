#### deleting checkouts

##### delete single checkout

* url: `\checkouts\{checkout_id}\`
* method: `delete`
* arguments:
  * url:
    * `checkout_id`
  * body:
    * `patron_id`

example:
```
DELETE /checkouts/151/ HTTP/1.1
Content-Type: application/json
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 107
```
results:
```
HTTP/1.1 204 NO CONTENT
Server: nginx/1.4.6 (Ubuntu)
Date: Tue, 26 Apr 2016 17:21:14 GMT
Content-Length: 0
Connection: close
X-Frame-Options: SAMEORIGIN
Vary: Cookie
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS
```

#### purging all of one patron's checkouts

* url: `\checkouts\purge\`
* method: `delete`
* arguments:
  * body:
    * `patron_id` - integer

example:
```
DELETE /checkouts/purge/ HTTP/1.1
Content-Type: application/json
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 19

{"patron_id":38085}
```

results:
```
HTTP/1.1 204 NO CONTENT
Server: nginx/1.4.6 (Ubuntu)
Date: Tue, 26 Apr 2016 17:27:57 GMT
Content-Length: 0
Connection: close
X-Frame-Options: SAMEORIGIN
Vary: Cookie
Allow: DELETE, OPTIONS
```