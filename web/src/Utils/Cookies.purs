module Utils.Cookies where

import Effect (Effect)
import Prelude (Unit)

foreign import setCookies ∷ String → Effect Unit
foreign import getCookies ∷ Effect String
