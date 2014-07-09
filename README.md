ES Curator
==========

A quick and dirty python script to delete old ES indices.
The official ES Curator project does not support http auth.
This just uses the base URL and requests lib to perform DELETE operations.

Run:

     pip install -r requirements.txt
     python es_curator.py --help
