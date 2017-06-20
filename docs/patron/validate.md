####validate

Validates patron against ILS using barcode and email

* url: `\patrons\validate\`
* method: `post`
* arguments:
  * body:
    * `email` - string
    * `barcode` - string

example query body:

```
{
  "barcode":"12345678900000",
  "email":"tmctesting@darienlibrary.org",
}
```


results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Fri, 25 Mar 2016 13:32:59 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: POST, OPTIONS
X-Frame-Options: SAMEORIGIN
Vary: Cookie

{  
   "patron_code":"STAFF",
   "valid":true,
   "patron_id":12345,
   "barcode":"12345678900000",
   "email":"tmctesting@darienlibrary.org",
   "first_name":"Test",
   "last_name":"McTesting",
   "expiration_date":"2018-01-02T00:00:00"
}
