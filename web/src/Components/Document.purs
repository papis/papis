module Components.Document where

import Data.Functor ((<$>))
import Data.Maybe (fromMaybe)
import Data.Show (show)
import Data.Unit (Unit)
import Data.Void (Void)
import Document as DO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Properties as HP
import Prelude (identity, ($))
import Prim.Boolean (True)
import Utils.HTML (cls)


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

--     <div class="input-group is-invalid">
--   <div class="input-group-prepend">
--     <label class="input-group-text" for="validatedInputGroupSelect">Options</label>
--   </div>
--   <select class="custom-select" id="validatedInputGroupSelect" required>
--     <option value="">Choose...</option>
--     <option value="1">One</option>
--     <option value="2">Two</option>
--     <option value="3">Three</option>
--   </select>
-- </div>

renderField ∷ ∀ w i. DO.Document → String → HH.HTML w i
renderField d name = HH.div [cls "input-group"] [label, input]
  where
    label = HH.div [cls "input-group-prepend"]
                   [HH.label [cls "input-group-text"] [HH.text name]]
    input = HH.input [HP.value value, cls "form-control"]
    value = fromMaybe "" $ DO.getString name d

render ∷ ∀ m. State → H.ComponentHTML Action Slots m
render state = HH.div [cls ""] [HH.div [cls "row"] [iframe, fields]]
  where
    keys = DO.keys state.document
    url = fromMaybe "" $ DO.getValidUrl state.document
    col d = HH.div [cls "col"] [d]
    iframe = col $ HH.div [cls "embed-responsive embed-responsive-16by9"]
                          [HH.iframe [ HP.src url
                                     , cls "embed-responsive-item"
                                     ]]
    fields = col $ HH.div [cls "container"] (renderField state.document <$> keys)



