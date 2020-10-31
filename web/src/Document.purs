module Document where

import Control.Category ((<<<))
import Data.Argonaut (_Object, _String)
import Data.Argonaut.Core (Json)
import Data.Lens (preview)
import Data.Lens.Index (ix)
import Data.Maybe (Maybe)
import Data.String (Pattern(..), split)
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

tags ∷ Document → Maybe (Array String)
tags doc = do
 _tags <- getString "tags" doc
 pure $ split (Pattern " ") _tags
