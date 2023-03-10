from rest_framework import routers


class FarmerzAPIView(routers.APIRootView):
    """
    All of the endpoints are documented in their respective pages.
    This page lists a general overview of the endpoints.

    **Note: This documentation will only be present in *development* builds.**

    ---

    ## Authentication

    See the `/token` endpoint for more details on authentication.

    ---

    ## IDs vs URIs

    URIs are preferred to IDs. [See HATEOAS](https://www.google.com/search?q=HATEOAS).
    Therefore, if possible URIs are used to represent resources.

    In certain scenarios, IDs are more appropriate, therefore, the API uses both.


    PS: URIs are not used for now because of frontend's structure.

    ---

    ## Filter and search

    Appropriate filters and search mechanisms are present in relevant APIs.
    You can use the Filters button on the relevant pages.
    This is the documentation for search and filters.

    You can combine search and filtering (although the interface doesn't allow this).

    ---

    ### For example

    For the `item` endpoint,

    `/api/item?categories=1&search=carrot` searches for `carrot` in category id `1`.

    ---

    ## Pagination

    Lists are paginated where appropriate. Page style pagination is used.
    Support for offset-limit style is also possible (currently not exposed).
    Pagination uses common values like `{ "count", "next", "previous", "results" }`

    ---

    ## Rate limits

    API is rate limited to unauthenticated users for now.
    More complex rate limits can be added later.

    ---

    ## About errors and validation

    We follow the convention from [DRF docs. Read here.]
    (https://www.django-rest-framework.org/api-guide/exceptions)

    All `400` series errors return a JSON containing
    a "detail" field which explains the error.

    The exception is validation errors for form like structures. In those cases,
    the JSON response contains:

    - field name as keys and list of error messages as value.
      Example `{'password': ['must contain 8 characters', 'common password']}`
    - Non field errors are present as `non_field_errors`.
      Example `{'non_field_errors': ['user has been banned by admin']}`
    - nested fields work as explained in DRF docs.

    ### Authentication vs Authorization

    - `401 - Unauthorized` is returned for authentication failure.
    - `403 - Forbidden` is returned for authorization failure.

    ---
    """

    pass


class FarmerzRouter(routers.DefaultRouter):
    APIRootView = FarmerzAPIView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = "/?"
