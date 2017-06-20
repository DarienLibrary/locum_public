#### checkout

Checks out e-content.

* url: `\patrons\{patron_id}\checkout\?provider={provider_id}`
* method: `post`
* arguments:
  * url:
    * `patron_id`
  * query_parameters:
    * `provider` - values: `bibliotheca`, `overdrive`
  * body:
    * `ils_id` - string

example:

```
POST /patrons/38085/checkout/?provider=bibliotheca HTTP/1.1
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
Date: Fri, 25 Mar 2016 14:01:36 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: POST, OPTIONS
X-Frame-Options: SAMEORIGIN
Vary: Cookie

{"success":true}
```
