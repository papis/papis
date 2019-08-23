import os
import difflib
import sys
import papis
import papis.api
import papis.config
import papis.commands
import papis.database
import colorama
import logging


logger = logging.getLogger('fzf')

# get all get_all_documents


def main():

    documents = papis.database.get_all_query_string()
    # documents = papis.database.get().query(query)
    print("Documents", documents)
