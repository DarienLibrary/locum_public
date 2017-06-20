#### basic data

Gets patron basic info

* url: `\patrons\{patron_id}\`
* method: `get`
* arguments:
  * url:
    * `patron_id`

example:

```
GET /patrons/15141/ HTTP/1.1
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Mon, 25 Apr 2016 17:46:01 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Vary: Cookie
X-Frame-Options: SAMEORIGIN
Allow: GET, HEAD, OPTIONS

{  
   "address":{  
      "county":"FAIRFIELD",
      "country":"USA",
      "state":"CT",
      "street_line_one":"90 STONELEIGH RD",
      "city":"TRUMBULL",
      "postal_code":"06611",
      "street_line_two":""
   },
   "phones":{  
      "home":"203-220-2292",
      "cell":"203-247-2007"
   },
   "checkout_history":true,
   "last_name":"Blyberg",
   "success":true,
   "first_name":"John",
   "email":"john@blyberg.net"
}
```

note: only the first address listed is returned, if no addresses are return `null` value is returned (same for phones)