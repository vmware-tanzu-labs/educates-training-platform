Version 2.6.9
=============

New Features
------------

* Any clickable action can now set a `hidden` property. The result of this is
  that the clickable action will be hidden from view in the workshop
  instructions. Not being visible a user will not be able to click on the
  action, however it can still be triggered automatically if `autorestart`
  property is set, or if it follows a clickable action which has `cascade`
  property set. For more details see [Hiding clickable actions from
  view](hiding-clickable-actions-from-view).
