module Database where

import Affjax as AX
import Affjax.ResponseFormat as ResponseFormat
import Data.Argonaut.Core (Json, toArray, toString)
import Data.Either (Either(..))
import Data.Maybe (Maybe(..), fromMaybe)
import Document as DO
import Effect.Aff (Aff)
import Prelude (bind, pure, show, ($), (<$>), (<<<))
import Route as R

toStringArray ∷ Json → Maybe (Array String)
toStringArray j = do
  ar <- toArray j
  jar ← Just $ ((fromMaybe "") <<< toString) <$> ar
  pure jar

getLibraries ∷ Aff (Maybe (Array String))
getLibraries = do
  result <- AX.get ResponseFormat.json route
  case result of
     Left error -> pure $ Nothing
     Right resp -> pure $ toStringArray resp.body
  where
    route = show $ R.LibraryNames

getAllDocuments ∷ String → Aff (Maybe (Array DO.Document))
getAllDocuments libname = do
  result <- AX.get ResponseFormat.json route
  case result of
     Left error -> pure Nothing
     Right resp -> pure $ toArray resp.body
  where
    route = show $ R.AllDocuments libname

getDocuments ∷ R.LibraryName → R.PapisQuery → Aff (Maybe (Array DO.Document))
getDocuments l q = do
  result <- AX.get ResponseFormat.json route
  case result of
     Left error -> pure Nothing
     Right resp -> pure $ toArray resp.body
  where
    route = show $ R.Documents l q
