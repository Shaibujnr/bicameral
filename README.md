# Bicameral

## Assumptions and Notes
1. Documents arrive in full meaining we don't get one part of the document in one request and get other parts in other request
2. Documents arrive to our system in one of three ways:
	a. Push => Another service sends the document to us via a REST API endpoint
    b. Pull => We periodically poll for a new document from a queue SQS or DB
	c. Hybrid => When a new document is ready, we are notified via an endpoint and then we pull the document from the source
3. We can achive processing multiple documents at the same time with FastAPI for the push approach. 
4. For the pull approach we can handle it via multi threading and multi processing
5. We can store matches in a database like PostgreSQL
6. To compute match of a document a sample we compute the match score of the document against each sample and the sample with the highest match score > 0 gets the document.
7. We compute match score by seeing how many values in the document match with values in the sample
8. If the document has a match score of zero with all samples then it doesn't match any sample

A lot of the design decision will really depend on what's expected of the system I/O wise.

## Setup
- Python version 3.11.6
- Run `pip install -r requirements.txt`
- Run `fastapi dev main.py`

