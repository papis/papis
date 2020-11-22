module Templates.Bootstrap where

import DOM.HTML.Indexed (Interactive)
import Data.Maybe (Maybe)
import Data.MediaType (MediaType(..))
import Data.Show (class Show, show)
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Elements as HE
import Halogen.HTML.Events as HEV
import Halogen.HTML.Properties as HP
import Prelude (($), (<>))
import Web.UIEvent.MouseEvent (MouseEvent)


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

listGroupItemAction' ∷ ∀ r i . HH.IProp (class ∷ String | r) i
listGroupItemAction' = mkProperty "list-group-item list-group-item-action"

-- BADGES
badge' ∷ ∀ r i . Style → HH.IProp (class ∷ String | r) i
badge' = mkStyledProperty "badge"

-- NAVIGATION
nav' ∷ HH.ClassName
nav' = HH.ClassName "nav"

-- PROPERTIES
-- dataToggle :: forall r i. String -> HH.IProp ( dataToggle :: String | r ) i
-- dataToggle = HH.prop (HH.PropName "data-toggle")

dataToggle :: forall r i. String -> HH.IProp r i
dataToggle = HH.attr (HH.AttrName "data-toggle")

-- TAG WRAPPERS

type HTMLa = Interactive
  ( download :: String
  , href :: String
  , hrefLang :: String
  , rel :: String
  , target :: String
  , dataToggle ∷ String
  , type :: MediaType
  )

a :: ∀ w i. HH.Node HTMLa w i
a = HE.element (HH.ElemName "a")

-- | Usual close button. I had to insert a unicode &times; because
-- | I did not know how to put it.
closeButton :: forall a b. (MouseEvent -> Maybe a) -> HH.HTML b a
closeButton f = HH.button
              [ HP.class_ $ HH.ClassName "close"
              , HEV.onClick f
              ] [HH.text "⨉"]
