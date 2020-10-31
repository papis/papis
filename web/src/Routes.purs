module Route where

import Data.Show (class Show)
import Prelude ((<>))

type LibraryName = String
type PapisQuery = String

data Route
  = LibraryNames
  | LibraryInformation LibraryName
  | AllDocuments LibraryName
  | Documents LibraryName PapisQuery


instance showRoute :: Show Route where
  show LibraryNames = "/library"
  show (LibraryInformation l) = "/library/" <> l
  show (AllDocuments l) = "/library/" <> l <> "/document"
  show (Documents l q) = "/library/" <> l <> "/document/" <> q
