#### search

Searches queries against elasticsearch index

* url: `\search\`
* method: `post`
* arguments:
  * body:
    * `query` - string
    * `limit` - integer
    * `offset` - integer
    * `type` - ['keyword', 'title', 'subject', 'author']
    * `facets` - array (example below)


    ```
    [{"terms": {"abs_mat_codes":["book","ebook"]}},
    {"range": {"pub_year":{"gte":2015, "lt":2017}}},
    {"terms": {"age":["adult"]}}]
    ```

example query body:
```
{
  "query": "brothers karamazov",
  "type": "keyword",
  "facets": [
    {
      "terms": {
        "abs_mat_codes": [
          "book",
          "ebook"
        ]
      }
    },
    {
      "range": {
        "pub_year": {
          "gte": 1990,
          "lt": 2016
        }
      }
    },
    {
      "terms": {
        "age": [
          "adult"
        ]
      }
    }
  ],
  "limit": 2,
  "offset": 0
}
```
results:

```
HTTP/1.1 200 OK
Server: nginx/1.4.6 (Ubuntu)
Date: Fri, 25 Mar 2016 13:16:34 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: close
Allow: POST, OPTIONS
X-Frame-Options: SAMEORIGIN
Vary: Cookie

{  
   "aggregations":{  
      "abs_mat_codes":{  
         "buckets":[  
            {  
               "doc_count":304,
               "key":"book"
            },
            {  
               "doc_count":50,
               "key":"eaudiobook"
            },
            {  
               "doc_count":32,
               "key":"audiobook"
            },
            {  
               "doc_count":24,
               "key":"ebook"
            }
         ],
         "sum_other_doc_count":0,
         "doc_count_error_upper_bound":0
      },
      "age":{  
         "buckets":[  
            {  
               "doc_count":304,
               "key":"adult"
            },
            {  
               "doc_count":1,
               "key":"teen"
            }
         ],
         "sum_other_doc_count":0,
         "doc_count_error_upper_bound":0
      },
      "pub_year":{  
         "avg":2008.3980263157894,
         "sum":610553.0,
         "count":304,
         "max":2015.0,
         "min":1991.0
      }
   },
   "success":true,
   "works":[  
      {  
         "id":45585,
         "title":"The brothers Karamazov",
         "author":"Fyodor Dostoyevsky",
         "bib_records":[  
            {  
               "locum_id":1530877,
               "ils_id":236677,
               "browse_author":"Dostoyevsky, Fyodor, 1821-1881.",
               "browse_title":"The Brothers Karamazov",
               "provider":"",
               "provider_id":"",
               "format_abbr":"bks",
               "abs_mat_code":"book"
            },
            {  
               "locum_id":1508008,
               "ils_id":207277,
               "browse_author":"Dostoyevsky, Fyodor, 1821-1881.",
               "browse_title":"The brothers Karamazov",
               "provider":"hoopla",
               "provider_id":"",
               "format_abbr":"aeb",
               "abs_mat_code":"eaudiobook"
            },
            {  
               "locum_id":1503745,
               "ils_id":202872,
               "browse_author":"Dostoyevsky, Fyodor, 1821-1881.",
               "browse_title":"The brothers Karamazov",
               "provider":"hoopla",
               "provider_id":"",
               "format_abbr":"aeb",
               "abs_mat_code":"eaudiobook"
            },
            {  
               "locum_id":1502467,
               "ils_id":201562,
               "browse_author":"Dostoyevsky, Fyodor, 1821-1881.",
               "browse_title":"The brothers Karamazov",
               "provider":"hoopla",
               "provider_id":"",
               "format_abbr":"aeb",
               "abs_mat_code":"eaudiobook"
            },
            {  
               "locum_id":1458904,
               "ils_id":93366,
               "browse_author":"Dostoyevsky, Fyodor, 1821-1881",
               "browse_title":"The brothers Karamazov",
               "provider":"",
               "provider_id":"",
               "format_abbr":"bks",
               "abs_mat_code":"book"
            }
         ]
      },
      {  
         "id":11195,
         "title":"Brothers : a novel",
         "author":"Ben Bova",
         "bib_records":[  
            {  
               "locum_id":1423370,
               "ils_id":24568,
               "browse_author":"Bova, Ben, 1932-",
               "browse_title":"Brothers : a novel",
               "provider":"",
               "provider_id":"",
               "format_abbr":"bks",
               "abs_mat_code":"book"
            }
         ]
      }
   ],
   "total":304
}
```
