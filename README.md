# 🧠 Multi-Tenant RAG Portal – Backend

FastAPI backend for a **multi-tenant Retrieval-Augmented Generation (RAG) portal**.

This service handles:

- ✅ Tenant registration (SaaS-style onboarding)
- ✅ JWT authentication (login, `/auth/me`)
- ✅ Role-based access control (admin / user)
- ✅ Per-tenant user management
- ✅ Document upload (files + URLs)
- ✅ Local embeddings (HuggingFace) – **no paid API needed**
- ✅ Chroma as vector store (per-tenant collections)
- ✅ RAG chat API (LLM over tenant knowledge base)

The frontend (React + MUI) consumes these APIs but lives in a **separate repo**.

---

## 🏗 Tech Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Auth:** JWT (Bearer tokens)
- **Database:** PostgreSQL (e.g. Neon, RDS, local Postgres)
- **ORM:** SQLAlchemy
- **Vector Store:** Chroma (local, on-disk collections)
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (local)
- **RAG plumbing:** LangChain (loaders, splitters, vectorstore)
- **Password hashing:** passlib + bcrypt
- **Server:** Uvicorn

---

## 🔐 Multi-Tenant & Roles Model

**Tenants**

- Each company/org = one **tenant**
- Created via `/auth/register-tenant`
- Each tenant has its **own users** and **its own document vector collection**

**Users**

- Belong to exactly one tenant (`tenant_id`)
- `role`: `"admin"` or `"user"`
- Admin:
  - manage users (create / list / delete / edit)
  - upload and ingest documents
  - add URLs as data sources
- Regular user:
  - can log in and use Chat
  - **cannot** manage users / upload docs

**Auth**

- Login returns a **JWT access token**
- Protected endpoints require `Authorization: Bearer <token>`
- `/auth/me` returns current user info including **tenant name**

---

## 📁 Project Structure

High-level overview (may vary slightly from your local tree):

```text
rag-portal-backend/
├── app/
│   ├── main.py                 # FastAPI app, router registration
│   ├── config.py               # Settings / .env loading (pydantic)
│   ├── db.py                   # DB engine & SessionLocal
│   ├── models/
│   │   ├── user.py             # User model (tenant_id, role, password_hash, ...)
│   │   ├── tenant.py           # Tenant model
│   │   ├── document.py         # Document model (file + URL)
│   ├── schemas/
│   │   ├── auth.py             # Login, token, /me, tenant registration schemas
│   │   ├── user.py             # UserCreate, UserUpdate, UserResponse, UserInfo
│   │   ├── document.py         # DocumentResponse DTO
│   ├── api/
│   │   ├── deps.py             # get_db, get_current_user, require_admin, etc.
│   │   ├── routes_auth.py      # /auth/login, /auth/me, /auth/register-tenant
│   │   ├── routes_documents.py # /documents (upload file/URL, list, ingest)
│   │   ├── routes_users.py     # /users (CRUD within tenant)
│   │   ├── routes_profile.py   # /profile/change-password (optional)
│   ├── services/
│   │   ├── auth_service.py     # hash_password, verify_password, token helpers
│   │   ├── document_service.py # save_document (disk storage), save_url_document
│   │   ├── ingest_langchain.py # LangChain-based ingestion with Chroma
│   │   ├── chat_service.py     # RAG chat pipeline over Chroma
│   ├── ai/
│   │   ├── base.py             # AIProvider interface (embed, chat)
│   │   ├── local_embeddings.py # Local HuggingFace embeddings provider
│   └── ...
├── storage/                    # Local document files (by tenant_id)
├── chroma/                     # Chroma DB persistence directory
├── requirements.txt
├── .env.example
└── README.md
````

---

## ⚙️ Configuration

Configuration is loaded from environment variables (via `app.config.settings`).

Create a **`.env`** file in the project root (same folder as `requirements.txt`).

Example:

```env
# --- Database ---
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname

# --- Auth / JWT ---
JWT_SECRET=change_me_to_a_long_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# --- Local embeddings ---
LOCAL_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# --- Chroma vector store ---
CHROMA_DIR=./chroma

# --- File upload ---
MAX_FILE_SIZE_MB=10
```

> If you previously used OpenAI / Gemini for embeddings, those keys are now **optional** or unused for ingestion because we use a local HuggingFace model.

---

## 🚀 Running Locally

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/rag-portal-backend.git
cd rag-portal-backend
```

### 2. Create virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` → `.env` and update values:

```bash
cp .env.example .env    # or create manually on Windows
```

Make sure `DATABASE_URL` points to a **PostgreSQL** instance (Neon / local / RDS, etc.)

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Server will start at:

