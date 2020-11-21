module Utils.String where

import Control.Category ((<<<))
import Data.Array (last)
import Data.Either (Either(..))
import Data.Function (($))
import Data.Maybe (fromMaybe)
import Data.String.Regex (regex, split)
import Data.String.Regex.Flags (noFlags)


basename ∷ String → String
basename path = case regex "[/\\\\]" noFlags of
  Right r → fromMaybe path <<< last <<< split r $ path
  Left _ → path
