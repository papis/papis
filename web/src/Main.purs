module Main where

import Prelude

import Biscotti.Cookie as Cookie
import Components.Document as CD
import Components.List as CL
import Components.Tab as CT
import Data.Array (length, range, zip, (!!))
import Data.Either (Either(..))
import Data.Maybe (Maybe(..), fromMaybe)
import Data.String (take)
import Data.Symbol (SProxy(..))
import Data.Tuple (Tuple(..))
import Database as DB
import Document as DO
import Effect (Effect)
import Effect.Aff.Class (class MonadAff)
import Effect.Console (log)
import Halogen as H
import Halogen.Aff as HA
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Halogen.HTML.Properties.ARIA as HPA
import Halogen.VDom.Driver (runUI)
import Query as Q
import Templates.Bootstrap as BO
import Utils.Cookies as UC
import Utils.HTML (cls)

type Input = Unit
type Output = Unit
type State =
  { libraries ∷ Array String
  , library ∷ String
  , query ∷ String
  , tabs ∷ Array CT.Tab
  }

data Action
  = GetAvailableLibraries
  | GetAndProcessCookies
  | GetAllDocuments
  | SetLibrary String
  | SubmitQuery String
  | OpenDocument DO.Document


-- | Slot for the components
-- |
-- |    H.Slot query output slot
type Slots =
  ( documentList ∷ ∀ query. H.Slot query CL.Output Int
  , documentView ∷ ∀ query. H.Slot query CD.Output Int
  )

_documentList = SProxy ∷ SProxy "documentList"
_documentView = SProxy ∷ SProxy "documentView"


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
      initialState _ = { query: ""
                       , library: ""
                       , libraries: []
                       , tabs: []
                       }


handleAction
  ∷ ∀ m
  . MonadAff m
  ⇒ Action
  → H.HalogenM State Action Slots Output m Unit
handleAction (OpenDocument d) = do
  H.liftEffect $ log $ "setting document"
  H.modify_ \s → s { tabs = s.tabs <> [CT.Document d]
                   }
handleAction GetAvailableLibraries = do
  libraries ← H.liftAff DB.getLibraries
  H.modify_ \s → s { libraries = fromMaybe [] libraries
                   , library = fromMaybe "" $ libraries >>= (_ !! 0)
                   }
  handleAction GetAndProcessCookies
handleAction GetAndProcessCookies = do
  --cookie ← H.liftEffect getCookies
  --H.modify_ \s → s { query = fromMaybe "" $ Cookie.getValue <$> cookie }
  H.get >>= H.put
handleAction GetAllDocuments = do
  state ← H.get
  docs ← H.liftAff $ DB.getAllDocuments state.library
  H.modify_ \s → s { tabs = state.tabs <> [CT.Documents (Q.mkQuery "∀")
                                                        (fromMaybe [] docs)] }
handleAction (SetLibrary libname) = H.modify_ \s → s { library = libname }
handleAction (SubmitQuery query) = do
  state ← H.get
  docs ← H.liftAff $ DB.getDocuments state.library query
  let newState = state { query = ""
                       , tabs = state.tabs
                              <> [CT.Documents (Q.mkQuery query)
                                               (fromMaybe [] docs)]
                       }
  --H.liftEffect $ setCookies newState
  H.modify_ \s → newState


setCookies ∷ State → Effect Unit
setCookies s = do
  let c = Cookie.stringify $ Cookie.new "query" s.query
  UC.setCookies c
  log $ "setting cookie " <> c


getCookies ∷ Effect (Maybe Cookie.Cookie)
getCookies = do
  cookies ← UC.getCookies
  case Cookie.parse cookies of
      Right c → pure <<< Just $ c
      otherwise → pure Nothing



