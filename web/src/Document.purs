module Document where

import Control.Alt ((<|>))
import Control.Applicative ((<$>))
import Control.Category ((<<<))
import Data.Argonaut (_Array, _Object, _String)
import Data.Argonaut.Core (Json, caseJsonObject)
import Data.Lens (preview)
import Data.Lens.Index (ix)
import Data.Maybe (Maybe(..), fromMaybe)
import Data.Monoid ((<>))
import Data.String (Pattern(..), split)
import Foreign.Object as Obj
import Prelude (bind, pure, ($))

type Document = Json
type FieldName = String

getString ∷ FieldName → Document → Maybe String
getString fieldName doc = preview (_Object <<< ix fieldName <<< _String) doc

-- | TODO: get all elements correctly
getArray ∷ FieldName → Document → Maybe (Array String)
getArray fieldName doc = case preview (_Object <<< ix fieldName <<< _Array <<< ix 0 <<< _String) doc of
  Just s -> Just [s]
  otherwise -> Nothing

title ∷ Document → Maybe String
title = getString "title"

author ∷ Document → Maybe String
author = getString "author"

year ∷ Document → Maybe String
year = getString "year"

doi ∷ Document → Maybe String
doi = getString "doi"

doiUrl :: Document → Maybe String
doiUrl d = ("https://doi.org/" <> _) <$> doi d

getValidUrl ∷ Document → Maybe String
getValidUrl d = getString "url" d <|> doiUrl d

tags ∷ Document → Maybe (Array String)
tags doc = do
 _tags ← getString "tags" doc
 pure $ split (Pattern " ") _tags

files ∷ Document → Array String
files doc = fromMaybe [] $ getArray "files" doc

keys ∷ Document → Array String
keys d = caseJsonObject [] Obj.keys d
