# Authentication Research for Persona

## 1. Context and Constraints
- **Multi-user**: Each user must have their own resumes, applications, and settings.
- **Unified Backend**: FastAPI serves both REST API and MCP.
- **Frontend**: React SPA.
- **Deployment**: Targeted for AWS (eventually).
- **Storage**: Currently SQLite, but multi-user might require moving to PostgreSQL if scaling on AWS.

## 2. Authentication Scenarios
- **Web UI**: Standard session or JWT-based auth. Social logins (Google, GitHub) are highly desirable.
- **REST API**: API keys or Bearer tokens for programmatic access.
- **MCP Server**:
    - **HTTP transport**: Requires Bearer tokens or API keys passed in headers.
    - **Stdio transport**: Typically runs locally for one user. For multi-user, stdio might not be the primary interface unless it's per-user local deployment.

## 3. Options Evaluation

### Option A: Self-hosted (FastAPI Users + JWT + SQLite/PostgreSQL)
- **Pros**:
    - Complete control over data and security.
    - No external dependency costs.
    - Fits well with the current Python/FastAPI stack.
- **Cons**:
    - High implementation effort (Registration, Login, Password Reset, Email verification, Session management).
    - Security is your responsibility.
    - Harder to implement Social Login (OAuth2) from scratch.

### Option B: Clerk
- **Pros**:
    - Best-in-class Developer Experience.
    - Pre-built React components for Login/Profile.
    - Handles Social Login, MFA, and User Management out of the box.
    - Generous free tier (up to 10k users).
- **Cons**:
    - External dependency.
    - Data silo (users are managed in Clerk, though you sync to your DB).

### Option C: AWS Cognito
- **Pros**:
    - Native to AWS (user's eventual target).
    - IAM integration if needed for other AWS services.
- **Cons**:
    - Poor Developer Experience compared to Clerk.
    - Basic UI components require significant styling effort.
    - Configuration is notoriously complex.

### Option D: Auth0
- **Pros**:
    - Industry standard, extremely flexible.
- **Cons**:
    - Complex pricing and configuration.
    - Overkill for this project.

## 4. MCP Authentication
The Model Context Protocol (MCP) over HTTP uses standard HTTP mechanisms.
- **Bearer Token**: The client (like Claude Desktop) sends an `Authorization: Bearer <token>` header.
- **FastAPI Middleware**: We can wrap the MCP mount point with authentication middleware to validate the token before it reaches FastMCP.
- **Stdio Mode**: When running via `--stdio`, the server typically trusts the environment. For a multi-user cloud host, users wouldn't typically use stdio mode directly against the remote server. They would use HTTP.

## 5. Multi-tenancy Design
- Add `user_id` (string/UUID) to all major tables: `resume_version`, `application`.
- Use `user_id` in `WHERE` clauses for all queries.
- Ensure `ResumeService` and `ApplicationService` are user-aware.

## 6. Preliminary Recommendation
**Clerk** is recommended for the fastest path to a high-quality multi-user experience. It handles the UI, security, and social logins, allowing you to focus on the Persona-specific logic.

If absolute data sovereignty and zero external dependencies are required, **FastAPI Users** with JWT is the alternative.
