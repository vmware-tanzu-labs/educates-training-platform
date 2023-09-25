Client Authentication
=====================

The training portal web interface is a quick way of providing access to a set of workshops when running a supervised training workshop. For integrating access to workshops into an existing web site, or for creating a custom web interface for accessing workshops hosted across one or more training portals, you can use can use the portal REST API.

The REST API will give you access to the list of workshops hosted by a training portal instance and allow you to request and access workshop sessions. This bypasses the training portal's own user registration and login so you can implement whatever access controls you need. This could include anonymous access, or access integrated into an organisations single sign on system.

Querying the credentials
------------------------

To provide access to the REST API a robot account is automatically provisioned. The login credentials and details of the OAuth client endpoint used for authentication, can be obtained by querying the resource definition for the training portal after it has been created and the deployment completed. If using ``kubectl describe``, you would use:

```
kubectl describe trainingportal.training.educates.dev/lab-markdown-sample
```

In the status section of the output you will see:

```
Status:
  educates:
    Clients:
      Robot:
        Id:      ACZpcaLIT3qr725YWmXu8et9REl4HBg1
        Secret:  t5IfXbGZQThAKR43apoc9usOFVDv2BLE
    Credentials:
      Admin:
        Password:  0kGmMlYw46BZT2vCntyrRuFf1gQq5ohi
        Username:  educates
      Robot:
        Password:  QrnY67ME9yGasNhq2OTbgWA4RzipUvo5
        Username:  robot@educates
```

The admin login credentials is what you would use if logging into the training portal web interface to access admin pages.

The robot login credentials is what would be used if wish to access the REST API.

Requesting an access token
--------------------------

Before you can make requests against the REST API to query details on workshops or request a workshop session, you need to login via the REST API to get an access token.

This would be done from any front end web application or provisioning system, but the step is equivalent to making a REST API call using ``curl`` of:

```
curl -v -X POST -d "grant_type=password&username=robot@educates&password=<robot-password>" -u "<robot-client-id>:<robot-client-secret>" https://lab-markdown-sample-ui.test/oauth2/token/
```

The URL sub path is ``/oauth2/token/``.

Upon success, the output will be a JSON response consisting of:

```
{
    "access_token": "tg31ied56fOo4axuhuZLHj5JpUYCEL",
    "expires_in": 36000,
    "token_type": "Bearer",
    "scope": "user:info",
    "refresh_token": "1ryXhXbNA9RsTRuCE8fDAyZToJmp30"
}
```

Refreshing the access token
---------------------------

The access token which is provided will expire and will need to be refreshed before it expires if being used by a long running application.

To refresh the access token you would use the equivalent of:

```
curl -v -X POST -d "grant_type=refresh_token&refresh_token=<refresh-token>&client_id=<robot-client-id>&client_secret=<robot-client-secret>" https://lab-markdown-sample-ui.test/oauth2/token/
```

As with requesting the initial access token, the URL sub path is ``/oauth2/token/``.

The JSON response will be of the same format as if a new token had been requested.

Revoking the access token
-------------------------

The access token would normally be retained by a client and used on subsequent requests until it expires. If this is not being done, a client should revoke the token so it is no longer valid.

To revoke the access token you would use the equivalent of:

```
curl -v -X POST -d "token=<access-token>&client_id=<robot-client-id>&client_secret=<robot-client-secret>" https://lab-markdown-sample-ui.test/oauth2/revoke-token/
```

The URL sub path is ``/oauth2/revoke-token/``.
