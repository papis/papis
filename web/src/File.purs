module File where

import Control.Category ((<<<))
import Data.Boolean (otherwise)
import Data.Either (Either(..))
import Data.Function (const)
import Data.Maybe (isJust)
import Data.String.Regex (match, regex)
import Data.String.Regex.Flags (noFlags)

type FileName = String

data FileType
  = Pdf FileName
  | Epub FileName
  | Data FileName

matchEnding ∷ String → (String → Boolean)
matchEnding ending = case regex ending noFlags of
  Left _ -> const false
  Right r -> isJust <<< match r

matchFileName ∷ FileName → FileType
matchFileName name
  | matchEnding "*.pdf" name = Pdf name
  | matchEnding "*.epub" name = Epub name
  | otherwise = Data name
