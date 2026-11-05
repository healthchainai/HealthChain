# Working with FHIR Sandboxes

This guide covers setting up access to public FHIR sandboxes for testing and development. These sandboxes provide free access to test data and realistic FHIR APIs without requiring production EHR credentials.

## Epic on FHIR Sandbox

Epic provides a public [testing sandbox](https://open.epic.com/MyApps/Endpoints) with [sample patients](https://fhir.epic.com/Documentation?docId=testpatients) and [resource specifications available](https://fhir.epic.com/Specifications) for developing against their FHIR Server.

### Prerequisites

- Free Epic on FHIR developer account: <https://fhir.epic.com/>
- No existing Epic customer account required (it only takes a minute)

### Step 1: Create an App

1. Log in to <https://fhir.epic.com/>

1. Navigate to "Build Apps" → "Create"

1. Fill out the application form:

1. **Application Name**: Choose any descriptive name

1. **Application Type**: Check "Backend Systems"

1. **FHIR APIs**: Select the APIs you need (note the versions)

### Step 2: Configure OAuth2 with JWT Authentication

Epic uses [OAuth2 with JWT assertion for authentication](https://fhir.epic.com/Documentation?docId=oauth2&section=BackendOAuth2Guide).

#### Generate Key Pair

Follow Epic's instructions to [create a Public Private key pair for JWT signature](https://fhir.epic.com/Documentation?docId=oauth2&section=Creating-Key-Pair):

```bash
# Generate private key - make sure the key length is at least 2048 bits.
openssl genrsa -out privatekey.pem 2048

# Export public key as base64 encoded X.509 certificate
openssl req -new -x509 -key privatekey.pem -out publickey509.pem -subj '/CN=myapp'
```

Where `/CN=myapp` is the subject name (e.g., your app name). The subject name doesn't have functional impact but is required for creating an X.509 certificate.

#### Register Public Key via JWKS URL

Epic now requires registering your public key via a **JWKS (JSON Web Key Set) URL** instead of direct file upload. For quick and dirty development/testing purposes, you can use ngrok to expose your JWKS server publicly.

1. **Set up a JWKS server**:

   ```bash
   # Ensure your .env has the private key path
   # EPIC_CLIENT_SECRET_PATH=path/to/privatekey.pem
   # EPIC_KEY_ID=healthchain-demo-key

   python scripts/serve_jwks.py
   ```

1. **Get a free static domain from ngrok**:

   - Sign up at [ngrok.com](https://ngrok.com)
   - Claim your free static domain from the dashboard
   - Example: `your-app.ngrok-free.app`

1. **Expose your JWKS server**:

   ```bash
   ngrok http 9999 --domain=your-app.ngrok-free.app
   ```

1. **Register in Epic App Orchard**:

   - In your Epic app configuration, locate the **Non-Production JWK Set URL** field
   - Enter: `https://your-app.ngrok-free.app/.well-known/jwks.json`
   - Click **Save**
   - Note down your **Non-Production Client ID**

The JWKS must be:

- Publicly accessible without authentication
- Served over HTTPS
- Stable (URL should not change)

### Step 3: Complete App Setup

1. Fill out remaining required fields (description, etc.)
1. Check to confirm terms of use
1. Click **Save & Ready for Sandbox**

### Step 4: Configure Environment Variables

Create a `.env` file with your credentials:

```bash
# .env file
EPIC_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_CLIENT_ID=your_non_production_client_id
EPIC_CLIENT_SECRET_PATH=path/to/privatekey.pem
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_USE_JWT_ASSERTION=true
EPIC_KEY_ID=healthchain-demo-key  # Must match the kid in your JWKS
```

**Important**: The `EPIC_KEY_ID` must match the Key ID (`kid`) you used when creating your JWKS. This allows Epic to identify which key to use for JWT verification.

### Using Epic Sandbox in Code

```python
from healthchain.gateway.clients import FHIRAuthConfig

# Load configuration from environment variables
config = FHIRAuthConfig.from_env("EPIC")
EPIC_URL = config.to_connection_string()

# Add to FHIR gateway
from healthchain.gateway import FHIRGateway

gateway = FHIRGateway()
gateway.add_source("epic", EPIC_URL)
```

### Testing Your Connection

After configuration:

```bash
python scripts/check_epic_connection.py
```

This script will:

1. Load your Epic configuration
1. Create a JWT assertion with the `kid` header
1. Request an access token from Epic
1. Test a FHIR endpoint query

### Available Test Patients

Epic provides [sample test patients](https://fhir.epic.com/Documentation?docId=testpatients) including:

- **Derrick Lin** - Patient ID: `eq081-VQEgP8drUUqCWzHfw3`
- **Linda Ross** - Patient ID: `eIXesllypH3M9tAA5WdJftQ3`
- Many others with various clinical scenarios

Troubleshooting (click to expand)

**Token request fails after JWKS registration:**

- Wait 15-30 minutes for Epic to propagate changes
- Verify your JWKS URL is publicly accessible (test in browser)
- Check that `EPIC_KEY_ID` matches the `kid` in your JWKS
- Ensure the ngrok tunnel is still running

**JWKS format errors:**

- Verify the JWKS structure at your URL matches Epic's requirements
- Check that `n` and `e` are properly base64url encoded (no padding)
- Algorithm should be RS384, RS256, or RS512

______________________________________________________________________

## Cerner Sandbox

Cerner (now Oracle Health) provides both open and secure public sandboxes for the [FHIR R4 APIs for Oracle Health Millennium Platform](https://docs.oracle.com/en/industries/health/millennium-platform-apis/mfrap/srv_root_url.html).

The Open Sandbox is read-only. It does not require authentication and is handy for quick proof of concepts:

```bash
https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d/:resource[?:parameters]
```

You can get an idea of patients available in the open sandbox by querying some common last names:

```bash
curl -i -H "Accept: application/json+fhir" "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d/Patient?family=smith"
```

Documentation on Secure Sandbox coming soon.

______________________________________________________________________

## Medplum

[Medplum](https://www.medplum.com/) is an open-source healthcare platform that provides a compliant FHIR server. It's useful for testing with controlled data where you can upload your own test patients. Medplum uses [standard OAuth2/OpenID authentication](https://www.medplum.com/docs/auth/client-credentials).

### Prerequisites

- Medplum account: [Register here](https://www.medplum.com/docs/tutorials/register)
- Free tier available

### Step 1: Create a Client Application

1. Log in to your Medplum account
1. Navigate to Client Application:
1. Option 1: Use this direct link: [ClientApplication](https://app.medplum.com/ClientApplication)
1. Option 2: Click the Medplum logo (top-left) and search for "Client Application" in the resources search bar
1. Create a new Client
1. Configure Access Policy if needed:
1. **Required for**: Production deployments, multi-user environments, restricted data access
1. **Optional for**: Sandbox testing with personal test data
1. For production setup, see [Medplum's access control documentation](https://www.medplum.com/docs/access/access-policies)

### Step 2: Get Credentials

After creating the client:

1. Note your **Client ID**
1. Copy your **Client Secret**

### Step 3: Configure Environment Variables

Create a `.env` file with your credentials:

```bash
# .env file
MEDPLUM_BASE_URL=https://api.medplum.com/fhir/R4
MEDPLUM_CLIENT_ID=your_client_id
MEDPLUM_CLIENT_SECRET=your_client_secret
MEDPLUM_TOKEN_URL=https://api.medplum.com/oauth2/token
MEDPLUM_SCOPE=openid
```

### Using Medplum in Code

```python
from healthchain.gateway import FHIRGateway
from healthchain.gateway.clients import FHIRAuthConfig

# Load configuration from environment variables (.env is read automatically)
config = FHIRAuthConfig.from_env("MEDPLUM")
MEDPLUM_URL = config.to_connection_string()

# Add to FHIR gateway
gateway = FHIRGateway()
gateway.add_source("medplum", MEDPLUM_URL)
```

### Seeding test data

Once credentials are configured, use `healthchain seed medplum` to upload FHIR data from a JSON file or directory of JSON files:

```bash
# Single bundle file
healthchain seed medplum ./cookbook/data/qa_patient.json

# Directory of bundle files
healthchain seed medplum ./cookbook/data/mimic_demo_patients/
```

The command accepts any FHIR transaction Bundle, resource array, or single resource. It prints the server-assigned Patient ID(s) after upload:

```text
◆ Seeding Medplum  qa_patient.json

  ✓ DEMO_PATIENT_ID=abc123
```

Each cookbook's `cookbook/data/` directory contains the seed file it needs.

### Benefits of Medplum

- **Full control**: Upload your own test data
- **FHIR R4 compliant**: Complete FHIR API implementation
- **Multi-source testing**: Create multiple projects for different data sources
- **Web interface**: Browse and manage resources via UI

______________________________________________________________________

## Tips for Multi-Source Testing

### Different Test Data

Public sandboxes (Epic, Cerner) contain different test patients. When testing multi-source aggregation:

- **Expected behavior**: Queries for patients not in a source should fail gracefully
- **Production use**: Map patient identifiers across systems or use sources sharing patient cohorts
- **Controlled testing**: Use Medplum where you can upload the same test patients to multiple instances

### Error Handling

Your code should handle:

- Network issues or downtime
- Patient not found in specific sources
- Rate limiting
- Authorization failures

### Authentication

| Sandbox     | Auth Mechanism                                      |
| ----------- | --------------------------------------------------- |
| **Epic**    | OAuth2 with JWT assertion (backend)                 |
| **Medplum** | OAuth2 client credentials (Client Credentials Flow) |

HealthChain's [FHIRGateway](https://healthchainai.github.io/HealthChain/reference/gateway/fhir_gateway/index.md) handles these automatically via connection strings.

## Next Steps

- Return to your tutorial to continue with the specific use case
- See [FHIR Gateway documentation](https://healthchainai.github.io/HealthChain/reference/gateway/fhir_gateway/index.md) for advanced configuration
- Check [FHIR Resources documentation](https://www.hl7.org/fhir/) for working with different resource types
