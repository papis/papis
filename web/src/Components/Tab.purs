module Components.Tab where

import Document as DO
import Query as Q

type Documents = (Array DO.Document)

data Tab
  = Documents Q.Query Documents
  | Document DO.Document
