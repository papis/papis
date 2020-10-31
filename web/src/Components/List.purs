module Components.List where

import Data.Maybe (Maybe(..), fromMaybe)
import Document as DO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Properties as HP
import Prelude (Unit, Void, ($), (<$>), (<<<), (<>))
import Templates.Bootstrap as BO

type State = { documents ∷ Array DO.Document }
type Input = { documents ∷ Array DO.Document }
type Output = Void
type Slots = ()

data Action
  = OpenListItem
  | Receive Input

component ∷ ∀ query m. H.Component HH.HTML query Input Output m
component = H.mkComponent
    { initialState
    , render
    , eval: H.mkEval $ H.defaultEval { handleAction = handleAction
                                     , receive = Just <<< Receive
                                     }
    }
    where
      initialState a = a

handleAction
  ∷ ∀ m
  . Action
  → H.HalogenM State Action Slots Output m Unit
handleAction OpenListItem = H.modify_ \s → s
handleAction (Receive input) = H.modify_ \s → s { documents = input.documents }

renderDocument ∷ ∀ w i. DO.Document → HH.HTML w i
renderDocument doc = HH.li [lgi] [title', author', year']
        where
          lgi = BO.listGroupItem'
          tags = fromMaybe [] $ DO.tags doc
          year = fromMaybe "" $ DO.year doc
          year' = HH.small_ [HH.text year]
          author' = HH.p [_cls "mb-1"] [HH.text author]
          author = fromMaybe "" $ DO.author doc
          tags' = (\x → HH.span [tagsClass] [HH.text x]) <$> tags
          tagsClass = BO.badge' BO.Primary
          _cls = HP.class_ <<< H.ClassName
          title = fromMaybe "" $ DO.title doc
          title' = HH.div [_cls "justify-content-between"]
                          ([titleHeader] <> tags')
          titleHeader = HH.h5 [_cls "mb-1"] [HH.text title]

render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div [lg] docs
  where
    lg = BO.listGroup'
    docs = renderDocument <$> state.documents
