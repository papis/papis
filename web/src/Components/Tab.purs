module Components.Tab where

import Data.Unit (Unit)
import Document as DO
import Halogen as H
import Halogen.HTML as HH
import Prelude (($))
import Query as Q

type Documents = (Array DO.Document)

data Tab
  = Documents Q.Query Documents
  | Document DO.Document