> [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 5. Open API docs

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📚 API Overview

High-level summary of key endpoints (paths may be slightly different depending on your final router prefixes):

### 🔑 Auth

* `POST /auth/login`
  → body: `{ "email": "...", "password": "..." }`
  → response: `{ "access_token": "...", "token_type": "bearer" }`

* `GET /auth/me`
  → requires `Authorization: Bearer <token>`
  → returns current user info, including `tenant_id` and `tenant_name`.

* `POST /auth/register-tenant`
  → body:

  ```json
  {
    "tenant_name": "Acme Corp",
    "admin_email": "admin@acme.com",
    "admin_password": "secret123"
  }
  ```

  → creates a new tenant + its first admin user.

---

### 👥 Users (admin-only, per-tenant)

All require `Authorization: Bearer <admin_token>`.

* `GET /users`
  → list users in the current admin’s tenant

* `POST /users`
  → create a new user in the current tenant

  ```json
  {
    "email": "user@acme.com",
    "password": "secret123",
    "role": "user"
  }
  ```

* `PATCH /users/{user_id}`
  → update email, role, or reset password

* `DELETE /users/{user_id}`
  → delete a user (cannot delete self)

---

### 📄 Documents (admin-only, per-tenant)

* `POST /documents/upload` (multipart/form-data)
  → upload file (`pdf`, `txt`, `md`, `docx`, `csv`, `json`, `html`)
  → backend enforces `MAX_FILE_SIZE_MB`
  → server saves file to `storage/<tenant_id>/<doc_id>_<filename>`

* `POST /documents/upload-url`
  → body: `{ "url": "https://example.com/article" }` or plain form field `url`
  → creates a document pointing to a URL instead of a local file

* `GET /documents`
  → list documents for current tenant (supports pagination in newer versions)

* `POST /documents/{document_id}/ingest`
  → runs ingestion pipeline:

  * load file (or fetch URL)
  * chunk text via `RecursiveCharacterTextSplitter`
  * embed chunks with HuggingFace model (`LOCAL_EMBED_MODEL`)
  * store vectors in Chroma under `collection_name = f"tenant_{tenant_id}"`

---

### 💬 Chat (RAG)

* `POST /chat/query` (example, exact path may differ)
  → body:

  ```json
  {
    "message": "What does the 1983 Cricket World Cup article say about the final?",
    "history": [
      { "role": "user", "content": "..." },
      { "role": "assistant", "content": "..." }
    ]
  }
  ```

  → pipeline:

  * embed query
  * retrieve top-k chunks from Chroma for current tenant
  * build prompt with context
  * call LLM (OpenAI / Gemini / other provider depending on `AIProvider` config)
  * return answer + optionally retrieved snippets

---

## 🧩 Ingestion Details

Ingestion uses **LangChain**:

* File loaders:

  * `PyPDFLoader` (PDF)
  * `TextLoader` (TXT)
  * `UnstructuredMarkdownLoader` (MD)
  * `UnstructuredWordDocumentLoader` (DOCX)
  * `UnstructuredCSVLoader` (CSV)
  * `JSONLoader` (JSON)
* URL loader:

  * `BSHTMLLoader` (BeautifulSoup-based HTML loader, using `requests` under the hood)
* Text splitter:

  * `RecursiveCharacterTextSplitter` with chunk size ~1000, overlap ~200
* Embeddings:

  * `HuggingFaceEmbeddings` using `LOCAL_EMBED_MODEL`
* Vector store:

  * `Chroma` from `langchain_chroma`, persisted to `CHROMA_DIR`

---

## ✅ Features Checklist

* [x] Tenant registration
* [x] JWT auth + `/auth/me`
* [x] Role-based access (admin/user)
* [x] User CRUD (admin-only, within tenant)
* [x] Document upload (file + URL)
* [x] File size limit enforced server-side
* [x] Local embeddings via HuggingFace
* [x] Per-tenant vector collections in Chroma
* [x] RAG chat endpoint
* [x] URL ingestion (HTML → text)
* [x] Pagination for documents & users (in newer version)
* [ ] Soft delete / re-ingest support per document
* [ ] Tenant settings (rename, limits, etc.)
* [ ] Audit logs for chat & ingestion

---

## 🧪 Testing (placeholder)

You can add tests under `tests/`:

```bash
pytest
```

Example areas to test:

* Auth flow (`/auth/login`, `/auth/me`, invalid tokens)
* Tenant registration
* Role enforcement (user vs admin)
* Document upload + ingestion
* Chat endpoint with fake LLM

---


## 🙋‍♂️ Author

**Saurabh Jain**

* GitHub: https://github.com/Saurabhjain2k1

---

