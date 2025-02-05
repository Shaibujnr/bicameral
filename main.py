from threading import Lock
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Any
from collections import defaultdict
from pydantic.dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
app = FastAPI()

@dataclass
class MatchedDocument:
	sample_id: str # id of the sample this document matched
	match_score: int # the match score
	document: dict[str, Any] # the document


class MockStorage:
	def __init__(self):
		self._lock = Lock()
		self._samples_store: list[dict[str, Any]] = [
		{
			"Id": "001",
			"Customer Name": "Redline Auto Center",
			"Customer #": "10322",
			"Invoice Number": "IK-901122694",
			"Invoice Amount": "20",
			"Invoice Date": "2019-12-05",
			"Comments": ""
		},
		{
			"Id": "002",
			"Customer Name": "Titan Heavy Industries",
			"Customer #": "120429",
			"Invoice Number": "019854",
			"Invoice Amount": "55350",
			"Invoice Date": "2024-02-25",
			"Comments": ""
		},
		{
			"Id": "003",
			"Customer Name": "Titan Heavy Industries",
			"Customer #": "120422",
			"Invoice Number": "024-2031893",
			"Invoice Amount": "0",
			"Invoice Date": "2024-05-05",
			"Comments": ""
		},
		{
			"Id": "004",
			"Customer Name": "Bella's Bakery",
			"Customer #": "21031",
			"Invoice Number": "2024492186",
			"Invoice Amount": "2022",
			"Invoice Date": "2022-05-02",
			"Comments": ""
		},
		{
			"Id": "005",
			"Customer Name": "Bread Co",
			"Customer #": "204203",
			"Invoice Number": "18587422",
			"Invoice Amount": "0",
			"Invoice Date": "2024-03-24",
			"Comments": ""
		},
		{
			"Id": "006",
			"Customer Name": "Bread Co",
			"Customer #": "204209",
			"Invoice Number": "98531002",
			"Invoice Amount": "0",
			"Invoice Date": "2024-01-29",
			"Comments": ""
		}
	]
		self._unmatched_documents_store: list[dict[str, Any]] = [] # holds list of documents that did not match any sample
		self._matched_documents_store: list[MatchedDocument] = [] # holds list of documents that matched a sample
		self._match_store = defaultdict(list) # holds a mapping between the sample and it's matching documents

	def fetch_samples(self) -> list[dict[str, Any]]:
		return self._samples_store
	
	def fetch_matched_documents(self) -> list[MatchedDocument]:
		with self._lock:
			return self._matched_documents_store

	def fetch_unmatched_documents(self) -> list[dict[str, Any]]:
		with self._lock:
			return self._unmatched_documents_store

	def get_match(self) -> dict[str, list[dict[str, Any]]]:
		with self._lock:
			return self._match_store

	def add_unmatched_document(self, document: dict[str, Any]) -> None:
		with self._lock:
			self._unmatched_documents_store.append(document)

	def save_matched_document(self, matched_document: MatchedDocument) -> None:
		with self._lock:
			self._matched_documents_store.append(matched_document)
			self._match_store[matched_document.sample_id].append(matched_document.document)

	def remove_unmatched_document(self, document: dict[str, Any]) -> None:
		with self._lock:
			self._unmatched_documents_store.remove(document)

	def replace_matched_document(self, old_matched_document: MatchedDocument, new_matched_document: MatchedDocument) -> None:
		with self._lock:
			self._matched_documents_store.remove(old_matched_document)
			self._match_store[old_matched_document.sample_id].remove(old_matched_document.document)
			self._matched_documents_store.append(new_matched_document)
			self._match_store[new_matched_document.sample_id].append(new_matched_document.document)


storage = MockStorage()
			

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

def compute_match_score(document: dict[str, Any], sample_or_document: dict[str, Any]) -> int:
	"""
	Compute the match score of a document against a sample.
	This is a simple implementation that counts the number of values in the document that are also in the sample.
	"""
	match_score = 0
	sample_values = get_values(sample_or_document)
	document_values = get_values(document)
	for value in document_values:
		if value in sample_values:
			match_score += 1
	return match_score

