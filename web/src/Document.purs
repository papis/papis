module Document where

import Control.Alt ((<|>))
import Control.Applicative ((<$>))
import Control.Category ((<<<))
import Data.Argonaut (_Object, _String)
import Data.Argonaut.Core (Json, caseJsonObject)
import Data.Lens (preview)
import Data.Lens.Index (ix)
import Data.Maybe (Maybe)
import Data.Monoid ((<>))
import Data.String (Pattern(..), split)
import Foreign.Object as Obj
import Prelude (bind, pure, ($))

type Document = Json
type FieldName = String

getString ∷ FieldName → Document → Maybe String
getString fieldName doc = preview (_Object <<< ix fieldName <<< _String) doc

title ∷ Document → Maybe String
title = getString "title"

author ∷ Document → Maybe String
author = getString "author"

year ∷ Document → Maybe String
year = getString "year"

getValidUrl ∷ Document → Maybe String
getValidUrl d
  =   getString "url" d
  <|> ("https://doi.org/" <> _) <$> getString "doi" d

tags ∷ Document → Maybe (Array String)
tags doc = do
 _tags <- getString "tags" doc
 pure $ split (Pattern " ") _tags

keys ∷ Document → Array String
keys d = caseJsonObject [] Obj.keys d
