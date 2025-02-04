from fastapi import FastAPI, HTTPException
from typing import Any

app = FastAPI()


def get_values(data: list[Any]|dict[str, Any]) -> list[Any]:
	"""
	Get the values of a list of dictionary. This function is recursive and can handle nested dictionaries and lists.
	"""
	result = []
	if isinstance(data, dict):
		values = data.values()
		for value in values:
			result.extend(get_values(value))
	elif isinstance(data, list):
		for item in data:
			result.extend(get_values(item))
	else:
		result.append(data)
	return result

def compute_match_score(document: dict[str, Any], sample: dict[str, Any]) -> int:
	"""
	Compute the match score of a document against a sample.
	This is a simple implementation that counts the number of values in the document that are also in the sample.
	"""
	match_score = 0
	sample_values = get_values(sample)
	document_values = get_values(document)
	for value in document_values:
		if value in sample_values:
			match_score += 1
	return match_score

def find_sample_match(document: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
	"""
	Find the sample that matches the document
	"""
	max_match_score = 0
	matching_sample = None
	for sample in samples:
		match_score = compute_match_score(document, sample)
		if match_score > max_match_score:
			max_match_score = match_score
			matching_sample = sample
	return matching_sample

def fetch_sample_descriptions() -> list[dict[str, Any]]:
	"""
	Fetch the sample descriptions from the database.
	"""
	return [
		{
			"Customer Name": "Redline Auto Center",
			"Customer #": "10322",
			"Invoice Number": "IK-901122694",
			"Invoice Amount": "20",
			"Invoice Date": "2019-12-05",
			"Comments": ""
		},
		{
			"Customer Name": "Titan Heavy Industries",
			"Customer #": "120429",
			"Invoice Number": "019854",
			"Invoice Amount": "55350",
			"Invoice Date": "2024-02-25",
			"Comments": ""
		},
		{
			"Customer Name": "Titan Heavy Industries",
			"Customer #": "120422",
			"Invoice Number": "024-2031893",
			"Invoice Amount": "0",
			"Invoice Date": "2024-05-05",
			"Comments": ""
		},
		{
			"Customer Name": "Bella's Bakery",
			"Customer #": "21031",
			"Invoice Number": "2024492186",
			"Invoice Amount": "2022",
			"Invoice Date": "2022-05-02",
			"Comments": ""
		},
		{
			"Customer Name": "Bread Co",
			"Customer #": "204203",
			"Invoice Number": "18587422",
			"Invoice Amount": "0",
			"Invoice Date": "2024-03-24",
			"Comments": ""
		},
		{
			"Customer Name": "Bread Co",
			"Customer #": "204209",
			"Invoice Number": "98531002",
			"Invoice Amount": "0",
			"Invoice Date": "2024-01-29",
			"Comments": ""
		}
	]

def update_sample_match(document: dict[str, Any], sample: dict[str, Any]):
	"""
	Update the sample match in the database. This should ideally store in a database but 
	for the purpose of this example, we will just print the sample that matches the document.
	"""
	print(f"Document: {document}")
	print(f"Matching Sample: {sample}")


@app.post("/document")
async def process_document(document: dict[str, Any]):
	"""
	Process a document and find the sample that matches the document
	"""
	samples = fetch_sample_descriptions()
	matching_sample = find_sample_match(document, samples)
	if matching_sample:
		update_sample_match(document, matching_sample)
	else:
		raise HTTPException(status_code=404, detail="No matching sample found")

