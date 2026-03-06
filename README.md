# openapi-enum

A Python tool for **API reconnaissance** that parses an OpenAPI/Swagger specification, extracts endpoints, generates fuzzable URLs, and probes them with **httpx** to identify live routes.

---

## Features

- Supports **OpenAPI v2 and v3**
- Parses **JSON and YAML**
- Accepts **local file or URL**
- Replaces parameters (`{id}`, `{userId}`) with a fuzz value
- Generates endpoint lists:
  - `GET`
  - `POST`
  - `ALL`
- Probes endpoints with **httpx** for **HTTP 200**
- Custom fuzz value and output directory

---

## Installation

Clone the repository:

```
git clone https://github.com/yourusername/openapi-enum.git
cd openapi-enum
```

Install dependencies:

```
pip install -r requirements.txt
```

Install **:contentReference[oaicite:0]{index=0}**:

```
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
```

Make sure it is in your PATH.

---

## Usage

Local specification:

```
python3 openapi_enum.py -i openapi.json
```

Remote specification:

```
python3 openapi_enum.py -u https://api.example.com/openapi.json
```

Custom fuzz value:

```
python3 openapi_enum.py -i openapi.json --fuzz-value TEST
```

Custom output directory:

```
python3 openapi_enum.py -i openapi.json -o results
```

---

## Output

The script generates:

```
endpoints_all.txt
endpoints_get.txt
endpoints_post.txt
httpx_alive.txt
```

Example:

```
https://api.example.com/users
https://api.example.com/users/FUZZ
https://api.example.com/auth/login
```

---

## Project Structure

```
openapi-enum/
├── openapi_enum.py
├── README.md
├── requirements.txt
```

---

## Disclaimer

For **authorized security testing only**.

---

## License

MIT