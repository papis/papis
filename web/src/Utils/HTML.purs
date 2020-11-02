module Utils.HTML where

import Data.Function ((<<<))
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Properties as HP

cls ∷ ∀ r i. String → HH.IProp (class ∷ String | r) i
cls = HP.class_ <<< H.ClassName
