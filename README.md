## Running the API
```bash
cd src
python api.py
```
The API will start running on localhost:5000/

## Getting metrics
API endpoint: `/metrics`. Example response:
```json
{
  "per_contract_metrics": [
    {
      "call_chains": 1,
      "call_count": 6,
      "contract_address": "0x80c080acd48ed66a35ae8a24bc1198672215a9bd",
      "total_amount": 0.0
    },
    {
      "call_chains": 1,
      "call_count": 6,
      "contract_address": "0x34b842d0acf830134d44075dcbce43ba04286c12",
      "total_amount": 0.0
    },
    {
      "call_chains": 1,
      "call_count": 6,
      "contract_address": "0xf00a183ae9daa5ed969818e09fdd76a8e0b627e6",
      "total_amount": 0.0
    }
  ],
  "total_user_count": 1
}
```