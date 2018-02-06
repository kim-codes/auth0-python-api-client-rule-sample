# Auth0 Client & Rules example 
## Python Web App

### Pre-requisites

To run the sample python web application you will need the appropriate dependencies found in the requirements.txt file. You can quickly install them by running:

run `pip install -r requirements.txt`

Create a new python application and a Non-Interactive Client in Auth0.

Rename .env.example to .env and populate it with the following data: 
- `AUTH0_CLIENT_ID`: python client
- `AUTH0_DOMAIN`: your Auth0 tenant name
- `AUTH0_CLIENT_SECRET`: python client secret
- `AUTH0_CALLBACK_URL`: running locally http://localhost:3000/callback
- `AUTH0_CLIENT_ID_MNGNMT_API`: non-interactive client
- `AUTH0_CLIENT_SECRET_MNGNMT_API`: non-interactive client secret
- `AUTH0_AUDIENCE_MNGNMT_API`: value of the Identifier field of the [Auth0 Management API](https://manage.auth0.com/#/apis)

Start the server `python server.py` and navigate to `http://localhost:3000`

## The application

To get a list of all our clients and rules we need to interact with the Auth0 Management API. In order to do so, we will need to create a Non-Interactive Client to talk to the API. 
The steps to do this can be found here: https://auth0.com/docs/api/management/v2/tokens#1-create-and-authorize-a-client 

Once created, we can make calls through an application, but we will need a token. Since we will be making frequent calls we can generate this token dynamtically. 

In our sample application we can add this piece of code to generate an access token to the API. 

```python
 # get access token from Auth0 for mngnment api
    base_url = "https://" + AUTH0_DOMAIN

    mngmnt_api_data = {'client_id':AUTH0_CLIENT_ID_MNGNMT_API,
                       'client_secret':AUTH0_CLIENT_SECRET_MNGNMT_API,
                       'audience': AUTH0_AUDIENCE_MNGNMT_API,
                       'grant_type': GRANT_TYPE}

    req = requests.post(base_url + "/oauth/token", data=mngmnt_api_data)
    access_data = req.json()
    access_token = access_data['access_token']
```

Now that we have a token, we can request a list of all our clients and all our rules. Below you will find the code that makes a request to the API, with the access token we just generated, to gather a list. 

> Note: You can see more information about the Auth0 Management APIv2 Token and examples in our languages here https://auth0.com/docs/api/management/v2/tokens]

```python
# get all rules using the access token 
headers = {'authorization': 'Bearer ' + access_token}
req = requests.get(base_url + "/api/v2/rules?fields=script,name", headers=headers)
rules_data = req.json()

# get all clients 
req = requests.get(base_url + "/api/v2/clients?fields=name,client_id", headers=headers)
client_data = req.json()
```

Since within a rule there is already an existing function to map it to a client, all we need to do is extract that data to generate our list. 

A short python script, that you can modify to suit your needs, will extract the line of code that sets the rule to a specific client. At which point, we can map our rules with clients and store the data as we see fit. 

In our example, we created a client object that stores the name and id, which is then used as a key in a dictionary whose value will be all the rules associate with that client.  


```python
# function to extract context type (client or id) with app name
def extract_app_name(script):
    index_of_context = re.findall('\(.*?\)', script)[1]
    context_type = re.findall('\w+\s', index_of_context)[0]
    app_name = re.findall(r'\'(.+?)\'',index_of_context)[0]
    return { 'type': context_type, 'name': app_name }

# format client data from api into a list
client_list = {}

for x in client_data[:-1]:
    new_client = Client(x['name'], x['client_id'])
    client_list[new_client] = [" "]

# add rules to client list 
for rule in rules_data:
    context_data = extract_app_name(rule['script'])
    app_rule_type = context_data['type']
    app_name = context_data['name']
    for key, value in client_list.items():
        if app_rule_type=="clientName ":
            search_key = key.name
        else:
            search_key = key.id
        if app_name==search_key:
            value.append(str(rule['name']))
            break  
    # end of client_list loop
# end of rules_data loop       
```
## Screenshots of application running 

### Login page

<img src="https://user-images.githubusercontent.com/5739370/35821492-1f2860c4-0a77-11e8-8cf8-e9f8689d8b87.PNG" width="400" height="200" />

### Dashboard page

<img src="https://user-images.githubusercontent.com/5739370/35821517-362e00ee-0a77-11e8-8914-9da85d41ee8b.PNG" width="400" height="200" />

### View list page
<img src="https://user-images.githubusercontent.com/5739370/35822316-e6a99ca6-0a79-11e8-9e01-816598cfd6b3.PNG" width="450" height="200" />

## License

This project is licensed under the MIT license. See the [LICENSE](LICENSE) file for more info.
