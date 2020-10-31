module Main where

import Prelude

import Components.List as CL
import Data.Array (length, (!!))
import Data.Maybe (Maybe(..), fromMaybe, maybe)
import Data.Show (show)
import Data.Symbol (SProxy(..))
import Database as DB
import Document as DO
import Effect (Effect)
import Effect.Aff.Class (class MonadAff)
import Halogen as H
import Halogen.Aff as HA
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Halogen.VDom.Driver (runUI)

type Input = Unit
type Output = Unit
type State =
  { documents ∷ Array DO.Document
  , libraries ∷ Array String
  , library ∷ String
  , query ∷ String
  }

data Action
  = GetAvailableLibraries
  | GetAllDocuments
  | SetLibrary String
  | SubmitQuery String


-- | Slot for the components
-- |
-- |    H.Slot query output slot
type Slots =
  ( documentList ∷ ∀ query. H.Slot query Void Int )

_documentList = SProxy ∷ SProxy "documentList"


app ∷ ∀ query m. MonadAff m ⇒ H.Component HH.HTML query Input Output m
app =
  H.mkComponent
    { initialState
    , render
    , eval: H.mkEval $ H.defaultEval { handleAction = handleAction
                                     , initialize = Just GetAvailableLibraries
                                     }
    }
    where
      initialState _ = { documents: []
                       , query: ""
                       , library: ""
                       , libraries: []
                       }


handleAction
  ∷ ∀ m
  . MonadAff m
  ⇒ Action
  → H.HalogenM State Action Slots Output m Unit
handleAction GetAvailableLibraries = do
  libraries ← H.liftAff DB.getLibraries
  H.modify_ \s → s { libraries = fromMaybe [] libraries }
handleAction GetAllDocuments = do
  docs ← H.liftAff $ DB.getAllDocuments "papers"
  H.modify_ \s → s { documents = fromMaybe [] docs }
handleAction (SetLibrary libname) = H.modify_ \s → s { library = libname }
handleAction (SubmitQuery query) = do
  docs ← H.liftAff $ DB.getDocuments "papers" query
  H.modify_ \s → s { documents = fromMaybe [] docs }


renderLibs ∷ ∀ m. State → H.ComponentHTML Action Slots m
renderLibs state = HH.select [ _cls "form-control" ] libs
  where
    event = HE.onSelectedIndexChange getLibrary
    getLibrary ∷ Int → Maybe Action
    getLibrary i = maybe Nothing (Just <<< SetLibrary) $ state.libraries !! i
    _cls = HP.class_ <<< H.ClassName
    libs = (\x → HH.option_ [HH.text x]) <$> state.libraries


render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div [ HP.classes [H.ClassName "container"] ] [q', forms, docList]
  where
    _cls x = HP.classes [H.ClassName x]
    forms = HH.div [ HP.classes [H.ClassName "form-group"] ]
                    [input, submitButton, libs]
    q' = HH.p_ [ HH.text $ "query: "
               <> state.query
               <> " state: "
               <> state.library
               <> " #docs: "
               <> (show $ length state.documents)
               ]
    libs = renderLibs state
    docList = HH.slot _documentList 0 CL.component { documents: state.documents } absurd
    submitButton = HH.button
                     [HE.onClick \x -> Just GetAllDocuments]
                     [HH.text "get all"]
    input = HH.input [ HP.placeholder "database query"
                     , HE.onValueInput \x -> Just $ SubmitQuery x
                     , _cls "form-control"
                     ]


main ∷ Effect Unit
main = HA.runHalogenAff do
    body ← HA.awaitBody
    runUI app unit body
