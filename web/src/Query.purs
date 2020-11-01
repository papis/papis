module Query where

import Data.Show (class Show)

-- | We will change the queries in the future
-- | to give it a more semantic structure
newtype Query = Query String

instance showQuery ∷ Show Query where
  show (Query s) = s

mkQuery ∷ String → Query
mkQuery = Query
