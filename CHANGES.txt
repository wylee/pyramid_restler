0.1a5 (unreleased)
------------------

- Nothing changed yet.


0.1a4 (2013-04-03)
------------------

- Made Python 3 compatible (contributed by eduardosan)


0.1a3 (2011-11-30)
------------------

- Changed project status from pre-alpha to alpha.

- Upgraded Pyramid from 1.1 to 1.2.3.

- Return a 404 response when an attempt is made to DELETE a member that does
  not exist. Previously, the response to a DELETE was *always* a 204.

- Added collection filtering capability.

  The interface for context classes now specifies that the `get_collection`
  method may accept keyword args that can be used to filter and/or sort the
  collection. These keyword args will be particular to the implementation.

  On the view side, if a $$ query param is present in a GET /collection
  request, it must be a JSON object, which will be decoded into a dict and
  passed along as-is to the context's `get_collection` mthod.

- Made construction of JSON output more flexible in SQLAlchemyORMContext.

- Added default HTTP cache view config. All views will by default add
  cache headers to cause all responses to expire immediately.

- Improved test infrastructure a bit. Added several tests. Got coverage for
  `view` module up to 100%.


0.1a2 (2011-07-22)
------------------

- Upgraded Pyramid from 1.0 to 1.1.


0.1a1 (2011-07-06)
------------------

- Initial version.
