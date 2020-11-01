module Components.Document where

import Data.Maybe (fromMaybe)
import Data.Unit (Unit)
import Data.Void (Void)
import Document as DO
import Halogen as H
import Halogen.HTML as HH
import Prelude (identity, ($))


type State = { document ∷ DO.Document }
type Input = { document ∷ DO.Document }
type Output = Void
type Slots = ()
type Action = Unit


component ∷ ∀ query m. H.Component HH.HTML query Input Output m
component =
  H.mkComponent
    { initialState: identity
    , render
    , eval: H.mkEval $ H.defaultEval
    }

render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div_ [HH.text $ fromMaybe "no title" $ DO.title state.document]