navBar ∷ ∀ m. State → H.ComponentHTML Action Slots m
navBar state = HH.nav [nav'] [hamburger, menu, searchBar]
  where
    nav' = cls "navbar navbar-expand-lg navbar-light bg-light"
    searchBar = HH.div [ cls "input-group w-20" ]
                       [libs, input, submitButton]
    input = HH.input [ HP.placeholder "database query"
                     , HP.value state.query
                     , HPA.label "search"
                     , HE.onValueChange \x → Just $ SubmitQuery x
                     , cls "form-control"
                     ]
    submitButton = HH.button [ HE.onClick \x → Just GetAllDocuments
                             , cls "btn btn-outline-success form-control"
                             ]
                             [HH.text "All"]
    libs = renderLibs state
    hamburger = HH.button [ cls "navbar-toggler"
                          , HPA.expanded "false"
                          , HPA.label "Toggle navigation"
                          ]
                          [hamburgerIcon]
    hamburgerIcon = HH.span [ cls "navbar-toggler-icon" ][]
    menu = HH.div [cls "collapse navbar-collapse"] [brand, table]
    brand = HH.a [cls "navbar-brand", HP.href "#"] [HH.text "Papis"]
    navLink txt href = HH.a [cls "nav-link", HP.href href ] [HH.text txt]
    table = HH.ul [cls "navbar-nav mr-auto -mt-2 mt-lg-0"]
                  [ HH.li [cls "nav-item active"] [navLink "Documents" "#"]
                  , HH.li [cls "nav-item"] [navLink "Import" "#"]
                  , HH.li [cls "nav-item"] [navLink "Settings" "#"]
                  ]


renderLibs ∷ ∀ m. State → H.ComponentHTML Action Slots m
renderLibs state = HH.select [ cls "form-control", event ] libs
  where
    event = HE.onValueChange (\x → Just $ SetLibrary x)
    libs = (\x → HH.option [HP.value x] [HH.text x]) <$> state.libraries

tabId ∷ Int → String
tabId i = "main-tab-" <> show i


renderTab ∷ ∀ m. (Tuple Int CT.Tab) → H.ComponentHTML Action Slots m
renderTab (Tuple i (CT.Document d)) = HH.div [id, cls "tab-pane"] [doc]
  where
    id = HP.id_ $ tabId i
    doc = HH.slot _documentView i CD.component {document: d} absurd
renderTab (Tuple i (CT.Documents q docs)) = HH.div [id, cls "tab-pane"] [docList]
  where
    id = HP.id_ $ tabId i
    docList = HH.slot _documentList i CL.component {documents: docs} _handleAction
    _handleAction ∷ CL.Output → Maybe Action
    _handleAction (CL.Clicked doc) = Just $ OpenDocument doc
    _handleAction (CL.QueryTag t) = Just <<< SubmitQuery $ "tags:" <> t

style :: forall r i. String -> HH.IProp (style :: String | r) i
style = HH.prop (HH.PropName "style")

renderTabHeader ∷ ∀ w i. (Tuple Int CT.Tab) → HH.HTML w i
renderTabHeader (Tuple i (CT.Document d)) = a
  where
    a = BO.a [ cls "nav-link"
             , href
             , dt
             ] [icon, HH.text title ]
    title = " " <> (take 20 <<< fromMaybe "" $ DO.title d)
    icon = HH.i [cls "fa fa-file"] []
    href = HP.href $ "#" <> tabId i
    dt = BO.dataToggle "pill"
    --truncate s = substring s
renderTabHeader (Tuple i (CT.Documents q ds)) = a
  where
    a = BO.a [cls "nav-link", href, dt] [icon, HH.text $ " " <> show q <> num]
    icon = HH.i [cls "fa fa-list"] []
    num = " (" <> (show $ length ds) <> ")"
    href = HP.href $ "#" <> tabId i
    dt = BO.dataToggle "tab"


render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div [] [nav, tabs]
  where
    nav = navBar state
    enumeratedTabs = zip tabRange state.tabs
    tabRange = range 0 (length state.tabs)
    tabNav = HH.nav [] [tabHeaders]
    tabs = HH.div [cls "row"] [tabHeaders, tabContent]
    tabHeaders = HH.div [cls "col-sm-2"] [HH.div [cls "nav flex-column nav-pills"] (renderTabHeader <$> enumeratedTabs)]
    tabContent = HH.div [cls "col-sm-10"] [HH.div [cls "tab-content"] (renderTab <$> enumeratedTabs)]


main ∷ Effect Unit
main = HA.runHalogenAff do
    body ← HA.awaitBody
    runUI app unit body
