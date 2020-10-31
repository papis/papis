module Templates.Bootstrap where

import Data.Show (class Show, show)
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Properties as HP
import Halogen.HTML.Properties.ARIA (role)
import Prelude (($), (<>))


data Style
  = Primary
  | Secondary
  | Success
  | Danger
  | Warning
  | Info
  | Light
  | Dark

instance showStyle ∷ Show Style where
  show Primary = "primary"
  show Secondary = "secondary"
  show Success = "success"
  show Danger = "danger"
  show Warning = "warning"
  show Info = "info"
  show Light = "light"
  show Dark = "dark"

type Node r w i
  = Array (HH.IProp r i)
  → Array (HH.HTML w i)


mkStyledProperty ∷ ∀ r i . String → Style → HH.IProp (class ∷ String | r) i
mkStyledProperty name style = HP.classes [ H.ClassName className ]
  where
    className = name <> " " <> name <> "-" <> show style

mkProperty ∷ ∀ r i . String → HH.IProp (class ∷ String | r) i
mkProperty name = HP.classes [ H.ClassName name ]

-- ALERTS
alert' ∷ ∀ r i . Style → HH.IProp (class ∷ String | r) i
alert' = mkStyledProperty "alert"

alertLink ∷ ∀ r i . HH.IProp (class ∷ String | r) i
alertLink = mkProperty "alert-link"

-- LIST GROUP
listGroup' ∷ ∀ r i . HH.IProp (class ∷ String | r) i
listGroup' = mkProperty "list-group"

listGroupItem' ∷ ∀ r i . HH.IProp (class ∷ String | r) i
listGroupItem' = mkProperty "list-group-item"

-- BADGES
badge' ∷ ∀ r i . Style → HH.IProp (class ∷ String | r) i
badge' = mkStyledProperty "badge"
