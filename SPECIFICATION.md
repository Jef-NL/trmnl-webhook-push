
This is the payload that will be sent to the Terminal Sensor Push API.

```json
payload = {
    "merge_variables": {
        "entities": [create_entity_payload(new_state)]
    }
}
```

each entity created by `create_entity_payload` will have the following payload:

```json
{
    "state": "Entity Value",
    "attributes": "Entity Attributes" 
}

An example of how this would be sent with a shell command would be:

```bash
```
curl -X POST -H "Content-Type: application/json" -d '{"merge_variables": {"entities": [{"state": "Entity Value", "attributes": {...}}]}}' https://usetrmnl.com/api/custom_plugins/XXXX-XXXX-XXXX-XXXX
```




