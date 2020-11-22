module Utils.HTML where

import Data.Function ((<<<))
import Halogen as H
import Halogen.HTML (IProp)
import Halogen.HTML.Properties as HP

cls ∷ ∀ r i. String → IProp (class ∷ String | r) i
cls = HP.class_ <<< H.ClassName

blankTarget :: forall a b. IProp (target :: String | b) a
blankTarget = HP.target "_blank"
