#### history

Gets reading history.

* url: `\patrons\{patron_id}\history`
* method: `get`
* arguments:
  * url:
    * `patron_id`
    * `limit`
    * `offset`

example:

```
GET /patrons/15141/history/?limit=10&offset=0 HTTP/1.1
Host: localhost:5555
Connection: close
User-Agent: Paw/2.3.1 (Macintosh; OS X/10.11.2) GCDHTTPRequest
```

results:
```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Tue, 26 Apr 2016 14:02:32 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: GET, HEAD, OPTIONS
Vary: Cookie
X-Frame-Options: SAMEORIGIN

{  
   "count":8,
   "next":null,
   "previous":null,
   "results":[  
      {  
         "id":160,
         "title":"The secret chord a novel",
         "author":"Brooks, Geraldine.",
         "checkout_date":"2015-10-23T13:40:58Z"
      },
      {  
         "id":159,
         "title":"After you",
         "author":"Moyes, Jojo, 1969-",
         "checkout_date":"2015-10-10T17:16:01Z"
      },
      {  
         "id":158,
         "title":"When someone you love suffers from posttraumatic stress : what to expect and what you can do",
         "author":"Zayfert, Claudia.",
         "checkout_date":"2015-02-24T21:45:25Z"
      },
      {  
         "id":157,
         "title":"The world of ice & fire : the untold history of Westeros and the Game of Thrones",
         "author":"Martin, George R. R.",
         "checkout_date":"2014-11-26T18:49:29Z"
      },
      {  
         "id":156,
         "title":"Unbroken : a World War II story of survival, resilience, and redemption",
         "author":"Hillenbrand, Laura, author.",
         "checkout_date":"2014-11-12T21:03:51Z"
      },
      {  
         "id":155,
         "title":"Artemis Fowl : the Arctic incident",
         "author":"Colfer, Eoin.",
         "checkout_date":"2014-09-04T19:22:15Z"
      },
      {  
         "id":154,
         "title":"All the light we cannot see (CD)",
         "author":"Doerr, Anthony.",
         "checkout_date":"2014-06-24T14:42:09Z"
      },
      {  
         "id":153,
         "title":"Between you & me",
         "author":"Calin, Marisa.",
         "checkout_date":"2014-01-05T18:04:12Z"
      }
   ],
   "success":true
}
```