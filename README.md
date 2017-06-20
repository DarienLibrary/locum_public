# locum

## API Endpoints

development host: `minerva.darienlibrary.org:8080`

staging host: `fleur.darienlibrary.org:8080`

Notes:
* All parameters are required unless noted as "(optional)".
* Body parameters must be provided in JSON.
* Sample results reflect the state of results at the time of last edit. Let me know if there are any discrepancies.
* In general, if methods fail, `{"success": false}` is returned. So, all example results below represent successful responses.

### Search

* [search](docs/search/search.md)

### Patron

* [validate](docs/patron/validate.md)
* [circulation](docs/patron/circulation.md)
* [checkout](docs/patron/checkout.md)
* [checkin](docs/patron/checkin.md)
* [placehold](docs/patron/placehold.md)
* [cancelhold](docs/patron/cancelhold.md)
* [history](docs/patron/history.md)
* [update history](docs/patron/update_history.md)
* [basic data](docs/patron/basic_data.md)
* [update basic data](docs/patron/update_basic_data.md)

### BibliographicRecords

* [availability](docs/bibs/availability.md)

### Wishes

* [wishes](docs/wishes/wishes.md)

### Balance (envisionware)

* [balance](docs/balance/balance.md)

### Covers (colin)

* [autofetch](docs/covers/autofetch.md)

### Checkouts

* [deleting checkouts](docs/checkouts/deleting_checkouts.md)