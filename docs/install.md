# FREEDOM Installation Guide
> **Translations:** This guide is also available in Japanese: [install_ja.md](install_ja.md).
> When editing this file, update [install_ja.md](install_ja.md) in the same change so both stay equivalent (see [CONTRIBUTING.md](../CONTRIBUTING.md#documentation-translations)).

This guide walks you through installing FREEDOM in a local environment.
Adjust the settings as needed to fit your environment.
All examples below use Windows.
For macOS/Linux, replace `\` with `/` and adjust commands accordingly (e.g. `.venv\Scripts\activate` → `source .venv/bin/activate`).

## 1. Install Required Software
### 1.1. Install Python 3.13.3
To run the FREEDOM backend, you need **Python 3.13.3**.
1. Download the installer from [Python.org](https://www.python.org/downloads/release/python-3133/).
2. Run the installer.
   - You can generally leave all options at their default values.
3. Open a terminal and run:
   ```bash
   python --version
   ```
4. If `Python 3.13.3` is displayed, the installation was successful.

### 1.2. Install Node.js
To run the FREEDOM frontend and set up the login feature, Node.js is required.
In this guide, we use **v24.18.0**, which is a version we have verified to work with FREEDOM.
1. Download the **v24.18.0** installer from [Node.js](https://nodejs.org/en/download).
2. Run the installer.
   - You can generally leave all options at their default values.
3. Open a terminal and run:
   ```bash
   node -v
   ```
4. If `v24.18.0` is displayed, the installation was successful.

### 1.3. Install and Configure PostgreSQL 16 or Later
1. Download the installer from [PostgreSQL: Downloads](https://www.postgresql.org/download/).
2. Run the installer.
   - You can generally leave all options at their default values.
   - **Stack Builder** is not required.
   - Be sure to record the PostgreSQL password you set during installation; you will need it later.
3. After installation, launch **pgAdmin**, which is installed together with PostgreSQL.
4. Add a connection to your PostgreSQL server if necessary.
5. Create a database with any name you like.
   This database name will be used later when setting `dsn` and `DATABASE_URL`.

## 2. Set Up the FREEDOM Development Environment
The following steps should be run in a terminal.
### 2.1. Set Up the Backend
1. Move to the `backend` directory.
   ```bash
   C:\your-directory\freedom> cd .\backend\
   ```
2. Create a Python virtual environment.
   ```bash
   C:\your-directory\freedom\backend> python -m venv .venv
   ```
   - If a `.venv` folder is created inside the `backend` directory, this step was successful.
3. Activate the virtual environment.
   ```bash
   C:\your-directory\freedom\backend> .venv\Scripts\activate
   ```
   - If `(.venv)` appears at the beginning of the command prompt, the environment is activated.
4. Install the required libraries.
   ```bash
   (.venv) C:\your-directory\freedom\backend> pip install -r requirements.txt
   ```

### 2.2. Set Up the Frontend
1. Move to the `frontend` directory.
   ```bash
   (.venv) C:\your-directory\freedom\backend> cd ..\frontend\
   ```
2. Install the required libraries.
   ```bash
   (.venv) C:\your-directory\freedom\frontend> npm install
   ```
   - If a `node_modules` directory is created inside `frontend`, this step was successful.
> **Note**
> Installation may take some time.
> If it does not complete within an hour, there may be an issue with the installation.

## 3. Configure FREEDOM
### 3.1. Create a Backend Configuration File
In `freedom/backend/config`, copy the template file `dummy.py` and give the copy any name you like.

### 3.2. Configure `main`
In the configuration file you created, update the `main` settings to match your environment.
```python
# freedom.main domain
main = freedom.main.Domain(
    interface = "PostgreSQL",    # Interface name
    dsn = "postgresql://postgres:password@localhost:5432/freedom_db",  # Database DSN
    schema = "public",  # Schema name
    table = "freedom_main",  # Table name
    update_cycle = 10,  # Update cycle in seconds
)
```
#### `dsn` Format
```text
postgresql://user:password@host:port/database_name
```
#### Example
```text
postgresql://postgres:password@localhost:5432/freedom_db
```
- The default PostgreSQL user name is usually `postgres`.

### 3.3. Configure `user_interface`
In the same configuration file, update the `user_interface` settings to match your environment.
```python
# freedom.user_interface domain
user_interface = freedom.user_interface.Domain(
    ip = "localhost",  # IP address
    port = 8080,  # Port
    origin = ["http://localhost:3000", "http://172.16.0.1:3000"]  # Allowed origins for CORS
)
```
- Set `ip` and `port` to the IP address and port where the backend Web API will be served.
- Set `origin` to the URL where the frontend (Web UI) will be served.
#### Example Configurations
- For local-only use:
  `http://localhost:3000`
- To allow access from another device:
  `http://<IP address of the PC running FREEDOM>:3000`

## 4. Initial Setup of User Authentication (Better Auth)
### 4.1. Start the Backend
1. Move to the project root.
2. Activate the virtual environment.
   ```bash
   C:\your-directory\freedom> .\backend\.venv\Scripts\activate
   ```
3. Start the backend.
   Replace `FILENAME` with the name of the configuration file you created under `backend/config` in step **3.1**.
   Do not include the `.py` extension when specifying the filename.
   ```bash
   (.venv) C:\your-directory\freedom> python .\backend\ FILENAME
   ```
   - If you see logs like `2026-02-27,17:22:25.740,src.freedom.log,INFO,"launch"...`, the backend has started successfully.
   - On first startup, schemas and tables required for the login feature are created automatically, and seed data is inserted.

### 4.2. Create a `.env` File for the Frontend
1. Move to the `frontend` directory.
   ```bash
   C:\your-directory\freedom> cd .\frontend\
   ```
2. Copy `.env.example` to `.env`.
   `.env.example` contains the following entries:
   ```env
   # Auth Secret (cookie signing)
   BETTER_AUTH_SECRET=
   # PostgreSQL used by Better Auth
   DATABASE_URL=postgresql://user:password@host:port/dbname?options=-c%20search_path%3Dauth
   # Better Auth (Next.js side)
   BETTER_AUTH_URL=http://localhost:3000
   # Next.js BFF -> Backend (aiohttp)
   BACKEND_BASE_URL=http://localhost:8080
   # Frontend -> Next.js BFF
   NEXT_PUBLIC_API_URL=/api/bff
   ```

### 4.3. Generate the Auth Secret
Generate a string to use for `BETTER_AUTH_SECRET`.
On Windows, run the following command:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```
Copy and save the generated string.
> **Note**
> You can also generate the secret using the method described in the official documentation:
> https://better-auth.com/docs/installation#set-environment-variables

### 4.4. Configure `.env`
Set the necessary values in the `.env` file you created:
The environment variables in this `.env` file are used with `npm run dev`, `npm run build`, and `npm run start`.
```env
BETTER_AUTH_SECRET=generated_string
DATABASE_URL=postgresql://user:password@host:port/dbname?options=-c%20search_path%3Dauth
BETTER_AUTH_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8080
NEXT_PUBLIC_API_URL=/api/bff
```
#### Example
```env
BETTER_AUTH_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://postgres:password@localhost:5432/freedom_db?options=-c%20search_path%3Dauth
BETTER_AUTH_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8080
NEXT_PUBLIC_API_URL=/api/bff
```
#### Field Descriptions
- `BETTER_AUTH_SECRET`
   Set the string generated in step **4.3**.
- `DATABASE_URL`
  PostgreSQL connection string used by Better Auth.
  You must include `?options=-c%20search_path%3Dauth`.
- `BETTER_AUTH_URL`
  The public URL of the frontend.
  Use the same value you set as `origin` in step **3.3**.
- `BACKEND_BASE_URL`
   The URL used by the Next.js BFF to connect to the backend.
   Use the backend `ip` and `port` values.
   Replace the `http://localhost:8080` part with the same `ip` and `port` you set in step **3.3**.
- `NEXT_PUBLIC_API_URL`
   The URL used by the frontend to connect to the Next.js BFF.
   Normally, leave it set to `/api/bff`.

### 4.5. Run Better Auth Migrations
With the backend still running, open a **separate terminal** and do the following:
1. Move to the `frontend` directory.
   ```bash
   C:\your-directory\freedom> cd .\frontend\
   ```
2. Run the Better Auth migration:
   ```bash
   C:\your-directory\freedom\frontend> npx auth@~1.7 migrate --config src/lib/auth.ts
   ```
   - The tables used by Better Auth are created by this migration.
   - If the following message appears, enter `y`.
      ```bash
      Need to install the following packages:
      auth@1.7.xx
      Ok to proceed? (y)
      ```
      ```bash
      🔑 The migration will affect the following:
      -> name, email, emailVerified, image, createdAt, updatedAt, username, displayUsername, role, banned, banReason, banExpires fields on user table.
      -> expiresAt, token, createdAt, updatedAt, ipAddress, userAgent, userId, impersonatedBy fields on session table.
      -> accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt fields on account table.
      -> identifier, value, expiresAt, createdAt, updatedAt fields on verification table.
      √ Are you sure you want to run these migrations?
      ```
   - If you see logs like `🚀 migration was completed successfully!`, this step has been completed successfully.

### 4.6. Create an Initial Admin User
1. In the `frontend` directory, run:
   ```bash
   C:\your-directory\freedom\frontend> npx tsx scripts/seed-admin.ts
   ```
   - If the following message appears, enter `y`.
      ```bash
      Need to install the following packages:
      tsx@4.23.1
      Ok to proceed? (y)
      ```
2. After running this script, the following initial admin user will be created:
   ```text
   username: admin
   password: admin123
   ```

## 5. Start FREEDOM
If you have already started the backend in Step 4, you can skip starting the backend in Step 5.1.
Proceed to Step 5.2 to start the frontend.
### 5.1. Start the Backend
1. Move to the project root.
2. Activate the virtual environment.
   ```bash
   C:\your-directory\freedom> .\backend\.venv\Scripts\activate
   ```
3. Start the backend.
   Replace `FILENAME` with the name of the configuration file you created under `backend/config` in step **3.1**.
   Do not include the `.py` extension when specifying the filename.
   ```bash
   (.venv) C:\your-directory\freedom> python .\backend\ FILENAME
   ```
   - If you see logs like `2026-02-27,17:22:25.740,src.freedom.log,INFO,"launch"...`, the backend has started successfully.

### 5.2. Start the Frontend
The frontend can be started in development mode or after building it.

#### Start in the development environment
1. Open another terminal if needed.
2. Move to the `frontend` directory.
   ```bash
   C:\your-directory\freedom> cd .\frontend\
   ```
3. Start the frontend.
   ```bash
   C:\your-directory\freedom\frontend> npm run dev
   ```

#### Build and start the frontend
1. Move to the `frontend` directory.
   ```bash
   C:\your-directory\freedom> cd .\frontend\
   ```
2. Build the frontend.
   ```bash
   C:\your-directory\freedom\frontend> npm run build
   ```
3. After the build completes, start the frontend.
   ```bash
   C:\your-directory\freedom\frontend> npm run start
   ```

- Before running `npm run build` and `npm run start`, set the required environment variables in the `.env` file from step **4.4**.
- `npm run build` builds the frontend, and `npm run start` starts the built frontend.
- The backend must also be running when starting the frontend after a build.

To change the frontend port in development, run:
```bash
C:\your-directory\freedom\frontend> npm run dev -- -p 4000
```
To change the frontend port when starting after a build, run:
```bash
C:\your-directory\freedom\frontend> npm run start -- -p 4000
```

When changing the port, also use the new port in the `origin` in step **3.3** and `BETTER_AUTH_URL` in step **4.4**.

After starting the frontend, access the URL specified as `origin` in step **3.3**.
If the URL is accessible, the frontend has started successfully.

## 6. Verify Operation
### 6.1. Check the FREEDOM UI
1. In your browser, access `http://localhost:3000` or the URL you set as `origin` in step **3.3**.
2. If the FREEDOM map screen appears, the setup is successful.
> **Note**
> After starting the frontend, you can also open the screen by holding **Ctrl** and clicking the `Local` URL shown in the terminal.

### 6.2. Check the Login Screen
1. In your browser, access the URL specified as `origin` in step **3.3**.
   Append `/login` to the end of the URL.
   ```text
   http://localhost:3000/login
   ```
   If you changed the port to 4000, use:
   ```text
   http://localhost:4000/login
   ```
2. Log in with the following credentials:
   ```text
   Username: admin
   Password: admin123
   ```

### 6.3. Verify After Logging In
After logging in, verify the following:
- When you click the account icon, your user information is displayed.
- A gear icon for admin settings appears in the header.
- You can access the **“Access Control Settings”** and **“User Settings”** pages.
- “Settings” is displayed in the left navigation bar.

### 6.4. Change the Initial Password
For security reasons, change the password after your first login.
#### Steps to Change the Password
- Go to the admin user management page.
- Update the password from **“Change Password”** for the target user.
> **Note**
> Set the new password for the initial admin user to a length between **1 and 128 characters**.

## 7. Important Notes
Perform the **initial setup** in the following order:
```text
Start backend
→ Run Better Auth migrations
→ Create initial admin user
→ Start frontend
```
- If the backend has not been started at least once, the tables required for user authentication will not exist, and subsequent steps may fail.
- If you encounter import errors when starting the backend, check whether all required libraries have been installed.
- If errors occur when running the frontend or migrations, verify the values of
   `DATABASE_URL`, `BETTER_AUTH_SECRET`, `BETTER_AUTH_URL`, `BACKEND_BASE_URL`,
   and `NEXT_PUBLIC_API_URL` in your `.env` file.