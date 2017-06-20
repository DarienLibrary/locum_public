#### wishes

##### Get wishes

* url: `/wishes/`
* method: `get`
* arguments:
  * url:
    * `patron_id`
    * `limit`
    * `offset`

example:

```
GET /wishes/?patron_id=38085&limit=10&offset=0 HTTP/1.1
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
```

results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Tue, 26 Apr 2016 13:59:26 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: GET, POST, HEAD, OPTIONS
Vary: Cookie
X-Frame-Options: SAMEORIGIN

{  
   "count":1,
   "next":null,
   "previous":null,
   "results":[  
      {  
         "id":15,
         "date_created":"2016-04-26T13:56:53.437939Z",
         "work_record":{  
            "id":2,
            "title":"20 years of Rolling Stone : what a long, strange trip it's been",
            "author":""
         }
      }
   ],
   "success":true,
   "wishes":[  
      {  
         "id":15,
         "date_created":"2016-04-26T13:56:53.437939Z",
         "work_record":{  
            "id":2,
            "title":"20 years of Rolling Stone : what a long, strange trip it's been",
            "author":""
         }
      }
   ]
}
```
#####Create a wish

* url: `/wishes/`
* method: `post`
* arguments:
  * body:
    * `patron_id`
    * `work_id`

#####Delete a wish

* url: `/wishes/{wish_id}/`
* method: `delete`
* arguments:
    * url:
      * `wish_id`
    * body:
      * `patron_id`

example:

```
DELETE /wishes/10/ HTTP/1.1
Content-Type: text/plain
Host: fleur.darienlibrary.org:8080
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
Content-Length: 32
```

result:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Mon, 25 Apr 2016 15:35:37 GMT
Content-Type: application/json
Content-Length: 0
Connection: close
X-Frame-Options: SAMEORIGIN
Vary: Cookie
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS

{"success":true}
```
