#### placehold

Places a hold on for ILS content and e-content.

* url: `\patrons\{patron_id}\place_hold\?provider={provider_id}`
* method: `post`
* arguments:
  * url:
    * `patron_id`
  * query_parameters:
    * `provider` - values: "mmm", "overdrive"
  * body:
    * `email` - string

example:

```
POST /patrons/38085/place_hold/?provider=bibliotheca HTTP/1.1
Content-Type: application/json
Host: minerva:8080
Connection: close
User-Agent: Paw/2.3.2 (Macintosh; OS X/10.11.1) GCDHTTPRequest
Content-Length: 25

{"provider_id":"dqeg5r9"}
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Fri, 25 Mar 2016 14:04:20 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: POST, OPTIONS
X-Frame-Options: SAMEORIGIN
Vary: Cookie

{"success":true}
```
