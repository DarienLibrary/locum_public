#### circulation

Gets checkout and hold data from ILS or e-content providers.

* url: `\patrons\{patron_id}\circulation\?provider={provider}`
* method: `get`
* arguments:
  * url:
    * `patron_id`
  * query_parameter:
    * `provider` (optional) - values: `bibliotheca`, `overdrive`
      if no value provided returns circulation data from the ILS

example:

```
GET /patrons/38085/circulation/?provider=bibliotheca HTTP/1.1
Content-Type: application/json
Host: minerva:8080
Connection: close
User-Agent: Paw/2.3.2 (Macintosh; OS X/10.11.1) GCDHTTPRequest
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Fri, 25 Mar 2016 14:06:04 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: GET, HEAD, OPTIONS
X-Frame-Options: SAMEORIGIN
Vary: Cookie

{  
   "provider_elaspsed_time":"0.68879",
   "checkouts":[  
      {  
         "author":"Donna Tartt",
         "checkout_date":"2016-03-25T10:16:16-04:00",
         "found_bib":true,
         "provider":"bibliotheca",
         "format_abbr":"ebk",
         "provider_id":"dqeg5r9",
         "expiration_date":"2016-04-15T10:16:16-04:00",
         "locum_id":1493085,
         "abs_mat_code":"ebook",
         "title":"The Goldfinch",
         "ils_id":184422
      }
   ],
   "success":true,
   "holds":[  
      {  
         "hold_list_position":"1",
         "is_ready":false,
         "expiration_date":null,
         "locum_id":1499077,
         "ils_id":196588,
         "author":"Anthony Doerr",
         "abs_mat_code":"ebook",
         "found_bib":true,
         "provider":"bibliotheca",
         "is_suspended":false,
         "provider_id":"ect4h89",
         "title":"All the Light We Cannot See A Novel",
         "format_abbr":"elr",
         "hold_placed_date":"2016-03-25T10:20:20-04:00"
      }
   ]
}
```
