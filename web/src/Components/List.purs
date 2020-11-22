module Components.List where

import Data.Array (foldr, fromFoldable)
import Data.Maybe (Maybe(..), fromMaybe)
import Document as DO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Prelude (Unit, ($), (<$>), (<<<), (<>))
import Templates.Bootstrap as BO
import Utils.HTML (blankTarget, cls)

type State = { documents ∷ Array DO.Document }
type Input = { documents ∷ Array DO.Document }
data Output = Clicked DO.Document
            | QueryTag String
type Slots = ()

data Action
  = OpenListItem
  | Receive Input
  | ClickTag String
  | Click DO.Document

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
handleAction (Click d) = do
  H.raise $ Clicked d
handleAction OpenListItem = H.modify_ \s → s
handleAction (Receive input) = H.modify_ \s → s { documents = input.documents }
handleAction (ClickTag tag) = H.raise $ QueryTag tag

renderTag ∷ ∀ m. String → H.ComponentHTML Action Slots m
renderTag t = HH.a [HP.href "#", HE.onClick \x → Just $ ClickTag t] [span]
  where
    span = HH.span [tagsClass] [HH.text t]
    tagsClass = BO.badge' BO.Primary

renderDocument ∷ ∀ m. DO.Document → H.ComponentHTML Action Slots m
renderDocument doc = HH.li [lgia, event] $ [title', author', year']
                                         <> (foldr (\ x y → fromFoldable x <> y)  [] [url'])
                                         <> files
        where
          lgia = BO.listGroupItemAction'
          urlClass = BO.badge' BO.Success
          url = DO.getValidUrl doc
          url' = (\x → a x
                       $ HH.i [cls "badge badge-success fa fa-link"]
                              [HH.text " "]) <$> url
          files = (\x → a x
                       $ HH.i [cls "badge badge-success fa fa-file"]
                              [HH.text " "]) <$> DO.files doc
          a href el = HH.a [HP.href href, blankTarget] [el]
          event = HE.onClick \x → Just $ Click doc
          tags = fromMaybe [] $ DO.tags doc
          year = fromMaybe "" $ DO.year doc
          year' = HH.small_ [HH.text year]
          author' = HH.p [cls "mb-1"] [HH.text author]
          author = fromMaybe "" $ DO.author doc
          tags' = renderTag <$> tags
          title = fromMaybe "NO TITLE" $ DO.title doc
          title' = HH.div [cls "justify-content-between"]
                          ([titleHeader] <> tags')
          i n = HH.i [cls $ "fa fa-" <> n] [HH.text " "]
          titleHeader = HH.h5 [cls "mb-1"] [a "#" $ i "ellipsis-v"
                                           , HH.text " "
                                           , HH.text title
                                           ]

render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div [lg] docs
  where
    lg = BO.listGroup'
    docs = renderDocument <$> state.documents