def match_document(document: dict[str, Any]) -> MatchedDocument|None:
	"""
	Find the sample that matches the document. Check for a match between the document and each sample
	and then check for a match between the document and previously matched documents. If the document
	matches a previously matched document, then return the sample that matched the previously matched document.
	"""
	max_match_score = 0
	matching_sample_id = None
	# check document against each sample
	samples = storage.fetch_samples()
	for sample in samples:
		match_score = compute_match_score(document, sample)
		if match_score > max_match_score:
			max_match_score = match_score
			matching_sample_id = sample["Id"]
	# check document against previously matched documents
	matched_documents = storage.fetch_matched_documents()
	for matched_document in matched_documents:
		match_score = compute_match_score(document, matched_document.document)
		if match_score > max_match_score:
			max_match_score = match_score
			matching_sample_id = matched_document.sample_id
	if matching_sample_id is not None:
		return MatchedDocument(sample_id=matching_sample_id, document=document, match_score=max_match_score)
	return None

def save_matched_document(matched_document: MatchedDocument) -> None:
	"""
	Store/Persist matched document
	"""
	storage.save_matched_document(matched_document)

def match_unmatched_documents_task(matched_document: MatchedDocument) -> None:
	"""
	This task will check each unmatched document against the provided matched document and match them if they match.
	"""
	logger.info("Matching unmatched documents")
	unmatched_documents = storage.fetch_unmatched_documents()
	for unmatched_document in unmatched_documents:
		match_score = compute_match_score(unmatched_document, matched_document.document)
		if match_score > 0:
			storage.remove_unmatched_document(unmatched_document)
			new_matched_document = MatchedDocument(
				sample_id=matched_document.sample_id,
				document=unmatched_document,
				match_score=match_score
			)
			save_matched_document(new_matched_document)
			logger.info("Matched a previously unmatched document")
			logger.info(new_matched_document)
	logger.info("Done matching unmatched documents")

def rematch_matched_documents_task(matched_document: MatchedDocument) -> None:
	"""
	This task will check each matched document against the provided newly matched document and rematch them if they match better.
	"""
	logger.info("Matching matched documents")
	matched_documents = storage.fetch_matched_documents()
	for already_matched_document in matched_documents:
		match_score = compute_match_score(already_matched_document.document, matched_document.document)
		if match_score > already_matched_document.match_score:
			logger.info(f"Found better match, old match score {already_matched_document.match_score} and new match score {match_score}")
			new_match = MatchedDocument(
				sample_id=matched_document.sample_id,
				document=already_matched_document.document,
				match_score=match_score
			)
			storage.replace_matched_document(already_matched_document, new_match)
			logger.info(f"Matched document has been rematched. Old sample Id {already_matched_document.sample_id} and New Sample Id {matched_document.sample_id}")
	logger.info("Done matching matched documents")

@app.post("/document")
async def process_document(document: dict[str, Any], background_tasks: BackgroundTasks):
	"""
	Process a document and find the sample that matches the document.
	For every newly received document it will try to match the document with a sample. If it's unable 
	to find a match for the document, it will store the document in the unmatched_documents list. However,
	when it does match successfully, it uses this new match to attempt matching with previously unmatched documents and
	also to see if this document matches better with previously matched samples and then updates the match dictionary.
	"""
	matched_document = match_document(document)
	if matched_document is not None:
		save_matched_document(matched_document)
		# check if the newly matched document has any match with documents that couldn't be matched previously and match them
		background_tasks.add_task(match_unmatched_documents_task, matched_document)
		# check if already matched documents match better with this new document and rematch them
		background_tasks.add_task(rematch_matched_documents_task, matched_document)
	else:
		storage.add_unmatched_document(document)
		raise HTTPException(status_code=404, detail="No matching sample found")

		


@app.get("/match")
def get_match():
	"""
	Get the match dictionary
	"""
	return storage.get_match()
